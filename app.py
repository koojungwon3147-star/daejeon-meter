import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------------------------------------------
# 1. 화면 스타일 (사학연금공단 블루 테마)
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
# 3. 구글 시트에서 실시간 탭(월) 목록 가져오기
# ----------------------------------------------------
worksheet_list = [ws.title for ws in doc.worksheets()]
default_tab_index = 0
for idx, title in enumerate(worksheet_list):
    if "2026년9월" in title:
        default_tab_index = idx
        break

selected_month = st.selectbox("📅 검침 대상 월 (시트 탭 선택)", worksheet_list, index=default_tab_index)
sheet = doc.worksheet(selected_month)

# ----------------------------------------------------
# 4. 구글 시트에서 전체 계량기 데이터 실시간 로드
# ----------------------------------------------------
all_rows = sheet.get_all_values()
if len(all_rows) < 2:
    st.warning("⚠️ 시트에 헤더 외에 입력된 데이터가 없습니다.")
    st.stop()

meters_data = []
completed_count = 0

for row_idx, row in enumerate(all_rows[1:], start=2):
    # A열이 비어있으면 건너뜀
    if not row or not row[0].strip():
        continue
    
    company = row[0].strip()
    meter_name = row[1].strip() if len(row) > 1 else "계량기"
    
    # 혹시 시트 아래쪽에 '배분'이나 '합계' 관련 별도 행이 있다면 자동 제외
    if "배분" in company or "배분" in meter_name or "합계" in company:
        continue
    
    # 배율 (C열)
    try:
        ct_ratio = float(row[2]) if len(row) > 2 and row[2].strip() else 1.0
    except ValueError:
        ct_ratio = 1.0
        
    # 전월지침 (D열)
    try:
        prev_val = float(row[3].replace(',', '')) if len(row) > 3 and row[3].strip() else 0.0
    except ValueError:
        prev_val = 0.0
        
    # 당월지침 (E열 - 이미 입력되었는지 확인)
    curr_val = None
    if len(row) > 4 and row[4].strip():
        try:
            curr_val = float(row[4].replace(',', ''))
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
if total_count == 0:
    st.warning("⚠️ 유효한 계량기 데이터가 없습니다. 시트를 확인해 주세요.")
    st.stop()

# ----------------------------------------------------
# 5. 실시간 진행 현황 게이지 & 필터
# ----------------------------------------------------
progress_ratio = completed_count / total_count
st.markdown(f"**검침 진행 현황:** **{completed_count}** / {total_count}개 완료 ({int(progress_ratio*100)}%)")
st.progress(progress_ratio)

col_filter1, col_filter2 = st.columns([2, 1])
with col_filter1:
    only_uncompleted = st.checkbox("⏳ 미검침 계량기만 모아보기", value=False)
with col_filter2:
    if st.button("🔄 시트 새로고침", use_container_width=True):
        st.rerun()

# ----------------------------------------------------
# 6. 검침 대상 선택
# ----------------------------------------------------
options = []
label_to_item = {}

for m in meters_data:
    is_done = (m["curr_val"] is not None)
    if only_uncompleted and is_done:
        continue
    
    tag = "✅ [완료]" if is_done else "⬜ [대기]"
    label = f"{tag} [{m['company']}] {m['meter']} (행 {m['row_idx']})"
    options.append(label)
    label_to_item[label] = m

st.markdown('<div class="tp-section-title">검침 대상 선택</div>', unsafe_allow_html=True)

if not options:
    st.success("🎉 모든 계량기의 검침이 완료되었습니다!")
    st.stop()

selected_label = st.selectbox("검침할 계량기를 선택하세요", options, label_visibility="collapsed")
curr_data = label_to_item[selected_label]
is_curr_done = (curr_data["curr_val"] is not None)

if is_curr_done:
    diff_recorded = int(round(curr_data["curr_val"] - curr_data["prev_val"]))
    usage_recorded = int(round(diff_recorded * curr_data["ct_ratio"]))
    st.markdown(f"""
    <div class="tp-done-box">
        ✅ <b>이미 구글 시트에 기록된 항목입니다.</b><br>
        입력된 당월지침: <b>{int(curr_data['curr_val']):,d}</b> │ 사용량: <b>{usage_recorded:,d} kWh</b>
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="tp-info-box">
    <b>입주사:</b> {curr_data['company']} &nbsp;│&nbsp; <b>계량기:</b> {curr_data['meter']}<br>
    <b>전월 지침:</b> {int(curr_data['prev_val']):,d} kWh &nbsp;│&nbsp; <b>적용 배율:</b> ×{int(curr_data['ct_ratio']) if curr_data['ct_ratio'].is_integer() else curr_data['ct_ratio']}
</div>
""", unsafe_allow_html=True)

# ----------------------------------------------------
# 7. 당월 지침 입력 & 자동 계산 (정수형 + 공동배분 안내)
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

# 💡 공동 간판일 경우 실시간 N등분 배분 안내 카드 표시
if "썬큰간판" in curr_data["meter"]:
    split_2 = round(actual_usage / 2, 1)
    st.info(f"""
    📢 **[공동 간판 배분 계산기 (1/2 배분)]**
    * 총 검침 사용량: **{actual_usage:,} kWh**
    * 업체별 부과량 (**플렉스 볼링센터 / 플렉스 골프라운지** 각 50%): **{split_2:,.1f} kWh**
    """)
elif "지주식" in curr_data["meter"]:
    split_5 = round(actual_usage / 5, 1)
    st.info(f"""
    📢 **[공동 간판 배분 계산기 (1/5 균등 배분)]**
    * 총 검침 사용량: **{actual_usage:,} kWh**
    * 업체별 부과량 (**한의원 / 치과 / 꽃방 / 볼링 / 웨딩** 각 20%): **{split_5:,.1f} kWh**
    """)

# ----------------------------------------------------
# 8. 구글 시트 저장
# ----------------------------------------------------
if st.button("💾 검침 데이터 저장 및 시트 전송", use_container_width=True):
    with st.spinner("구글 시트에 실시간 기록 중..."):
        row = curr_data["row_idx"]
        # E열(5): 당월지침, F열(6): 차이, G열(7): 사용량
        sheet.update_cell(row, 5, input_val)
        sheet.update_cell(row, 6, diff)
        sheet.update_cell(row, 7, actual_usage)
        
        st.success(f"🎉 [{curr_data['company']} - {curr_data['meter']}] 구글 시트에 정상 반영되었습니다!")
        st.balloons()
        st.rerun()
