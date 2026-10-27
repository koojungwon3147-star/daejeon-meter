import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# ----------------------------------------------------
# 1. 화면 스타일 (다크/라이트 대응 & 슬림 테마)
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
    font-size: 13px;
    font-weight: 600;
    border-radius: 6px 6px 0 0;
}

/* 타이틀 헤더 */
.tp-header {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #E2E8F0;
    border-bottom: 3px solid #1B75BC !important;
    padding: 16px 18px 14px 18px;
    margin-bottom: 18px;
    border-radius: 0 0 6px 6px;
}
.tp-header-title {
    font-size: 20px;
    font-weight: 700;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.tp-header-title span {
    color: #1B75BC !important;
}

/* 계량기 상세 안내 박스 */
.tp-info-box {
    background: rgba(27, 117, 188, 0.08);
    border: 1px solid rgba(27, 117, 188, 0.3);
    border-radius: 8px;
    padding: 14px 16px;
    margin-bottom: 15px;
    font-size: 15px;
    line-height: 1.7;
}

/* 완료 안내 박스 */
.tp-done-box {
    background: rgba(46, 125, 50, 0.12);
    border: 1px solid rgba(76, 175, 80, 0.4);
    border-radius: 8px;
    padding: 12px 14px;
    margin-bottom: 15px;
    font-size: 14px;
    font-weight: 600;
    color: #4CAF50 !important;
}

/* 소제목 타이틀 */
.tp-section-title {
    font-size: 16px;
    font-weight: 700;
    color: #4DA3FF !important;
    border-left: 4px solid #1B75BC;
    padding-left: 10px;
    margin: 22px 0 12px 0;
}

/* 드롭다운 & 입력창 */
div[data-baseweb="select"] * {
    font-size: 15px !important;
}
div[data-baseweb="input"] input {
    font-size: 20px !important;
    font-weight: 700 !important;
    height: 46px !important;
}

/* 새로고침 미니 버튼 */
.mini-btn button {
    height: 32px !important;
    min-height: 32px !important;
    padding: 0px 14px !important;
    background-color: #1B75BC !important;
    color: #FFFFFF !important;
    border: none !important;
    border-radius: 4px !important;
    white-space: nowrap !important;
    margin-top: 0px !important;
}
.mini-btn button p {
    font-size: 13px !important;
    font-weight: 600 !important;
    color: #FFFFFF !important;
    line-height: 32px !important;
}

/* 하단 검침 저장 버튼 */
.save-btn > button {
    background-color: #1B75BC !important;
    color: #FFFFFF !important;
    font-size: 17px !important;
    font-weight: 700 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 14px 0 !important;
    margin-top: 18px !important;
    box-shadow: 0 4px 6px rgba(27, 117, 188, 0.2) !important;
}
.save-btn > button p {
    color: #FFFFFF !important;
    font-size: 17px !important;
    font-weight: 700 !important;
}

/* 위치 태그 뱃지 */
.location-badge {
    background-color: #E2E8F0;
    color: #1A202C;
    padding: 3px 8px;
    border-radius: 4px;
    font-size: 13px;
    font-weight: 600;
}

/* 계량기 번호 뱃지 */
.meter-no-badge {
    background-color: #1B75BC;
    color: #FFFFFF;
    padding: 2px 7px;
    border-radius: 4px;
    font-size: 12px;
    font-weight: 700;
    margin-right: 6px;
}
</style>

<div class="tp-top-bar">티피에스 주식회사 | 대전회관</div>
<div class="tp-header">
    <div class="tp-header-title">⚡ <span>대전회관</span> 전기계량기 검침 대장</div>
</div>
"""
st.markdown(tp_custom_css, unsafe_allow_html=True)

# ----------------------------------------------------
# 2. 위치표 이미지 기반 절대적 순서(Order) 및 번호 매핑
# ----------------------------------------------------
def get_meter_info(company, meter):
    c = company.replace(" ", "")
    m = meter.replace(" ", "")
    
    # 💡 1F 방재센터 원격검침 대상 (목록에서 완벽 제외하기 위한 플래그)
    is_remote = False
    if "보안관리단" in c or "시설관리단" in c or "메리츠" in c:
        is_remote = True
    elif "아이피" in c or "와이즈넛" in c or "방송통신" in c:
        is_remote = True
    elif "부동산원" in c and ("6F" in c or "6층" in c or "9F" in c or "9층" in c or "에어컨" in m) and ("18F" not in c and "18층" not in c):
        is_remote = True
    elif "F&U" in c and ("EHP" in m or "4,5층" in m or "시스템" not in m):
        is_remote = True
    elif "A+에셋" in c and ("9F" in c or "9층" in c) and "실외기" not in m and "남측" not in m and "8F" not in c:
        is_remote = True

    if is_remote:
        return None  # 원격검침은 아예 제외 처리

    # --- [위치표 이미지 상단 -> 하단, 좌 -> 우 엄격 순서] ---
    
    # 1. PH1
    if ("코웨이" in c or "이안" in c) or ("19F" in m and "실외기" in m):
        return {"location": "🏢 PH1 (옥상)", "no": "No.5", "order": 1}
    if ("A+에셋" in c or "에셋" in c) and ("12F" in m or "12층" in m) and "실외기" in m:
        return {"location": "🏢 PH1 (옥상)", "no": "No.9", "order": 2}
    if ("A+에셋" in c or "에셋" in c) and ("15F" in m or "15층" in m) and "실외기" in m:
        return {"location": "🏢 PH1 (옥상)", "no": "No.53", "order": 3}
    if ("A+에셋" in c or "에셋" in c) and ("18F" in m or "18층" in m) and "실외기" in m:
        return {"location": "🏢 PH1 (옥상)", "no": "No.60", "order": 4}

    # 2. 20F EPS, 컨택센터
    if "컨택센터UPS" in m or ("컨택" in c and "UPS" in m):
        return {"location": "📍 20F EPS실", "no": "No.1", "order": 5}
    if "컨텍센터EHP" in m or "컨택센터EHP" in m or ("컨택" in c and "EHP" in m):
        return {"location": "📍 20F EPS실", "no": "No.2", "order": 6}
    if "신한카드채권" in c or ("신한카드" in c and ("PAC" in m or "채권" in c)):
        return {"location": "📍 20F EPS실", "no": "No.54", "order": 7}
    if "KB라이프" in c:
        return {"location": "📍 20F EPS실", "no": "No.55", "order": 8}
    if "ABL생명" in c:
        return {"location": "📍 20F EPS실", "no": "No.56", "order": 9}

    # 3. 19F EPS
    if "근로복지공단" in c and ("19F" in c or "19층" in c):
        return {"location": "📍 19F EPS실", "no": "No.4", "order": 10}
    if "프레제니우스" in c or "FMCK" in c:
        return {"location": "📍 19F EPS실", "no": "No.6", "order": 11}

    # 4. 15F EPS
    if "근로복지공단" in c and ("11층" in m or "11F" in m):
        return {"location": "📍 15F EPS실", "no": "No.11", "order": 12}
    if "한국부동산원" in c and ("18F" in c or "18층" in c):
        return {"location": "📍 15F EPS실", "no": "No.52", "order": 13}

    # 5. 14F EPS
    if "신한카드" in c and ("14F" in c or "14층" in c):
        return {"location": "📍 14F EPS실", "no": "No.7", "order": 14}

    # 6. 13F EPS
    if "시마즈" in c:
        return {"location": "📍 13F EPS실", "no": "No.56", "order": 15}

    # 7. 7F EPS
    if "오티스" in c or "OTIS" in c:
        return {"location": "📍 7F EPS실", "no": "No.16", "order": 16}

    # 8. 6F EPS
    if "법률사무소" in c and "PAC" in m:
        if "12" in m or "1" in m:
            return {"location": "📍 6F EPS실", "no": "No.12", "order": 17}
        return {"location": "📍 6F EPS실", "no": "No.13", "order": 18}
    if ("A+에셋" in c or "에셋" in c) and ("8F" in c or "8층" in c):
        return {"location": "📍 6F EPS실", "no": "No.15", "order": 19}

    # 9. 5층 옥상 (10, 17, 39, 46, 23, 28, 37, 14, KODATA)
    if ("A+에셋" in c or "에셋" in c) and ("남측" in c or "남측" in m or "돌출간판" in m or "10" in m):
        return {"location": "🌳 5층 옥상", "no": "No.10", "order": 20}
    if "생산성본부" in c or "17" in m:
        return {"location": "🌳 5층 옥상", "no": "No.17", "order": 21}
    if "볼링" in c and "서측" in m:
        return {"location": "🌳 5층 옥상", "no": "No.39", "order": 22}
    if "골프" in c and "서측" in m:
        return {"location": "🌳 5층 옥상", "no": "No.46", "order": 23}
    if "알티오라" in c and "서측" in m:
        return {"location": "🌳 5층 옥상", "no": "No.23", "order": 24}
    if "한의원" in c and "간판" in m:
        return {"location": "🌳 5층 옥상", "no": "No.28", "order": 25}
    if "청사치과" in c and "서측" in m:
        return {"location": "🌳 5층 옥상", "no": "No.37", "order": 26}
    if "법률사무소" in c and "돌출간판" in m:
        return {"location": "🌳 5층 옥상", "no": "No.14", "order": 27}
    if "KODATA" in c or "코데이터" in c or "한국평가데이터" in c:
        return {"location": "🌳 5층 옥상", "no": "", "order": 28} # KODATA 번호 없음 요청 반영

    # 10. 4F 라이나생명 내부
    if "라이나생명" in c:
        return {"location": "📍 4F 라이나생명 내부", "no": "No.18", "order": 29}

    # 11. 4F EPS
    if "F&U" in c and "시스템" in m:
        return {"location": "📍 4F EPS실", "no": "No.59", "order": 30}

    # 12. 3F EPS
    if "계산" in m and "정산" in m:
        return {"location": "📍 3F EPS실", "no": "No.19", "order": 31}

    # 13. 3F 음향실
    if "음향실" in m or ("웨딩" in m and "3층" in m):
        return {"location": "📍 3F 음향실", "no": "No.26", "order": 32}

    # 14. 2F EPS
    if "빌라드" in c and "동측" in m:
        return {"location": "📍 2F EPS실", "no": "No.22", "order": 33}
    if "웨딩예약실" in m:
        return {"location": "📍 2F EPS실", "no": "No.25", "order": 34}

    # 15. 2F 한의원 내 분전반
    if "한의원" in c and "일반전열" in m:
        return {"location": "📍 2F 한의원 내부 분전반", "no": "No.29", "order": 35}

    # 16. 1F EPS
    if "동문꽃방" in c:
        return {"location": "📍 1F EPS실", "no": "No.36", "order": 36}

    # 17. 1F 고반식당
    if "고반식당" in c:
        if "일반전열" in m or "32" in m:
            return {"location": "📍 1F 고반식당", "no": "No.32", "order": 37}
        if "비상전열" in m or "33" in m:
            return {"location": "📍 1F 고반식당", "no": "No.33", "order": 38}
        return {"location": "📍 1F 고반식당", "no": "No.34", "order": 39}

    # 18. 1F 해이커피
    if "해이커피" in c:
        return {"location": "📍 1F 해이커피", "no": "No.57", "order": 40}

    # 19. 1F 현대캐피탈
    if "현대캐피탈" in c:
        return {"location": "📍 1F 현대캐피탈", "no": "No.58", "order": 41}

    # 20. 1F 지주식 입간판
    if "지주식" in m or "49" in m:
        return {"location": "🌳 1F 정문 화단", "no": "No.49", "order": 42}

    # 21. 1F 후문 화단
    if "썬큰간판" in m or "48" in m:
        return {"location": "🌳 1F 후문 화단", "no": "No.48", "order": 43}

    # 22. B1F 골프장
    if "골프장" in m and "동력" in m:
        return {"location": "⛳ B1F 플렉스 골프라운지", "no": "No.47", "order": 44}
    if "골프장" in m and "에어컨-1" in m:
        return {"location": "⛳ B1F 플렉스 골프라운지", "no": "No.50", "order": 45}
    if "골프장" in m and "에어컨-2" in m:
        return {"location": "⛳ B1F 플렉스 골프라운지", "no": "No.51", "order": 46}

    # 23. B1F 볼링장
    if "볼링" in c and "일반전열" in m:
        return {"location": " bowling B1F 플렉스 볼링센터", "no": "No.43", "order": 47}

    # 24. B1F EPS
    if "후문계단" in m or "2F홀" in m:
        return {"location": "📍 B1F EPS실", "no": "No.24", "order": 48}
    if "볼링" in c and "에어컨3" in m:
        return {"location": "📍 B1F EPS실", "no": "No.42", "order": 49}

    # 25. B4F 상부 EPS
    if "냉동기" in m:
        return {"location": "📍 B4F 상부 EPS실", "no": "No.27", "order": 50}

    # 26. B5F 수변전실
    if "주방동력1" in m:
        return {"location": "⚡ B5F 수변전실", "no": "No.21", "order": 51}
    if "주방동력2" in m:
        return {"location": "⚡ B5F 수변전실", "no": "No.20", "order": 52}
    if "볼링" in c and "동력" in m:
        return {"location": "⚡ B5F 수변전실", "no": "No.38", "order": 53}
    if "볼링" in c and "에어컨1" in m:
        return {"location": "⚡ B5F 수변전실", "no": "No.40", "order": 54}
    if "볼링" in c and "에어컨2" in m:
        return {"location": "⚡ B5F 수변전실", "no": "No.41", "order": 55}
        
    return {"location": "📍 현장 분전반", "no": "", "order": 999}

# ----------------------------------------------------
# 3. 구글 시트 연결
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
# 4. 실시간 탭(월) 로드
# ----------------------------------------------------
worksheet_list = [ws.title for ws in doc.worksheets()]
default_tab_index = 0
for idx, title in enumerate(worksheet_list):
    if "9월" in title or "2026년 9월" in title or "2026년9월" in title:
        default_tab_index = idx
        break

selected_month = st.selectbox("검침 대상 월 (시트 탭 선택)", worksheet_list, index=default_tab_index)
sheet = doc.worksheet(selected_month)

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
seen_keys = set()

for row_idx, row in enumerate(all_rows[1:], start=2):
    if not row or not row[col_company].strip():
        continue
    
    company = row[col_company].strip()
    meter_name = row[col_meter].strip() if len(row) > col_meter else "계량기"
    
    if "합계" in company or "총합계" in company:
        continue
        
    is_virtual_split = (
        ("광고입간판" in meter_name and "1F 지주식" not in meter_name and "정문" not in meter_name) or
        ("썬큰간판" in meter_name and "후문" not in meter_name and "볼링/골프" not in company)
    )
    if is_virtual_split:
        continue

    unique_key = f"{company}_{meter_name}"
    if unique_key in seen_keys:
        continue
    seen_keys.add(unique_key)
        
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

    info = get_meter_info(company, meter_name)
    if info is None:
        continue  # 원격검침 항목은 완전히 제외

    meters_data.append({
        "row_idx": row_idx,
        "company": company,
        "meter": meter_name,
        "location": info["location"],
        "meter_no": info["no"],
        "order": info["order"],
        "ct_ratio": ct_ratio,
        "prev_val": prev_val,
        "curr_val": curr_val
    })

# 💡 [핵심] 이미지 표 기준 순서 1번부터 완전히 오름차순 정렬
meters_data.sort(key=lambda x: x["order"])

total_count = len(meters_data)

# ----------------------------------------------------
# 5. 진행 현황 & 미니 새로고침
# ----------------------------------------------------
progress_ratio = completed_count / total_count if total_count > 0 else 0
st.markdown(f"**검침 진행 현황:** **{completed_count}** / {total_count}개 완료 ({int(progress_ratio*100)}%)")
st.progress(progress_ratio)

col_filter1, col_filter2 = st.columns([3.0, 1.0])
with col_filter1:
    only_uncompleted = st.checkbox("미검침 계량기만 보기", value=False)
with col_filter2:
    st.markdown('<div class="mini-btn">', unsafe_allow_html=True)
    if st.button("새로고침", use_container_width=True):
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------------------------------
# 6. 검침 대상 선택 (이미지 위치표 동선 100% 매칭)
# ----------------------------------------------------
options = []
label_to_item = {}

for m in meters_data:
    is_done = (m["curr_val"] is not None)
    if only_uncompleted and is_done:
        continue
    
    tag = "✅ [완료]" if is_done else "⬜ [대기]"
    no_str = f"[{m['meter_no']}] " if m['meter_no'] else ""
    label = f"{tag} {no_str}[{m['company']}] {m['meter']}"
    options.append(label)
    label_to_item[label] = m

st.markdown('<div class="tp-section-title">검침 대상 선택</div>', unsafe_allow_html=True)

if not options:
    st.success("모든 계량기의 검침이 완료되었습니다.")
    st.stop()

if 'selected_idx' not in st.session_state or st.session_state.selected_idx >= len(options):
    st.session_state.selected_idx = 0

selected_label = st.selectbox("검침 계량기 선택", options, index=st.session_state.selected_idx, label_visibility="collapsed")
curr_data = label_to_item[selected_label]
is_curr_done = (curr_data["curr_val"] is not None)

if is_curr_done:
    diff_recorded = int(round(curr_data["curr_val"] - curr_data["prev_val"]))
    usage_recorded = int(round(diff_recorded * curr_data["ct_ratio"]))
    st.markdown(f"""
    <div class="tp-done-box">
        기록 완료 (당월지침: <b>{int(curr_data['curr_val']):,d}</b> │ 사용량: <b>{usage_recorded:,d} kWh</b>)
    </div>
    """, unsafe_allow_html=True)

no_badge = f'<span class="meter-no-badge">{curr_data["meter_no"]}</span>' if curr_data["meter_no"] else ""
st.markdown(f"""
<div class="tp-info-box">
    <b>검침 위치:</b> <span class="location-badge">{curr_data['location']}</span><br>
    <b>입주사:</b> {curr_data['company']} &nbsp;|&nbsp; <b>계량기:</b> {no_badge}{curr_data['meter']}<br>
    <b>전월 지침:</b> {int(curr_data['prev_val']):,d} kWh &nbsp;|&nbsp; <b>적용 배율:</b> ×{int(curr_data['ct_ratio']) if curr_data['ct_ratio'].is_integer() else curr_data['ct_ratio']}
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
    st.error("당월 지침이 전월 지침보다 작습니다. 오입력을 확인하세요.")

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
# 8. 검침 데이터 저장
# ----------------------------------------------------
st.markdown('<div class="save-btn">', unsafe_allow_html=True)
if st.button("검침 데이터 저장", use_container_width=True):
    with st.spinner("구글 시트에 실시간 기록 중..."):
        row = curr_data["row_idx"]
        
        if col_curr != -1:
            sheet.update_cell(row, col_curr + 1, input_val)
        if col_diff != -1:
            sheet.update_cell(row, col_diff + 1, diff)
        if col_usage != -1:
            sheet.update_cell(row, col_usage + 1, actual_usage)
            
        st.toast(f"[{curr_data['company']}] 저장 완료!", icon="💾")
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)
