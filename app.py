import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------------------------------------------
# 1. 화면 스타일 (밝은 모드/다크 모드 완벽 고정 테마)
# ----------------------------------------------------
st.set_page_config(page_title="대전회관 전기계량기 검침", layout="centered")

tp_custom_css = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;500;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Noto Sans KR', sans-serif !important;
}

/* 상단 사학연금/티피에스 남색 바 */
.tp-top-bar {
    background-color: #2A2F5C !important;
    color: #FFFFFF !important;
    padding: 8px 16px;
    font-size: 14px;
    font-weight: 600;
    border-radius: 6px 6px 0 0;
}

/* 타이틀 헤더 */
.tp-header {
    background-color: #FFFFFF !important;
    border: 1px solid #E2E8F0;
    border-bottom: 3px solid #1B75BC !important;
    padding: 16px 18px 14px 18px;
    margin-bottom: 18px;
    border-radius: 0 0 6px 6px;
}
.tp-header-title {
    font-size: 22px;
    font-weight: 700;
    color: #2A2F5C !important;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.tp-header-title span {
    color: #1B75BC !important;
}

/* 계량기 상세 안내 박스 (폰트 16px 확대) */
.tp-info-box {
    background-color: #F0F7FD !important;
    border: 1px solid #BEE3F8 !important;
    border-radius: 8px;
    padding: 16px 18px;
    margin-bottom: 15px;
    font-size: 16px;
    color: #1A365D !important;
    line-height: 1.7;
}

/* 완료 녹색 안내 박스 (폰트 15px 확대) */
.tp-done-box {
    background-color: #F0FFF4 !important;
    border: 1px solid #C6F6D5 !important;
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 15px;
    font-size: 15px;
    font-weight: 600;
    color: #22543D !important;
}

/* 섹션 타이틀 (17px 확대) */
.tp-section-title {
    font-size: 17px;
    font-weight: 700;
    color: #2A2F5C !important;
    border-left: 4px solid #1B75BC;
    padding-left: 10px;
    margin: 20px 0 12px 0;
}

/* 드롭다운 & 텍스트/숫자 입력창 크기 확대 (22px & 볼드) */
div[data-baseweb="select"] * {
    font-size: 16px !important;
}
div[data-baseweb="input"] input {
    font-size: 22px !important;
    font-weight: 700 !important;
    height: 48px !important;
}

/* 우측 새로고침 미니 버튼 */
div[data-testid="column"]:nth-child(2) button {
    height: 40px !important;
    font-size: 14px !important;
    padding: 0px 12px !important;
    border-radius: 6px !important;
}

/* 하단 검침 저장 버튼 (18px 강조) */
.stButton > button:last-child {
    background-color: #1B75BC !important;
    color: #FFFFFF !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 16px 0 !important;
    margin-top: 18px !important;
    box-shadow: 0 4px 6px rgba(27, 117, 188, 0.2) !important;
}

.stButton > button:last-child p {
    color: #FFFFFF !important;
    font-size: 18px !important;
    font-weight: 700 !important;
}
</style>

<div class="tp-top-bar">티피에스 주식회사 │ 대전회관</div>
<div class="tp-header">
    <div class="tp-header-title">⚡ <span>대전회관</span> 전기계량기 검침 대장</div>
</div>
"""
st.markdown(tp_custom_css, unsafe_allow_html=True)

# ----------------------------------------------------
# 2. 구글 스프레드시트 연결 엔진
# ----------------------------------------------------
@st.cache_resource
def get_spreadsheet_client():
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
        return doc
    except Exception as e:
        st.error(f"❌ 구글 시트 연결 실패: {e}")
        return None

doc = get_spreadsheet_client()
if not doc:
    st.stop()

# ----------------------------------------------------
# 3. 실시간 탭(월) 목록 가져오기
# ----------------------------------------------------
worksheet_list = [ws.title for ws in doc.worksheets()]
default_tab_index = 0
for idx, title in enumerate(worksheet_list):
    if "9월" in title or "2026년 9월" in title or "2026년9월" in title:
        default_tab_index = idx
        break

selected_month = st.selectbox("📅 검침 대상 월 (시트 탭 선택)", worksheet_list, index=default_tab_index)
sheet = doc.worksheet(selected_month)

# ----------------------------------------------------
# 4. 헤더 자동 분석 및 데이터 파싱
# ----------------------------------------------------
all_rows = sheet.get_all_values()
if len(all_rows) < 2:
    st.warning("⚠️ 시트에 데이터가 없습니다.")
    st.stop()

header = all_rows[0]

def find_col_idx(names):
    for target in names:
        for idx, col_name in enumerate(header):
            clean_name = col_name.replace(" ", "").strip()
            if clean_name == target:
                return idx
    return -1

col_company = find_col_idx(["업체명", "입주사명", "입주사"])
col_meter   = find_col_idx(["계량기명", "계량기형", "계량기"])
col_prev    = find_col_idx(["전월지침", "전출지침", "전월"])
col_curr    = find_col_idx(["당월지침", "금월지침", "금월", "당월"])
col_diff    = find_col_idx(["지침차", "지원차", "차이"])
col_ratio   = find_col_idx(["배율", "배비"])
col_usage   = find_col_idx(["사용량"])

col_company = 0 if col_company == -1 else col_company
col_meter = 1 if col_meter == -1 else col_meter

meters_data = []
completed_count = 0

for row_idx, row in enumerate(all_rows[1:], start=2):
    if not row or not row[col_company].strip():
        continue
    
    company = row[col_company].strip()
    meter_name = row[col_meter].strip() if len(row) > col_meter else "계량기"
    
    if "합계" in company or "총합계" in company:
        continue
        
    # 가상 간판 배분 행은 검침 목록에서 자동 제외
    is_virtual_split = (
        ("광고입간판" in meter_name and "1F 지주식" not in meter_name) or
        ("썬큰간판" in meter_name and "후문" not in meter_name and "볼링/골프" not in company)
    )
    if is_virtual_split:
        continue
        
    ct_ratio = 1.0
    if col_ratio != -1 and len(row) > col_ratio and row[col_ratio].strip():
        try:
            ct_ratio = float(row[col_ratio].replace(',', ''))
        except ValueError:
            ct_ratio = 1.0

    prev_val = 0.0
    if col_prev != -1 and len(row) > col_prev and row[col_prev].strip():
        try:
            prev_val = float(row[col_prev].replace(',', ''))
        except ValueError:
            prev_val = 0.0

    curr_val = None
    if col_curr != -1 and len(row) > col_curr and row[col_curr].strip():
        try:
            curr_val = float(row[col_curr].replace(',', ''))
            completed_count += 1
        except ValueError:
            curr_val = None

    meters_data.append({
        "row_idx": row_idx,
        "company": company,
        "meter": meter_name,
        "ct_ratio": ct_ratio,
        "prev_val": prev_val,
        "curr_val": curr_val
    })

total_count = len(meters_data)

# ----------------------------------------------------
# 5. 진행 현황 & 미니 새로고침
# ----------------------------------------------------
progress_ratio = completed_count / total_count if total_count > 0 else 0
st.markdown(f"**검침 진행 현황:** **{completed_count}** / {total_count}개 완료 ({int(progress_ratio*100)}%)")
st.progress(progress_ratio)

col_filter1, col_filter2 = st.columns([2.5, 1])
with col_filter1:
    only_uncompleted = st.checkbox("⏳ 미검침 계량기만 모아보기", value=False)
with col_filter2:
    if st.button("🔄 새로고침", use_container_width=True):
        st.rerun()

# ----------------------------------------------------
# 6. 검침 대상 선택 (라벨에서 행 번호 제거)
# ----------------------------------------------------
options = []
label_to_item = {}

for m in meters_data:
    is_done = (m["curr_val"] is not None)
    if only_uncompleted and is_done:
        continue
    
    tag = "✅ [완료]" if is_done else "⬜ [대기]"
    # 행 번호 문구를 제외하고 가독성 최적화
    label = f"{tag} [{m['company']}] {m['meter']}"
    options.append(label)
    label_to_item[label] = m

st.markdown('<div class="tp-section-title">검침 대상 선택</div>', unsafe_allow_html=True)

if not options:
    st.success("🎉 모든 실물 계량기의 검침이 완료되었습니다!")
    st.stop()

# 자동 순차 이동을 위한 인덱스 제어
if 'selected_idx' not in st.session_state or st.session_state.selected_idx >= len(options):
    st.session_state.selected_idx = 0

selected_label = st.selectbox("검침 계량기 선택", options, index=st.session_state.selected_idx, label_visibility="collapsed")
curr_data = label_to_item[selected_label]
curr_idx = options.index(selected_label)
is_curr_done = (curr_data["curr_val"] is not None)

if is_curr_done:
    diff_recorded = int(round(curr_data["curr_val"] - curr_data["prev_val"]))
    usage_recorded = int(round(diff_recorded * curr_data["ct_ratio"]))
    st.markdown(f"""
    <div class="tp-done-box">
        ✅ <b>이미 기록된 계량기입니다.</b> (당월지침: <b>{int(curr_data['curr_val']):,d}</b> │ 사용량: <b>{usage_recorded:,d} kWh</b>)
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="tp-info-box">
    <b>입주사:</b> {curr_data['company']} &nbsp;│&nbsp; <b>계량기:</b> {curr_data['meter']}<br>
    <b>전월 지침:</b> {int(curr_data['prev_val']):,d} kWh &nbsp;│&nbsp; <b>적용 배율:</b> ×{int(curr_data['ct_ratio']) if curr_data['ct_ratio'].is_integer() else curr_data['ct_ratio']}
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 7. 당월 지침 입력 & 자동 계산
# ----------------------------------------------------
st.markdown('<div class="tp-section-title">당월 지침값 입력</div>', unsafe_allow_html=True)

default_val = int(curr_data["curr_val"]) if curr_data["curr_val"] is not None else int(curr_data["prev_val"])

input_val = st.number_input(
    "당월 지침값", 
    value=default_val, 
    step=1, 
    format="%d", 
    label_visibility="collapsed"
)

diff = int(input_val - int(curr_data["prev_val"]))
actual_usage = int(diff * curr_data["ct_ratio"])

col1, col2 = st.columns(2)
with col1:
    st.metric("지침 차이", f"{diff:,}")
with col2:
    st.metric("당월 사용량 (배율 적용)", f"{actual_usage:,} kWh")

if diff < 0:
    st.error("⚠️ 주의: 당월 지침이 전월 지침보다 작습니다. 오입력을 확인하세요.")

# 공동 간판 실시간 배분 안내 박스
if "썬큰간판" in curr_data["meter"]:
    split_2 = round(actual_usage / 2, 1)
    st.info(f"""
    📢 **[공동 간판 배분 계산기 (1/2 배분)]**
    * 총 검침 사용량: **{actual_usage:,} kWh**
    * 업체별 부담 (**플렉스 볼링센터 / 플렉스 골프라운지** 각 50%): **{split_2:,.1f} kWh**
    """)
elif "지주식" in curr_data["meter"]:
    split_5 = round(actual_usage / 5, 1)
    st.info(f"""
    📢 **[공동 간판 배분 계산기 (1/5 균등 배분)]**
    * 총 검침 사용량: **{actual_usage:,} kWh**
    * 업체별 부담 (**한의원 / 치과 / 꽃방 / 볼링 / 웨딩** 각 20%): **{split_5:,.1f} kWh**
    """)

# ----------------------------------------------------
# 8. 스마트 저장 및 다음 계량기 자동 이동
# ----------------------------------------------------
st.markdown('<div class="save-btn">', unsafe_allow_html=True)
if st.button("💾 검침 데이터 저장 및 다음 계량기로 이동", use_container_width=True):
    with st.spinner("구글 시트에 실시간 기록 중..."):
        row = curr_data["row_idx"]
        
        if col_curr != -1:
            sheet.update_cell(row, col_curr + 1, input_val)
        if col_diff != -1:
            sheet.update_cell(row, col_diff + 1, diff)
        if col_usage != -1:
            sheet.update_cell(row, col_usage + 1, actual_usage)
            
        # 다음 계량기로 포커스 자동 전환
        if curr_idx + 1 < len(options):
            st.session_state.selected_idx = curr_idx + 1
        else:
            st.session_state.selected_idx = 0
            
        st.toast(f"✅ [{curr_data['company']}] 저장 완료!", icon="💾")
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
