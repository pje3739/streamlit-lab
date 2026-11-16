
import streamlit as st
from openai import OpenAI

st.title("GPT 질문 응답 프로그램")

# 응답 함수 캐싱
@st.cache_data
def get_response(question, api_key):
    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model="gpt-6-luna",
        input=question
    )

    return response.output_text


# 질문 입력
question = st.text_input("질문을 입력하세요.")

# 버튼 클릭
api_key = st.session_state.get("api_key")

if st.button("질문하기"):

    if not api_key:
        st.warning("사이드바에 API Key를 입력해주세요.")

    elif not question:
        st.warning("질문을 입력해주세요.")

    else:
        with st.spinner("답변을 생성하고 있습니다..."):
            try:
                answer = get_response(question, api_key)
                st.subheader("GPT 답변")
                st.write(answer)

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")


import base64

st.divider()

st.header("AI 이미지 생성")

# 이미지 프롬프트 입력
prompt = st.text_input("생성할 이미지에 대해 설명해주세요.")

# 이미지 생성 버튼
if st.button("이미지 생성하기"):

    if not api_key:
        st.warning("API Key를 먼저 입력해주세요.")

    elif not prompt:
        st.warning("이미지 설명을 입력해주세요.")

    else:
        client = st.session_state["openai_client"]

        with st.spinner("이미지를 생성하고 있습니다..."):
            try:
                img = client.images.generate(
                    model="gpt-image-2.6-flare",
                    prompt=prompt
                )

                image_bytes = base64.b64decode(
                    img.data[0].b64_json
                )

                st.image(image_bytes)

            except Exception as e:
                st.error(f"이미지 생성 오류: {e}")
