import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="수학 문제 AI 변환기", layout="wide")

st.title("📐 수학 문제 이미지 → 텍스트 변환기")
st.info("이미지를 업로드하면 AI가 문제를 분석하여 텍스트로 추출해줍니다.")

# 사이드바에서 API 키 입력 받기
with st.sidebar:
    st.header("설정")
    api_key = st.text_input("Gemini API Key를 입력하세요", type="password")
    st.markdown("[API 키 발급받기](https://aistudio.google.com/app/apikey)")

if not api_key:
    st.warning("왼쪽 사이드바에 API Key를 입력해 주세요.")
    st.stop()

# AI 설정
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

uploaded_file = st.file_uploader("수학 문제 이미지를 업로드하세요", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    image = Image.open(uploaded_file)
    st.image(image, caption='업로드된 이미지', width=400)
    
    if st.button("AI 분석 시작"):
        with st.spinner("AI가 문제를 분석 중입니다..."):
            try:
                # 분석 요청
                prompt = "이 수학 문제 이미지의 내용을 텍스트로 정확히 추출하고, 풀이와 정답을 정리해줘."
                response = model.generate_content([prompt, image])
                
                st.success("분석 완료!")
                st.markdown("### 📝 분석 결과")
                st.write(response.text)
                
                # 복사하기 편하게 텍스트 영역 제공
                st.text_area("결과 복사하기 (Ctrl+C)", value=response.text, height=300)
                
            except Exception as e:
                st.error(f"에러 발생: {e}")
