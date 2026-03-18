import streamlit as st
import google.generativeai as genai
from pyhwpx import Hwp
import re
import os
from PIL import Image
import io

# --- [1. 수식 번역 및 HWP 처리 함수] ---
def latex_to_hwp(script):
    script = script.replace('=', ' = ').replace('+', ' + ').replace('-', ' - ')
    script = script.replace('implies', ' # rarrow # ')
    script = re.sub(r'\\frac\{(.*?)\}\{(.*?)\}', r'{\1} over { \2 }', script)
    script = re.sub(r'([a-zA-Z0-9\(\)]+)/([a-zA-Z0-9\(\)]+)', r'{\1} over { \2 }', script)
    replacements = {
        r'\sqrt': 'root', r'\pm': '+-', r'\ge': '>=', r'\le': '<=',
        r'\times': 'times', r'\pi': 'pi', r'\therefore': 'therefor', r'\cdot': 'times'
    }
    for old, new in replacements.items():
        script = script.replace(old, new)
    return script.replace('\\', '').strip()

def insert_eq(hwp, script, font_name, font_size):
    try:
        h_script = latex_to_hwp(script)
        pset = hwp.HParameterSet.HEqEdit
        hwp.HAction.GetDefault("EquationCreate", pset.HSet)
        pset.string = h_script
        pset.EqFontName = font_name
        pset.BaseUnit = hwp.PointToHwpUnit(float(font_size))
        hwp.HAction.Execute("EquationCreate", pset.HSet)
        hwp.Run("MoveRight")
        hwp.insert_text(" ") 
    except:
        pass

# --- [2. 웹 화면 레이아웃 설정] ---
st.set_page_config(page_title="Math AI HWP Converter", page_icon="📐", layout="wide")

# 사이드바: 제작자 정보 및 설정
with st.sidebar:
    st.title("👨‍🏫 제작자 정보")
    st.info("**꽃미남 강사**\n\n본 도구는 수학 강사님의 수업 자료 준비 시간을 단축하기 위해 제작되었습니다.")
    st.markdown("---")
    
    st.header("🔑 개인 API 설정")
    user_key = st.text_input("Gemini API Key 입력", type="password", 
                            help="Google AI Studio에서 발급받은 본인의 API 키를 입력하세요.")
    st.caption("[여기서 API 키 발급받기 (무료)](https://aistudio.google.com/app/apikey)")
    
    st.divider()
    st.header("⚙️ 문서 세부 설정")
    file_name = st.text_input("HWP 파일명", value="수학문제_변환결과")
    selected_font = st.selectbox("수식 폰트", ["HancomEQN", "함초롬바탕", "돋움"])
    selected_size = st.number_input("기본 글자 크기", 8, 20, 10)

# --- [3. 메인 화면 설명 문구] ---
st.title("📐 AI 수학 문제 한글(HWP) 변환기")
st.subheader("이미지를 슥- 올리면, 자연스러운 해설지가 짠!")

# 사용법 안내 섹션
col_info1, col_info2, col_info3 = st.columns(3)
with col_info1:
    st.markdown("### 1️⃣ 키 입력\n왼쪽 사이드바에 본인의 **API 키**를 입력해 주세요.")
with col_info2:
    st.markdown("### 2️⃣ 이미지 업로드\n변환하고 싶은 **문제 캡처본**을 아래에 넣으세요.")
with col_info3:
    st.markdown("### 3️⃣ 자동 생성\n버튼을 누르면 AI가 분석 후 **HWP 파일을 생성**합니다.")

st.divider()

# --- [4. 파일 업로드 및 분석 로직] ---
uploaded_file = st.file_uploader("🖼️ 이미지 파일을 선택하거나 드래그하세요.", type=['png', 'jpg', 'jpeg'])

if uploaded_file:
    # 화면을 반으로 나눠 미리보기와 결과창 구성
    c1, c2 = st.columns([1, 1])
    
    with c1:
        st.image(uploaded_file, caption="업로드된 문제 이미지", use_container_width=True)
    
    with c2:
        st.write("### 🚀 실행")
        if st.button("한글(HWP) 파일 생성 시작", use_container_width=True):
            if not user_key:
                st.warning("⚠️ 왼쪽 사이드바에 **API Key**를 입력해야 작동합니다!")
            else:
                try:
                    with st.spinner('선생님의 API로 문제를 정밀 분석 중입니다...'):
                        # 사용자 API 설정
                        genai.configure(api_key=user_key)
                        model = genai.GenerativeModel('gemini-2.5-flash')
                        
                        # 이미지 전송 준비
                        img = Image.open(uploaded_file)
                        img.save("temp_input.png")
                        img_file = genai.upload_file("temp_input.png")
                        
                        prompt = """당신은 수학 전문 해설가겸 집필진입니다. 
                    다음 이미지를 바탕으로 [문제 복원]과 [해설]을 자연스러운 문장으로 작성하세요.
                    
                    **핵심 가이드:**
                    [문제] 문제는 원문을 그대로 작성하고 문제와 해설사이는 반드시 문단을 구분하십시요.
                    [해설]
                    1. 핵심 수식 위주로 가독성있게 간결하게 해설하세요.
                    2. '따라서', '즉', '그러므로', '이때' 등 접속사를 쓸때에는 반드시 문단 구분하십시요.
                    3. 평가원에서 출제한 문제의 형식과 어투를 최대한 모방하여 작성하세요.
                    4. 입니다, ~합니다, 등의 종결어미를 생략하고 평가원 해설지스럽게 작성하세요.
                    5. 모든 수식은 $...$ 사이에 넣고 한글 수식 문법을 준수하세요.
                    """
                        
                        res = model.generate_content([prompt, img])
                        
                        # HWP 생성 로직
                        hwp = Hwp()
                        parts = re.split(r'(\$.*?\$)', res.text, flags=re.DOTALL)
                        for part in parts:
                            if part.startswith('$') and part.endswith('$'):
                                insert_eq(hwp, part.strip('$'), selected_font, selected_size)
                            else:
                                clean_text = part.replace('\n', ' ').strip()
                                if clean_text:
                                    hwp.insert_text(clean_text)
                                    if "[문제]" in part or "[해설]" in part:
                                        hwp.Run("BreakPara")
                                        hwp.Run("BreakPara")
                        
                        # 결과 저장 및 다운로드 버튼
                        save_path = os.path.abspath(f"{file_name}.hwp")
                        hwp.save_as(save_path)
                        
                        st.balloons() # 축하 효과
                        st.success(f"✅ '{file_name}.hwp' 생성 완료!")
                        with open(save_path, "rb") as f:
                            st.download_button("📥 내 컴퓨터로 다운로드", f, file_name=f"{file_name}.hwp", use_container_width=True)
                except Exception as e:
                    st.error(f"❌ 오류 발생: {str(e)}\n\nAPI 키가 유효한지, 혹은 이미지 파일이 손상되지 않았는지 확인해 주세요.")

st.markdown("---")
st.caption("Powered by Gemini AI & pyhwpx | Developed for Teachers")