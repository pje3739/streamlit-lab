import re
import streamlit as st

st.title("ChatPDF")
st.write("PDF 파일을 업로드하고 문서에 대해 질문해 보세요.")

# 대화 기록 초기화
if "pdf_messages" not in st.session_state:
    st.session_state.pdf_messages = []

# 대화 내용만 삭제
def clear_chat():
    st.session_state.pdf_messages = []

# PDF 파일 업로드
if "vector_store_id" not in st.session_state:

    uploaded_file = st.file_uploader(
        "PDF 파일을 업로드하세요.",
        type=["pdf"],
        accept_multiple_files=False
    )

    if uploaded_file is not None:

        if st.button("PDF 업로드 및 준비"):

            if "openai_client" not in st.session_state:
                st.warning("사이드바에 API Key를 입력해주세요.")

            else:
                client = st.session_state["openai_client"]

                try:
                    with st.spinner("PDF를 업로드하고 분석하고 있습니다..."):

                        # Vector Store 생성
                        vector_store = client.vector_stores.create(
                            name=uploaded_file.name
                        )

                        # PDF 파일 업로드 및 검색 준비
                        client.vector_stores.files.upload_and_poll(
                            vector_store_id=vector_store.id,
                            file=(
                                uploaded_file.name,
                                uploaded_file.getvalue(),
                                "application/pdf"
                            )
                        )

                        # Vector Store ID 저장
                        st.session_state["vector_store_id"] = vector_store.id
                        st.session_state["pdf_filename"] = uploaded_file.name

                    st.success("PDF 준비가 완료되었습니다!")
                    st.rerun()

                except Exception as e:
                    st.error(f"PDF 업로드 오류: {e}")

# PDF가 준비된 경우
if "vector_store_id" in st.session_state:

    client = st.session_state["openai_client"]

    st.success(
        f"현재 파일: {st.session_state['pdf_filename']}"
    )

    # Clear와 Leave 버튼
    col1, col2 = st.columns(2)

    with col1:
        st.button("Clear", on_click=clear_chat)

    
    with col2:
        if st.button("Leave"):

            vector_store_id = st.session_state.get(
                "vector_store_id"
            )

            try:
                client.vector_stores.delete(
                    vector_store_id=vector_store_id
                )

                st.success("Vector Store가 삭제되었습니다.")

            except Exception as e:

                # 이미 삭제된 경우도 업로드 화면으로 돌아가도록 처리
                if "404" in str(e):
                    st.warning(
                        "Vector Store가 이미 삭제되었거나 "
                        "현재 API Key에서 찾을 수 없습니다."
                    )
                else:
                    st.error(f"삭제 오류: {e}")

                    # 다른 오류라면 상태를 유지
                    st.stop()

            # 세션 데이터 초기화
            st.session_state.pop("vector_store_id", None)
            st.session_state.pop("pdf_filename", None)
            st.session_state.pdf_messages = []

            st.rerun()

    # 이전 대화 출력
    for message in st.session_state.pdf_messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])

    # 질문 입력
    if prompt := st.chat_input("PDF에 대해 질문하세요."):

        st.session_state.pdf_messages.append({
            "role": "user",
            "content": prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

        with st.chat_message("assistant"):

            try:
                stream = client.responses.create(
                    model="gpt-6-luna",
                    instructions="업로드된 PDF 파일의 내용을 바탕으로 질문에 답변하세요. 문서에 없는 내용은 추측하지 말고 문서에서 확인할 수 없다고 알려주세요.",
                    input=st.session_state.pdf_messages,
                    tools=[
                        {
                            "type": "file_search",
                            "vector_store_ids": [
                                st.session_state["vector_store_id"]
                            ]
                        }
                    ],
                    stream=True
                )
    
                
                # 스트리밍 응답 처리
                def generate_text(stream):

                    buffer = ""
                    marker_start = "filecite"
                    marker_end = ""

                    for event in stream:

                        if event.type != "response.output_text.delta":
                            continue

                        buffer += event.delta

                        while True:

                            # 파일 인용 표시 시작 위치 찾기
                            start = buffer.find(marker_start)

                            if start != -1:

                                # 인용 표시 앞의 일반 텍스트 출력
                                if start > 0:
                                    yield buffer[:start]

                                # 인용 표시 끝 위치 찾기
                                end = buffer.find(
                                    marker_end,
                                    start + len(marker_start)
                                )

                                # 인용 표시가 아직 완성되지 않았다면 대기
                                if end == -1:
                                    buffer = buffer[start:]
                                    break

                                # 인용 표시 제거
                                buffer = buffer[end + len(marker_end):]
                                continue

                            # 인용 표시가 여러 조각으로 나뉘어 들어오는 경우 처리
                            keep = 0

                            for i in range(1, min(len(marker_start), len(buffer) + 1)):
                                if marker_start.startswith(buffer[-i:]):
                                    keep = i

                            if keep:
                                safe_text = buffer[:-keep]
                                buffer = buffer[-keep:]
                            else:
                                safe_text = buffer
                                buffer = ""

                            if safe_text:
                                yield safe_text

                            break

                    # 마지막에 남은 일반 텍스트 출력
                    if buffer and not marker_start.startswith(buffer):
                        yield buffer


                # 실시간 스트리밍 출력
                response = st.write_stream(
                    generate_text(stream)
                )



                st.session_state.pdf_messages.append({
                    "role": "assistant",
                    "content": response
                })

            except Exception as e:
                st.error(f"답변 생성 오류: {e}")
