
import streamlit as st

st.title("GPT Chat")

# 대화 내용 초기화
if "messages" not in st.session_state:
    st.session_state.messages = []

# 대화 초기화 함수
def clear_chat():
    st.session_state.messages = []

# Clear 버튼
st.button("Clear", on_click=clear_chat)

# 이전 대화 출력
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# 사용자 질문 입력
if prompt := st.chat_input("메시지를 입력하세요."):

    if "openai_client" not in st.session_state:
        st.warning("API Key를 입력해주세요.")

    else:
        client = st.session_state["openai_client"]

        # 사용자 질문 저장
        st.session_state.messages.append({
            "role": "user",
            "content": prompt
        })

        # 사용자 질문 출력
        with st.chat_message("user"):
            st.write(prompt)

        # GPT 응답 생성
        with st.chat_message("assistant"):

            stream = client.responses.create(
                model="gpt-6-luna",
                input=st.session_state.messages,
                stream=True
            )

            response = st.write_stream(stream)

        # GPT 응답 저장
        st.session_state.messages.append({
            "role": "assistant",
            "content": response
        })
