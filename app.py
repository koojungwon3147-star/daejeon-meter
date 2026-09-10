import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------------------------------------------
# 1. 사학연금공단(tp.or.kr) 스타일 헤더 & 디자인
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

.tp-top-bar {
    background-color: #2A2F5C;
    color: #FFFFFF;
    padding: 6px 16px;
    font-size: 12px;
    font-weight: 500;
    border-radius: 4px 4px 0 0;
}
.tp-header {
    background-color: #FFFFFF;
    border-bottom: 2px solid #1B75BC;
    padding: 14px 16px 12px 16px;
    margin-bottom: 15px;
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

.tp-info-box {
    background-color: #EAF3FB;
    border: 1px solid #D2E4F5;
    border-radius: 6px;
    padding: 14px 16px;
    margin-bottom: 15px;
    font-size: 14px;
    color: #2A2F5C;
    line-height: 1.6;
}

.tp-done-box {
    background-color: #E8F5E9;
    border: 1px solid #C8E6C9;
    border-radius: 6px;
    padding: 10px 14px;
    margin-bottom: 15px;
    font-size: 13px;
    font-weight: 600;
    color: #2E7D32;
}

.tp-section-title {
    font-size: 15px;
    font-weight: 700;
    color: #2A2F5C;
    border-left: 3px solid #1B75BC;
    padding-left: 8px;
    margin: 18px 0 10px 0;
}

.stButton > button {
    background-color: #1B75BC !important;
    color: #FFFFFF !important;
    font-size: 16px !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
    border: 1px solid #1B75BC !important;
    padding: 12px 0 !important;
    transition: all 0.2s ease !important;
    margin-top: 15px;
}
.stButton > button:hover {
    background-color: #155A94 !important;
    box-shadow: 0 4px 12px rgba(27,117,188,0.25) !important;
}

div[data-baseweb="select"], div[data-baseweb="input"] {
    border-radius: 6px !important;
}
</style>

<div class="tp-top-bar">시설관리팀 종합검침시스템 │ 대전회관</div>
<div class="tp-header">
    <div class="tp-header-title">⚡ <span>대전회관</span> 전기계량기 검침 (2026.09)</div>
</div>
"""
st.markdown(tp_custom_css, unsafe_allow_html=True)

# ----------------------------------------------------
# 2. 구글 시트 연동 함수
# ----------------------------------------------------
def get_google_sheet():
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        sec = st.secrets["gcp_service_account"]
        secret_dict = {
            "type": sec["type"],
            "project_id": sec["project_id"],
            "private_key_id": sec["private_key_id"],
            "private_key": sec["private_key"].replace("\\n", "\n"),
            "client_email": sec["client_email"],
            "client_id": sec["client_id"],
            "auth_uri": sec["auth_uri"],
            "token_uri": sec["token_uri"],
            "auth_provider_x509_cert_url": sec["auth_provider_x509_cert_url"],
            "client_x509_cert_url": sec["client_x509_cert_url"]
        }
        creds = ServiceAccountCredentials.from_json_keyfile_dict(secret_dict, scope)
        client = gspread.authorize(creds)
        doc = client.open("대전회관 전기계량기 검침")
        sheet = doc.worksheet("2026년9월")
        return sheet
    except Exception as e:
        st.error(f"❌ 에러 이유: {e}")
        return None

# ----------------------------------------------------
# 3. 65개 계량기 마스터 데이터
# ----------------------------------------------------
RAW_METERS = [
    {"id": "m1", "no": 1, "company": "20F 티피에스㈜", "meter": "컨택센터 UPS", "ct_ratio": 30, "prev_val": 2277.0},
    {"id": "m2", "no": 2, "company": "20F 티피에스㈜", "meter": "컨택센터 EHP", "ct_ratio": 1, "prev_val": 35853.0},
    {"id": "m3", "no": 54, "company": "20F 신한카드 채권관리팀", "meter": "EHP", "ct_ratio": 1, "prev_val": 7921.0},
    {"id": "m4", "no": 55, "company": "20F KB라이프", "meter": "EHP", "ct_ratio": 1, "prev_val": 2727.0},
    {"id": "m5", "no": 56, "company": "20F ABL생명", "meter": "EHP", "ct_ratio": 1, "prev_val": 4603.0},
    {"id": "m6", "no": 4, "company": "19F 근로복지공단", "meter": "19F PAC에어컨", "ct_ratio": 1, "prev_val": 12722.0},
    {"id": "m7", "no": 5, "company": "19F 이연", "meter": "에어컨", "ct_ratio": 1, "prev_val": 4547.0},
    {"id": "m8", "no": 6, "company": "19F 프레제니우스 메디칼 케어", "meter": "EHP", "ct_ratio": 1, "prev_val": 5029.0},
    {"id": "m9", "no": 52, "company": "18F 한국부동산원", "meter": "에어컨", "ct_ratio": 1, "prev_val": 1704.0},
    {"id": "m10", "no": 60, "company": "18F A+에셋", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 1464.0},
    {"id": "m11", "no": 53, "company": "15F A+에셋", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 7888.0},
    {"id": "m12", "no": 7, "company": "14F 신한카드", "meter": "EHP", "ct_ratio": 1, "prev_val": 28258.0},
    {"id": "m13", "no": 56, "company": "13F 시마즈 사이언티픽 코리아", "meter": "EHP", "ct_ratio": 1, "prev_val": 8545.0},
    {"id": "m14", "no": 9, "company": "12F A+에셋", "meter": "12층실외기", "ct_ratio": 1, "prev_val": 162212.0},
    {"id": "m15", "no": 10, "company": "12F A+에셋", "meter": "남측돌출간판", "ct_ratio": 1, "prev_val": 4052.0},
    {"id": "m16", "no": 11, "company": "11F 근로복지공단", "meter": "11층 EHP", "ct_ratio": 1, "prev_val": 11487.0},
    {"id": "m17", "no": 12, "company": "10F 법률사무소", "meter": "PAC에어컨 1", "ct_ratio": 1, "prev_val": 174022.0},
    {"id": "m18", "no": 13, "company": "10F 법률사무소", "meter": "PAC에어컨 2", "ct_ratio": 1, "prev_val": 75763.0},
    {"id": "m19", "no": 14, "company": "10F 법률사무소", "meter": "돌출간판", "ct_ratio": 1, "prev_val": 4307.0},
    {"id": "m20", "no": 15, "company": "8F A+ 에셋", "meter": "에어컨", "ct_ratio": 1, "prev_val": 130371.0},
    {"id": "m21", "no": 16, "company": "7F OTIS", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 133716.0},
    {"id": "m22", "no": 17, "company": "5F KPC한국 생산성본부", "meter": "돌출간판", "ct_ratio": 1, "prev_val": 1946.0},
    {"id": "m23", "no": 18, "company": "4F 라이나생명", "meter": "사무실 EHP", "ct_ratio": 1, "prev_val": 17097.0},
    {"id": "m24", "no": 19, "company": "㈜빌라드 알티오라", "meter": "3F 계산 및 정산실", "ct_ratio": 1, "prev_val": 73150.0},
    {"id": "m25", "no": 20, "company": "㈜빌라드 알티오라", "meter": "주방동력2", "ct_ratio": 8, "prev_val": 117128.0},
    {"id": "m26", "no": 21, "company": "㈜빌라드 알티오라", "meter": "주방동력1", "ct_ratio": 20, "prev_val": 33635.0},
    {"id": "m27", "no": 22, "company": "㈜빌라드 알티오라", "meter": "3층(동측에어컨)", "ct_ratio": 1, "prev_val": 50173.0},
    {"id": "m28", "no": 23, "company": "㈜빌라드 알티오라", "meter": "서측 벽간판", "ct_ratio": 1, "prev_val": 1856.0},
    {"id": "m29", "no": 24, "company": "㈜빌라드 알티오라", "meter": "2층 후문계단쪽 PAC (B1층 EPS실)", "ct_ratio": 1, "prev_val": 69297.0},
    {"id": "m30", "no": 25, "company": "㈜빌라드 알티오라", "meter": "웨딩예약실PAC (2층 EPS실)", "ct_ratio": 1, "prev_val": 56915.0},
    {"id": "m31", "no": 26, "company": "㈜빌라드 알티오라", "meter": "웨딩홀PAC (3층 음향실)", "ct_ratio": 1, "prev_val": 36712.0},
    {"id": "m32", "no": 27, "company": "㈜빌라드 알티오라", "meter": "B4층 냉동기", "ct_ratio": 1, "prev_val": 49517.0},
    {"id": "m33", "no": 28, "company": "박기섭한의원", "meter": "돌출간판, 서측 벽간판", "ct_ratio": 1, "prev_val": 11086.0},
    {"id": "m34", "no": 29, "company": "박기섭한의원", "meter": "일반전열", "ct_ratio": 1, "prev_val": 312913.0},
    {"id": "m35", "no": 32, "company": "고반식당", "meter": "일반전열", "ct_ratio": 1, "prev_val": 50699.0},
    {"id": "m36", "no": 33, "company": "고반식당", "meter": "비상전열", "ct_ratio": 1, "prev_val": 141249.0},
    {"id": "m37", "no": 34, "company": "고반식당", "meter": "에어컨", "ct_ratio": 1, "prev_val": 137368.0},
    {"id": "m38", "no": 36, "company": "동문꽃방", "meter": "쇼케이스냉장고", "ct_ratio": 1, "prev_val": 35642.0},
    {"id": "m39", "no": 37, "company": "청사치과", "meter": "서측 벽간판", "ct_ratio": 1, "prev_val": 1201.0},
    {"id": "m40", "no": 57, "company": "해이커피", "meter": "일반전열", "ct_ratio": 1, "prev_val": 18147.0},
    {"id": "m41", "no": 58, "company": "현대캐피탈", "meter": "EHP", "ct_ratio": 1, "prev_val": 1280.0},
    {"id": "m42", "no": 38, "company": "플렉스 볼링센터", "meter": "볼링장 동력", "ct_ratio": 30, "prev_val": 33359.0},
    {"id": "m43", "no": 39, "company": "플렉스 볼링센터", "meter": "서측 벽간판", "ct_ratio": 1, "prev_val": 2299.0},
    {"id": "m44", "no": 40, "company": "플렉스 볼링센터", "meter": "천정형 에어컨1", "ct_ratio": 1, "prev_val": 198439.0},
    {"id": "m45", "no": 41, "company": "플렉스 볼링센터", "meter": "천정형 에어컨2", "ct_ratio": 1, "prev_val": 18562.0},
    {"id": "m46", "no": 42, "company": "플렉스 볼링센터", "meter": "천정형 에어컨3", "ct_ratio": 1, "prev_val": 64081.0},
    {"id": "m47", "no": 43, "company": "플렉스 볼링센터", "meter": "일반전열", "ct_ratio": 1, "prev_val": 165407.0},
    {"id": "m48", "no": 46, "company": "플렉스 골프라운지", "meter": "서측 벽간판", "ct_ratio": 1, "prev_val": 2414.0},
    {"id": "m49", "no": 47, "company": "플렉스 골프라운지", "meter": "골프장 동력(하단)", "ct_ratio": 1, "prev_val": 136045.0},
    {"id": "m50", "no": 50, "company": "플렉스 골프라운지", "meter": "골프장 에어컨 - 1(상)", "ct_ratio": 1, "prev_val": 81118.0},
    {"id": "m51", "no": 51, "company": "플렉스 골프라운지", "meter": "골프장 에어컨 - 2(하)", "ct_ratio": 1, "prev_val": 34311.0},
    {"id": "m52", "no": "원격", "company": "19F 과학기술 보안관리단", "meter": "EHP", "ct_ratio": 1, "prev_val": 10967.0},
    {"id": "m53", "no": "원격", "company": "13F 과학기술 시설관리단", "meter": "EHP", "ct_ratio": 1, "prev_val": 15118.0},
    {"id": "m54", "no": "원격", "company": "13F 메리츠 캐피탈", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 6316.0},
    {"id": "m55", "no": "원격", "company": "12F 노무법인 태양", "meter": "EHP", "ct_ratio": 1, "prev_val": 4632.0},
    {"id": "m56", "no": "원격", "company": "11F 아이피 앤텍플러스", "meter": "EHP", "ct_ratio": 1, "prev_val": 8082.0},
    {"id": "m57", "no": "원격", "company": "9F A+ 에셋 (서측)", "meter": "EHP", "ct_ratio": 1, "prev_val": 28164.0},
    {"id": "m58", "no": "원격", "company": "9F A+ 에셋 (남측)", "meter": "EHP", "ct_ratio": 1, "prev_val": 316.0},
    {"id": "m59", "no": "원격", "company": "9F KODATA", "meter": "에어컨", "ct_ratio": 1, "prev_val": 8448.0},
    {"id": "m60", "no": "원격", "company": "6F 한국부동산원", "meter": "에어컨", "ct_ratio": 1, "prev_val": 12968.0},
    {"id": "m61", "no": "원격", "company": "4F 방송통신심의위원회", "meter": "PAC에어컨", "ct_ratio": 1, "prev_val": 20804.0},
    {"id": "m62", "no": "원격", "company": "4F F&U", "meter": "EHP", "ct_ratio": 1, "prev_val": 2108.0},
    {"id": "m63", "no": 59, "company": "4F F&U", "meter": "시스템실", "ct_ratio": 1, "prev_val": 9936.0},
    {"id": "m64", "no": 48, "company": "공동 (볼링/골프)", "meter": "썬큰간판 (1F 후문화단)", "ct_ratio": 1, "prev_val": 24072.0},
    {"id": "m65", "no": 49, "company": "공동 (한의원/치과/꽃방/볼링/웨딩)", "meter": "1F 지주식 광고입간판", "ct_ratio": 1, "prev_val": 11260.0}
]

if 'completed_records' not in st.session_state:
    st.session_state.completed_records = {}

# ----------------------------------------------------
# 4. 현황 게이지 및 필터
# ----------------------------------------------------
total_count = len(RAW_METERS)
done_count = len(st.session_state.completed_records)
progress_ratio = done_count / total_count

st.markdown(f"**검침 진행 현황:** **{done_count}** / {total_count}개 완료 ({int(progress_ratio*100)}%)")
st.progress(progress_ratio)

col_filter1, col_filter2 = st.columns([2, 1])
with col_filter1:
    only_uncompleted = st.checkbox("⏳ 미검침 계량기만 모아보기", value=False)

# ----------------------------------------------------
# 5. 검침 대상 선택
# ----------------------------------------------------
options = []
display_to_meter = {}

for idx, m in enumerate(RAW_METERS):
    is_done = m['id'] in st.session_state.completed_records
    if only_uncompleted and is_done:
        continue
    tag = "✅ [완료]" if is_done else "⬜ [대기]"
    label = f"{tag} [{m['company']}] {m['meter']} (NO.{m['no']})"
    options.append(label)
    display_to_meter[label] = m

st.markdown('<div class="tp-section-title">검침 대상 선택</div>', unsafe_allow_html=True)

if not options:
    st.success("🎉 모든 계량기의 검침이 완료되었습니다!")
    st.stop()

selected_label = st.selectbox("검침 계량기를 선택하세요", options, label_visibility="collapsed")
curr_data = display_to_meter[selected_label]
is_curr_done = curr_data['id'] in st.session_state.completed_records

if is_curr_done:
    done_val = st.session_state.completed_records[curr_data['id']]
    done_diff = round(done_val - curr_data['prev_val'], 2)
    done_usage = round(done_diff * curr_data['ct_ratio'], 2)
    st.markdown(f"""
    <div class="tp-done-box">
        ✅ <b>검침 완료된 항목입니다.</b> (입력값: {done_val:,.1f} kWh │ 사용량: {done_usage:,.1f} kWh)
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="tp-info-box">
    <b>위치/업체:</b> {curr_data['company']} &nbsp;│&nbsp; <b>계량기:</b> {curr_data['meter']}<br>
    <b>전월 지침:</b> {curr_data['prev_val']:,.1f} kWh &nbsp;│&nbsp; <b>적용 배율:</b> ×{curr_data['ct_ratio']}
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 6. 당월 지침 입력
# ----------------------------------------------------
st.markdown('<div class="tp-section-title">당월 지침값 입력</div>', unsafe_allow_html=True)
default_input = float(st.session_state.completed_records.get(curr_data['id'], curr_data['prev_val']))

current_val = st.number_input(
    "당월 지침값", 
    value=default_input, 
    step=0.1, 
    format="%.1f", 
    label_visibility="collapsed"
)

# ----------------------------------------------------
# 7. 실시간 차이 계산 & 구글 시트 저장
# ----------------------------------------------------
diff = round(current_val - curr_data['prev_val'], 2)
actual_usage = round(diff * curr_data['ct_ratio'], 2)

col1, col2 = st.columns(2)
with col1:
    st.metric("지침 차이", f"{diff:,.1f}")
with col2:
    st.metric("당월 사용량 (배율 적용)", f"{actual_usage:,.1f} kWh")

if diff < 0:
    st.error("⚠️ 주의: 당월 지침이 전월 지침보다 작습니다. 오입력을 확인하세요.")

if st.button("💾 검침 데이터 저장 및 시트 전송", use_container_width=True):
    st.session_state.completed_records[curr_data['id']] = current_val
    
    with st.spinner("구글 시트에 저장하는 중..."):
        sheet = get_google_sheet()
        if sheet:
            row_idx = RAW_METERS.index(curr_data) + 2  # 2행부터 시작
            # E열(5): 당월지침, F열(6): 차이, G열(7): 사용량
            sheet.update_cell(row_idx, 5, current_val)
            sheet.update_cell(row_idx, 6, diff)
            sheet.update_cell(row_idx, 7, actual_usage)
            st.success(f"🎉 [{curr_data['company']}] 구글 시트에 정상 반영되었습니다!")
            st.balloons()
        else:
            st.error("❌ 구글 시트 연결에 실패했습니다. 아래 Secrets 설정을 확인하세요.")
