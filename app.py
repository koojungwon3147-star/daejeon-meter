import streamlit as st
from google import genai
from PIL import Image
import io

# ----------------------------------------------------
# 1. 사학연금공단(tp.or.kr) 스타일 CSS 적용
# ----------------------------------------------------
st.set_page_config(page_title="대전회관 전기계량기 검침", layout="centered")

tp_custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif !important;
    color: #333333;
    background-color: #FFFFFF;
}

/* 상단 유틸리티 바 & 헤더 */
.tp-top-bar {
    background-color: #2A2F5C;
    color: #FFFFFF;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
    letter-spacing: -0.3px;
    border-radius: 4px 4px 0 0;
}
.tp-header {
    background-color: #FFFFFF;
    border-bottom: 2px solid #1B75BC;
    padding: 14px 16px 12px 16px;
    margin-bottom: 20px;
}
.tp-header-title {
    font-size: 20px;
    font-weight: 700;
    color: #2A2F5C;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.tp-header-title span {
    color: #1B75BC;
}

/* 안내 카드 & 정보 박스 */
.tp-info-box {
    background-color: #EAF3FB;
    border: 1px solid #D2E4F5;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #2A2F5C;
}

/* 섹션 타이틀 */
.tp-section-title {
    font-size: 15px;
    font-weight: 700;
    color: #2A2F5C;
    border-left: 3px solid #1B75BC;
    padding-left: 8px;
    margin: 18px 0 10px 0;
}

/* 버튼 스타일 */
.stButton > button {
    background-color: #1B75BC !important;
    color: #FFFFFF !important;
    font-weight: 500 !important;
    border-radius: 4px !important;
    border: 1px solid #1B75BC !important;
    transition: all 0.2s ease !important;
}
.stButton > button:hover {
    background-color: #155A94 !important;
    border-color: #155A94 !important;
    box-shadow: 0 2px 8px rgba(27,117,188,0.2) !important;
}

/* 인풋 필드 테두리 */
div[data-baseweb="select"], div[data-baseweb="input"] {
    border-radius: 4px !important;
}
</style>

<div class="tp-top-bar">시설관리팀 종합검침시스템 │ 대전회관</div>
<div class="tp-header">
    <div class="tp-header-title">⚡ <span>대전회관</span> 전기계량기 검침</div>
</div>
"""
st.markdown(tp_custom_css, unsafe_allow_html=True)

# ----------------------------------------------------
# 2. Gemini API 세팅
# ----------------------------------------------------
GEMINI_API_KEY = "AQ.Ab8RN6JnCPvk7EZJxnCs8r0_9TmR5MsPQaf4MnI2tolAyY7GnA"
client = genai.Client(api_key=GEMINI_API_KEY)

# ----------------------------------------------------
# 3. 72개 실사 계량기 마스터 데이터
# ----------------------------------------------------
REAL_METERS = [
    {"no": 1, "company": "20F 티피에스㈜", "meter": "컨택센터 UPS", "ct_ratio": 30, "prev_val": 2277.0},
    {"no": 2, "company": "20F 티피에스㈜", "meter": "컨택센터 EHP", "ct_ratio": 1, "prev_val": 35853.0},
    {"no": 54, "company": "20F 신한카드 채권관리팀", "meter": "EHP", "ct_ratio": 1, "prev_val": 7921.0},
    {"no": 55, "company": "20F KB라이프", "meter": "EHP", "ct_ratio": 1, "prev_val": 2727.0},
    {"no": 56, "company": "20F ABL생명", "meter": "EHP", "ct_ratio": 1, "prev_val": 4603.0},
    {"no": 4, "company": "19F 근로복지공단", "meter": "19F PAC에어컨", "ct_ratio": 1, "prev_val": 12722.0},
    {"no": 5, "company": "19F 이연", "meter": "에어컨", "ct_ratio": 1, "prev_val": 4547.0},
    {"no": 6, "company": "19F 프레제니우스 메디칼 케어", "meter": "EHP", "ct_ratio": 1, "prev_val": 5029.0},
    {"no": 52, "company": "18F 한국부동산원", "meter": "에어컨", "ct_ratio": 1, "prev_val": 1704.0},
    {"no": 60, "company": "18F A+에셋", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 1464.0},
    {"no": 53, "company": "15F A+에셋", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 7888.0},
    {"no": 7, "company": "14F 신한카드", "meter": "EHP", "ct_ratio": 1, "prev_val": 28258.0},
    {"no": 56, "company": "13F 시마즈 사이언티픽 코리아", "meter": "EHP", "ct_ratio": 1, "prev_val": 8545.0},
    {"no": 9, "company": "12F A+에셋", "meter": "12층실외기", "ct_ratio": 1, "prev_val": 162212.0},
    {"no": 10, "company": "12F A+에셋", "meter": "남측돌출간판", "ct_ratio": 1, "prev_val": 4052.0},
    {"no": 11, "company": "11F 근로복지공단", "meter": "11층 EHP", "ct_ratio": 1, "prev_val": 11487.0},
    {"no": 12, "company": "10F 법률사무소", "meter": "PAC에어컨 1", "ct_ratio": 1, "prev_val": 174022.0},
    {"no": 13, "company": "10F 법률사무소", "meter": "PAC에어컨 2", "ct_ratio": 1, "prev_val": 75763.0},
    {"no": 14, "company": "10F 법률사무소", "meter": "돌출간판", "ct_ratio": 1, "prev_val": 4307.0},
    {"no": 15, "company": "8F A+ 에셋", "meter": "에어컨", "ct_ratio": 1, "prev_val": 130371.0},
    {"no": 16, "company": "7F OTIS", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 133716.0},
    {"no": 17, "company": "5F KPC한국 생산성본부", "meter": "돌출간판", "ct_ratio": 1, "prev_val": 1946.0},
    {"no": 18, "company": "4F 라이나생명", "meter": "사무실 EHP", "ct_ratio": 1, "prev_val": 17097.0},
    {"no": 19, "company": "㈜빌라드 알티오라", "meter": "3F 계산 및 정산실", "ct_ratio": 1, "prev_val": 73150.0},
    {"no": 20, "company": "㈜빌라드 알티오라", "meter": "주방동력2", "ct_ratio": 8, "prev_val": 117128.0},
    {"no": 21, "company": "㈜빌라드 알티오라", "meter": "주방동력1", "ct_ratio": 20, "prev_val": 33635.0},
    {"no": 22, "company": "㈜빌라드 알티오라", "meter": "3층(동측에어컨)", "ct_ratio": 1, "prev_val": 50173.0},
    {"no": 23, "company": "㈜빌라드 알티오라", "meter": "서측 벽간판", "ct_ratio": 1, "prev_val": 1856.0},
    {"no": 24, "company": "㈜빌라드 알티오라", "meter": "2층 후문계단쪽 PAC (B1층 EPS실)", "ct_ratio": 1, "prev_val": 69297.0},
    {"no": 25, "company": "㈜빌라드 알티오라", "meter": "웨딩예약실PAC (2층 EPS실)", "ct_ratio": 1, "prev_val": 56915.0},
    {"no": 26, "company": "㈜빌라드 알티오라", "meter": "웨딩홀PAC (3층 음향실)", "ct_ratio": 1, "prev_val": 36712.0},
    {"no": 27, "company": "㈜빌라드 알티오라", "meter": "B4층 냉동기", "ct_ratio": 1, "prev_val": 49517.0},
    {"no": 28, "company": "박기섭한의원", "meter": "돌출간판, 서측 벽간판", "ct_ratio": 1, "prev_val": 11086.0},
    {"no": 29, "company": "박기섭한의원", "meter": "일반전열", "ct_ratio": 1, "prev_val": 312913.0},
    {"no": 32, "company": "고반식당", "meter": "일반전열", "ct_ratio": 1, "prev_val": 50699.0},
    {"no": 33, "company": "고반식당", "meter": "비상전열", "ct_ratio": 1, "prev_val": 141249.0},
    {"no": 34, "company": "고반식당", "meter": "에어컨", "ct_ratio": 1, "prev_val": 137368.0},
    {"no": 36, "company": "동문꽃방", "meter": "쇼케이스냉장고", "ct_ratio": 1, "prev_val": 35642.0},
    {"no": 37, "company": "청사치과", "meter": "서측 벽간판", "ct_ratio": 1, "prev_val": 1201.0},
    {"no": 57, "company": "해이커피", "meter": "일반전열", "ct_ratio": 1, "prev_val": 18147.0},
    {"no": 58, "company": "현대캐피탈", "meter": "EHP", "ct_ratio": 1, "prev_val": 1280.0},
    {"no": 38, "company": "플렉스 볼링센터", "meter": "볼링장 동력", "ct_ratio": 30, "prev_val": 33359.0},
    {"no": 39, "company": "플렉스 볼링센터", "meter": "서측 벽간판", "ct_ratio": 1, "prev_val": 2299.0},
    {"no": 40, "company": "플렉스 볼링센터", "meter": "천정형 에어컨1", "ct_ratio": 1, "prev_val": 198439.0},
    {"no": 41, "company": "플렉스 볼링센터", "meter": "천정형 에어컨2", "ct_ratio": 1, "prev_val": 18562.0},
    {"no": 42, "company": "플렉스 볼링센터", "meter": "천정형 에어컨3", "ct_ratio": 1, "prev_val": 64081.0},
    {"no": 43, "company": "플렉스 볼링센터", "meter": "일반전열", "ct_ratio": 1, "prev_val": 165407.0},
    {"no": 46, "company": "플렉스 골프라운지", "meter": "서측 벽간판", "ct_ratio": 1, "prev_val": 2414.0},
    {"no": 47, "company": "플렉스 골프라운지", "meter": "골프장 동력(하단)", "ct_ratio": 1, "prev_val": 136045.0},
    {"no": 50, "company": "플렉스 골프라운지", "meter": "골프장 에어컨 - 1(상)", "ct_ratio": 1, "prev_val": 81118.0},
    {"no": 51, "company": "플렉스 골프라운지", "meter": "골프장 에어컨 - 2(하)", "ct_ratio": 1, "prev_val": 34311.0},
    {"no": "원격", "company": "19F 과학기술 보안관리단", "meter": "EHP", "ct_ratio": 1, "prev_val": 10967.0},
    {"no": "원격", "company": "13F 과학기술 시설관리단", "meter": "EHP", "ct_ratio": 1, "prev_val": 15118.0},
    {"no": "원격", "company": "13F 메리츠 캐피탈", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 6316.0},
    {"no": "원격", "company": "12F 노무법인 태양", "meter": "EHP", "ct_ratio": 1, "prev_val": 4632.0},
    {"no": "원격", "company": "11F 아이피 앤텍플러스", "meter": "EHP", "ct_ratio": 1, "prev_val": 8082.0},
    {"no": "원격", "company": "9F A+ 에셋 (서측)", "meter": "EHP", "ct_ratio": 1, "prev_val": 28164.0},
    {"no": "원격", "company": "9F A+ 에셋 (남측)", "meter": "EHP", "ct_ratio": 1, "prev_val": 316.0},
    {"no": "원격", "company": "9F KODATA", "meter": "에어컨", "ct_ratio": 1, "prev_val": 8448.0},
    {"no": "원격", "company": "6F 한국부동산원", "meter": "에어컨", "ct_ratio": 1, "prev_val": 12968.0},
    {"no": "원격", "company": "4F 방송통신심의위원회", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 20804.0},
    {"no": "원격", "company": "4F F&U", "meter": "EHP", "ct_ratio": 1, "prev_val": 2108.0},
    {"no": 59, "company": "4F F&U", "meter": "시스템실", "ct_ratio": 1, "prev_val": 9936.0},
    {"no": 48, "company": "공동 (볼링/골프)", "meter": "썬큰간판 (1F 후문화단)", "ct_ratio": 1, "prev_val": 24072.0},
    {"no": 49, "company": "공동 (한의원/치과/꽃방/볼링/웨딩)", "meter": "1F 지주식 광고입간판", "ct_ratio": 1, "prev_val": 11260.0}
]

# ----------------------------------------------------
# 4. 상단 드롭다운 선택
# ----------------------------------------------------
st.markdown('<div class="tp-section-title">검침 대상 선택</div>', unsafe_allow_html=True)
meter_options = [f"[{m['company']}] {m['meter']} (NO.{m['no']})" for m in REAL_METERS]
selected_option = st.selectbox("검침 계량기를 선택하세요", meter_options, label_visibility="collapsed")

curr_data = next(m for m in REAL_METERS if f"[{m['company']}] {m['meter']} (NO.{m['no']})" == selected_option)

st.markdown(f"""
<div class="tp-info-box">
    <b>위치/업체:</b> {curr_data['company']} &nbsp;│&nbsp; <b>계량기:</b> {curr_data['meter']}<br>
    <b>전월 지침:</b> {curr_data['prev_val']:,.1f} kWh &nbsp;│&nbsp; <b>적용 배율:</b> ×{curr_data['ct_ratio']}
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 5. 당월 지침 입력 & 간이 카메라 버튼
# ----------------------------------------------------
st.markdown('<div class="tp-section-title">당월 지침값 입력</div>', unsafe_allow_html=True)

col_input, col_cam_btn = st.columns([4, 1])

if 'show_cam' not in st.session_state:
    st.session_state.show_cam = False

with col_cam_btn:
    st.write("")
    if st.button("📷 촬영", help="카메라로 계량기 숫자 자동 인식"):
        st.session_state.show_cam = not st.session_state.show_cam

detected_value = None

if st.session_state.show_cam:
    cam_box = st.container()
    with cam_box:
        camera_file = st.camera_input("계량기 LCD 화면을 비춰주세요", label_visibility="collapsed")
        if camera_file is not None:
            with st.spinner("숫자 판독 중..."):
                try:
                    img = Image.open(camera_file)
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG")
                    prompt = "전기계량기 누적 사용량 숫자만 소수점 포함 단독 출력해줘."
                    res = client.models.generate_content(
                        model='gemini-2.5-flash',
                        contents=[genai.types.Part.from_bytes(data=buf.getvalue(), mime_type="image/jpeg"), prompt]
                    )
                    detected_value = float(res.text.strip().replace(",", ""))
                    st.success(f"판독 완료: {detected_value}")
                    st.session_state.show_cam = False
                except Exception:
                    st.warning("판독 실패. 직접 입력해 주세요.")

with col_input:
    default_val = float(detected_value) if detected_value is not None else float(curr_data['prev_val'])
    current_val = st.number_input(
        "당월 지침값", 
        value=default_val, 
        step=0.1, 
        format="%.1f", 
        label_visibility="collapsed"
    )

# ----------------------------------------------------
# 6. 실시간 계산 및 저장
# ----------------------------------------------------
diff = round(current_val - curr_data['prev_val'], 2)
actual_usage = round(diff * curr_data['ct_ratio'], 2)

col_metric1, col_metric2 = st.columns(2)
with col_metric1:
    st.metric("지침 차이", f"{diff:,.1f}")
with col_metric2:
    st.metric("당월 사용량 (배율 적용)", f"{actual_usage:,.1f} kWh")

if diff < 0:
    st.error("⚠️ 당월 지침이 전월 지침보다 작습니다. 오입력을 확인하세요.")

if st.button("💾 검침 데이터 저장", use_container_width=True):
    st.success(f"[{curr_data['company']}] {current_val} kWh가 정상 저장되었습니다.")
    st.balloons()
