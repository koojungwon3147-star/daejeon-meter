import streamlit as st
import gspread
import re, math, base64, unicodedata
from datetime import datetime, timezone, timedelta
from html import escape
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


route_table_slot = st.container()

SPREADSHEET_ID = "1GuRaE9GASUYYynraKB4zMhnyW8swaXMqBEoykyIp_CU"
ROUTE = {1: {'location': 'PH1 (옥상)', 'no': 'No.5', 'order': 1}, 2: {'location': 'PH1 (옥상)', 'no': 'No.9', 'order': 2}, 3: {'location': 'PH1 (옥상)', 'no': 'No.53', 'order': 3}, 4: {'location': 'PH1 (옥상)', 'no': 'No.60', 'order': 4}, 5: {'location': '20F EPS실', 'no': 'No.1', 'order': 5}, 6: {'location': '20F EPS실', 'no': 'No.2', 'order': 6}, 7: {'location': '20F EPS실', 'no': 'No.54', 'order': 7}, 8: {'location': '20F EPS실', 'no': 'No.55', 'order': 8}, 9: {'location': '20F EPS실', 'no': 'No.56', 'order': 9}, 10: {'location': '19F EPS실', 'no': 'No.4', 'order': 10}, 11: {'location': '19F EPS실', 'no': 'No.6', 'order': 11}, 12: {'location': '15F EPS실', 'no': 'No.11', 'order': 12}, 13: {'location': '15F EPS실', 'no': 'No.52', 'order': 13}, 14: {'location': '14F EPS실', 'no': 'No.7', 'order': 14}, 15: {'location': '13F EPS실', 'no': 'No.56', 'order': 15}, 16: {'location': '7F EPS실', 'no': 'No.16', 'order': 16}, 17: {'location': '6F EPS실', 'no': 'No.12', 'order': 17}, 18: {'location': '6F EPS실', 'no': 'No.13', 'order': 18}, 19: {'location': '6F EPS실', 'no': 'No.15', 'order': 19}, 20: {'location': '5층 옥상', 'no': 'No.10', 'order': 20}, 21: {'location': '5층 옥상', 'no': 'No.17', 'order': 21}, 22: {'location': '5층 옥상', 'no': 'No.39', 'order': 22}, 23: {'location': '5층 옥상', 'no': 'No.46', 'order': 23}, 24: {'location': '5층 옥상', 'no': 'No.23', 'order': 24}, 25: {'location': '5층 옥상', 'no': 'No.28', 'order': 25}, 26: {'location': '5층 옥상', 'no': 'No.37', 'order': 26}, 27: {'location': '5층 옥상', 'no': 'No.14', 'order': 27}, 28: {'location': '5층 옥상', 'no': '', 'order': 28}, 29: {'location': '4F 라이나생명 내부', 'no': 'No.18', 'order': 29}, 30: {'location': '4F EPS실', 'no': 'No.59', 'order': 30}, 31: {'location': '3F EPS실', 'no': 'No.19', 'order': 31}, 32: {'location': '3F 음향실', 'no': 'No.26', 'order': 32}, 33: {'location': '2F EPS실', 'no': 'No.22', 'order': 33}, 34: {'location': '2F EPS실', 'no': 'No.25', 'order': 34}, 35: {'location': '2F 한의원 내부 분전반', 'no': 'No.29', 'order': 35}, 36: {'location': '1F EPS실', 'no': 'No.36', 'order': 36}, 37: {'location': '1F 고반식당', 'no': 'No.32', 'order': 37}, 38: {'location': '1F 고반식당', 'no': 'No.33', 'order': 38}, 39: {'location': '1F 고반식당', 'no': 'No.34', 'order': 39}, 40: {'location': '1F 해이커피', 'no': 'No.57', 'order': 40}, 41: {'location': '1F 현대캐피탈', 'no': 'No.58', 'order': 41}, 42: {'location': '1F 정문 화단', 'no': 'No.49', 'order': 42}, 43: {'location': '1F 후문 화단', 'no': 'No.48', 'order': 43}, 44: {'location': 'B1F 플렉스 골프라운지', 'no': 'No.47', 'order': 44}, 45: {'location': 'B1F 플렉스 골프라운지', 'no': 'No.50', 'order': 45}, 46: {'location': 'B1F 플렉스 골프라운지', 'no': 'No.51', 'order': 46}, 47: {'location': 'B1F 플렉스 볼링센터', 'no': 'No.43', 'order': 47}, 48: {'location': 'B1F EPS실', 'no': 'No.24', 'order': 48}, 49: {'location': 'B1F EPS실', 'no': 'No.42', 'order': 49}, 50: {'location': 'B4F 상부 EPS실', 'no': 'No.27', 'order': 50}, 51: {'location': 'B5F 수변전실', 'no': 'No.21', 'order': 51}, 52: {'location': 'B5F 수변전실', 'no': 'No.20', 'order': 52}, 53: {'location': 'B5F 수변전실', 'no': 'No.38', 'order': 53}, 54: {'location': 'B5F 수변전실', 'no': 'No.40', 'order': 54}, 55: {'location': 'B5F 수변전실', 'no': 'No.41', 'order': 55}}
MAPPING = {('19F이연', '에어컨'): 1, ('12FA+에셋', '12층실외기'): 2, ('15FA+에셋', 'PAC에어컨'): 3, ('18FA+에셋', 'PAC에어컨'): 4, ('20F티피에스(주)', '컨택센터UPS'): 5, ('20F티피에스(주)', '컨택센터EHP'): 6, ('20F신한카드채권관리팀', 'EHP'): 7, ('20FKB라이프', 'EHP'): 8, ('20FABL생명', 'EHP'): 9, ('19F근로복지공단', '19FPAC에어컨'): 10, ('19F프레제니우스메디칼케어', 'EHP'): 11, ('11F근로복지공단', '11층EHP'): 12, ('18F한국부동산원', '에어컨'): 13, ('14F신한카드', 'EHP'): 14, ('13F시마즈사이언티픽코리아', 'EHP'): 15, ('7FOTIS', 'PAC에어컨'): 16, ('10F법률사무소', 'PAC에어컨1'): 17, ('10F법률사무소', 'PAC에어컨2'): 18, ('8FA+에셋', '에어컨'): 19, ('12FA+에셋', '남측돌출간판'): 20, ('5FKPC한국생산성본부', '돌출간판'): 21, ('플렉스볼링센터', '서측벽간판'): 22, ('플렉스골프라운지', '서측벽간판'): 23, ('(주)빌라드알티오라', '서측벽간판'): 24, ('박기섭한의원', '돌출간판,서측벽간판'): 25, ('청사치과', '서측벽간판'): 26, ('10F법률사무소', '돌출간판'): 27, ('9FKODATA', '에어컨'): 28, ('4F라이나생명', '사무실EHP'): 29, ('4FF&U', '시스템실'): 30, ('(주)빌라드알티오라', '3F계산및정산실'): 31, ('(주)빌라드알티오라', '웨딩홀PAC(3층음향실)'): 32, ('(주)빌라드알티오라', '3층(동측에어컨)'): 33, ('(주)빌라드알티오라', '웨딩예약실PAC(2층EPS실)'): 34, ('박기섭한의원', '일반전열'): 35, ('동문꽃방', '쇼케이스냉장고'): 36, ('고반식당', '일반전열'): 37, ('고반식당', '비상전열'): 38, ('고반식당', '에어컨'): 39, ('해이커피', '일반전열'): 40, ('현대캐피탈', 'EHP'): 41, ('(한의원/치과/꽃방/볼링/웨딩)', '1F지주식광고입간판'): 42, ('(볼링/골프)', '썬큰간판(1F후문화단)'): 43, ('플렉스골프라운지', '골프장동력(하단)'): 44, ('플렉스골프라운지', '골프장에어컨-1(상)'): 45, ('플렉스골프라운지', '골프장에어컨-2(하)'): 46, ('플렉스볼링센터', '일반전열'): 47, ('(주)빌라드알티오라', '2층후문계단쪽PAC(B1층EPS실)'): 48, ('플렉스볼링센터', '천정형에어컨3'): 49, ('(주)빌라드알티오라', 'B4층냉동기'): 50, ('(주)빌라드알티오라', '주방동력1'): 51, ('(주)빌라드알티오라', '주방동력2'): 52, ('플렉스볼링센터', '볼링장동력'): 53, ('플렉스볼링센터', '천정형에어컨1'): 54, ('플렉스볼링센터', '천정형에어컨2'): 55}
EXCLUDED = {('플렉스골프라운지', '썬큰간판'), ('플렉스볼링센터', '썬큰간판'), ('박기섭한의원', '광고입간판'), ('플렉스볼링센터', '광고입간판'), ('동문꽃방', '광고입간판'), ('9FA+에셋(남측)', 'EHP'), ('12F노무법인태양', 'EHP'), ('19F과학기술보안관리단', 'EHP'), ('11F아이피앤텍플러스', 'EHP'), ('4FF&U', 'EHP'), ('4F방송통신심의위원회', 'PAC에어컨'), ('13F메리츠캐피탈', 'PAC에어컨'), ('청사치과', '광고입간판'), ('13F과학기술시설관리단', 'EHP'), ('9FA+에셋(서측)', 'EHP'), ('(주)빌라드알티오라', '광고입간판'), ('6F한국부동산원', '에어컨')}
def normalize(value):
    return re.sub(r"\s+", "", unicodedata.normalize("NFKC", str(value or ""))).upper()

def identity(company, meter):
    return (normalize(company), normalize(meter))

def cell(row, index):
    return str(row[index]).strip() if index < len(row) and row[index] is not None else ""

def numeric(value, label, optional=False):
    value = str(value or "").replace(",", "").strip()
    if not value and optional:
        return None
    try:
        number = float(value)
        if not math.isfinite(number):
            raise ValueError()
        return number
    except ValueError:
        raise ValueError(f"{label} 값이 숫자가 아닙니다: {value or '(빈칸)'}")

def read_main_rows(rows):
    # The workbook has a second header/total block at row 74 and allocation rows
    # at 77-83. Stop at that boundary; never include or write the allocation block.
    headers = {normalize(value): i for i, value in enumerate(rows[0])}
    required = ('입주사명', '계량기명', '전월지침', '당월지침', '배율', '지침차', '사용량')
    if not all(name in headers for name in required):
        raise ValueError('첫 행에 입주사명·계량기명·전월지침·당월지침·배율·지침차·사용량 열이 필요합니다.')
    result = []
    for row_no, row in enumerate(rows[1:], 2):
        company, meter = cell(row, headers['입주사명']), cell(row, headers['계량기명'])
        if not company:
            if cell(row, headers['전월지침']) in ('전월지침', '전출지침'):
                break
            continue
        if '합계' in company:
            break
        result.append((row_no, company, meter, row))
    return headers, result

def prepare_meters(rows):
    columns, main = read_main_rows(rows)
    meters, unknown, excluded = [], [], []
    for row_no, company, meter, raw in main:
        key = identity(company, meter)
        if key in EXCLUDED:
            excluded.append(row_no)
            continue
        order = MAPPING.get(key)
        if order is None:
            unknown.append({'시트 행': row_no, '입주사': company, '계량기': meter})
            continue
        item = dict(ROUTE[order], row_idx=row_no, company=company, meter=meter,
                    identity=key, raw=list(raw), error=None)
        try:
            item['prev_val'] = numeric(cell(raw, columns['전월지침']), '전월지침')
            item['curr_val'] = numeric(cell(raw, columns['당월지침']), '당월지침', optional=True)
            item['ratio'] = numeric(cell(raw, columns['배율']), '배율')
            if item['ratio'] <= 0:
                raise ValueError('배율은 0보다 커야 합니다.')
        except ValueError as error:
            item['error'] = str(error)
        meters.append(item)
    meters.sort(key=lambda item: (item['order'], item['row_idx']))
    return columns, meters, unknown, excluded

def plan_save(old_rows, fresh_rows, formula_rows, target, value):
    columns, main = read_main_rows(fresh_rows)
    old_columns, _ = read_main_rows(old_rows)
    if columns != old_columns:
        raise ValueError('시트 열 구성이 변경되었습니다. 새로고침 후 다시 입력하세요.')
    matches = [(n, row) for n, company, meter, row in main
               if identity(company, meter) == target['identity']]
    if len(matches) != 1:
        raise ValueError('본문에 같은 입주사명·계량기명이 없거나 중복됩니다. 시트를 확인하세요.')
    row_no, row = matches[0]
    for field in ('전월지침', '당월지침', '배율'):
        index = columns[field]
        if cell(row, index) != cell(target['raw'], index):
            raise ValueError('다른 곳에서 검침 데이터가 변경되었습니다. 새로고침 후 다시 입력하세요.')
    _, formula_main = read_main_rows(formula_rows)
    formula_match = [(n, raw) for n, c, m, raw in formula_main if identity(c, m) == target['identity']]
    if len(formula_match) != 1 or formula_match[0][0] != row_no:
        raise ValueError('확인 중 시트 행이 변경되었습니다. 새로고침 후 다시 입력하세요.')
    formulas = formula_match[0][1]
    if cell(formulas, columns['당월지침']).startswith('='):
        raise ValueError('당월지침 칸에 수식이 있습니다. 자동계산 행에는 직접 저장하지 않습니다.')
    previous = numeric(cell(row, columns['전월지침']), '전월지침')
    ratio = numeric(cell(row, columns['배율']), '배율')
    if not math.isfinite(value) or value < previous or ratio <= 0:
        raise ValueError('당월지침과 배율을 확인하세요.')
    difference = value - previous
    updates = [(row_no, columns['당월지침'] + 1, value)]
    # Existing E/G formulas remain intact. If a legacy version replaced one with
    # a constant, update that numeric output to avoid leaving stale usage behind.
    for field, result in (('지침차', difference), ('사용량', difference * ratio)):
        if not cell(formulas, columns[field]).startswith('='):
            updates.append((row_no, columns[field] + 1, result))
    return updates

@st.cache_resource
def connect_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    secret = dict(st.secrets['gcp_service_account'])
    secret['private_key'] = secret['private_key'].replace('\\n', '\n')
    credentials = ServiceAccountCredentials.from_json_keyfile_dict(secret, scope)
    return gspread.authorize(credentials).open_by_key(SPREADSHEET_ID)

@st.cache_resource(ttl=300)
def worksheets_by_title():
    return {ws.title: ws for ws in connect_sheet().worksheets()}

@st.cache_data(ttl=60, show_spinner=False)
def load_month_rows(title):
    return worksheets_by_title()[title].get_all_values()

def is_quota_error(error):
    return getattr(getattr(error, 'response', None), 'status_code', None) == 429 or '429' in str(error)

def show_quota_message():
    st.error('구글시트의 분당 요청 한도에 도달했습니다. 약 1분 뒤 다시 시도하세요. 입력한 값은 현재 화면에 유지됩니다.')
    st.session_state['quota_until'] = datetime.now(timezone.utc).timestamp() + 60

remaining = st.session_state.get('quota_until', 0) - datetime.now(timezone.utc).timestamp()
if remaining > 0:
    st.warning(f'구글시트 요청 한도 회복 대기 중입니다. 약 {int(remaining)+1}초 뒤 다시 시도하세요.')
    if st.button('다시 연결'):
        st.rerun()
    st.stop()

try:
    worksheets = worksheets_by_title()
    months = [title for title in worksheets if re.search(r'\d{4}년\s*\d{1,2}월', title)]
    if not months:
        st.error('월별 시트 탭을 찾지 못했습니다.')
        st.stop()
    def month_key(title):
        match = re.search(r'(\d{4})년\s*(\d{1,2})월', title)
        return tuple(map(int, match.groups()))
    months.sort(key=month_key)
    now = datetime.now(timezone(timedelta(hours=9)))
    default = next((i for i, title in enumerate(months) if month_key(title) == (now.year, now.month)), len(months)-1)
    selected_month = st.selectbox('검침 대상 월 (시트 탭 선택)', months, index=default)
    sheet = worksheets[selected_month]
    all_rows = load_month_rows(selected_month)
    columns, meters, unknown, excluded = prepare_meters(all_rows)
except Exception as error:
    if is_quota_error(error):
        show_quota_message()
    else:
        st.error(f'시트를 불러오지 못했습니다: {error}')
    if st.button('다시 연결'):
        st.rerun()
    st.stop()

notice = st.session_state.pop('saved_notice', None)
if notice:
    st.success(notice)
completed = sum(m.get('curr_val') is not None and not m['error'] for m in meters)
st.markdown(f'**검침 진행 현황: {completed} / {len(meters)}개 완료**')
st.progress(completed / len(meters) if meters else 0.0)
left, right = st.columns([3, 1])
with left:
    only_pending = st.checkbox('미검침 계량기만 보기')
with right:
    if st.button('새로고침', use_container_width=True):
        now_seconds = datetime.now(timezone.utc).timestamp()
        if now_seconds - st.session_state.get('last_refresh', 0) < 15:
            st.info('새로고침은 15초 간격으로 할 수 있습니다.')
        else:
            st.session_state['last_refresh'] = now_seconds
            load_month_rows.clear(selected_month)
            worksheets_by_title.clear()
            for key in list(st.session_state):
                if key.startswith('reading_'):
                    del st.session_state[key]
            st.rerun()
st.caption('조회 결과는 최대 1분간 재사용합니다. 저장 시 최신 시트를 다시 확인합니다.')
if unknown:
    st.warning('순서표와 연결되지 않은 새 항목이 있습니다. 아래 목록을 확인하세요.')
    st.dataframe(unknown, hide_index=True)
missing = sorted(set(ROUTE) - {m['order'] for m in meters})
if missing:
    st.warning('시트에서 찾지 못한 PDF 순서: ' + ', '.join(str(x) for x in missing))
with route_table_slot.expander('계량기 검침 위치 및 순서표 보기', expanded=False):
    st.caption('화면 순서는 PDF 기준입니다. 저장은 입주사명과 계량기명이 일치하는 본문 행에 합니다. 하단 배분표는 제외합니다.')
    st.caption('표는 PDF 순서로 고정됩니다. 옆으로 밀면 나머지 내용을 볼 수 있습니다.')
    headings = ('순서', '위치', '번호', '입주사', '계량기', '시트 행')
    table_header = ''.join(f'<th scope="col">{name}</th>' for name in headings)
    table_rows = ''.join(
        '<tr>' + ''.join(f'<td>{escape(str(value))}</td>' for value in
            (m['order'], m['location'], m['no'], m['company'], m['meter'], m['row_idx'])) + '</tr>'
        for m in meters)
    st.markdown('''<style>
    .meter-route-scroll {overflow-x:auto; -webkit-overflow-scrolling:touch;}
    .meter-route-table {border-collapse:collapse; width:100%; min-width:680px; font-size:14px;}
    .meter-route-table th, .meter-route-table td {padding:9px 10px; border:1px solid rgba(128,128,128,.35); text-align:left;}
    .meter-route-table th {white-space:nowrap; cursor:default; background:rgba(128,128,128,.12);}
    </style>''' + '<div class="meter-route-scroll" tabindex="0" role="region" aria-label="PDF 순서로 고정된 검침 목록">'
        + '<table class="meter-route-table"><thead><tr>' + table_header + '</tr></thead><tbody>'
        + table_rows + '</tbody></table></div>', unsafe_allow_html=True)

visible = [m for m in meters if not only_pending or m.get('curr_val') is None or m['error']]
if not visible:
    st.info('미검침 항목이 없습니다.' if only_pending else '검침 대상이 없습니다.')
    st.stop()
items = {m['row_idx']: m for m in visible}
options = list(items)
selector_key = f'meter_selector_{selected_month}_{only_pending}'
pending = st.session_state.pop('next_meter', None)
if pending in options:
    st.session_state[selector_key] = pending
if st.session_state.get(selector_key) not in options:
    st.session_state[selector_key] = options[0]

def label(row):
    m = items[row]
    status = '✅' if m.get('curr_val') is not None and not m['error'] else '⬜'
    return f"{status} {m['order']:02d}. {m['location']} | {m['no']} [{m['company']}] {m['meter']}"

st.markdown('<div class="tp-section-title">검침 대상 선택 · PDF 순서</div>', unsafe_allow_html=True)
selected = st.selectbox('검침 계량기 선택', options, format_func=label, key=selector_key, label_visibility='collapsed')
target = items[selected]
position = options.index(selected)
def move_to(row):
    st.session_state[selector_key] = row
previous_button, next_button = st.columns(2)
with previous_button:
    st.button('← 이전 계량기', disabled=position == 0, on_click=move_to,
              args=(options[max(0, position-1)],), use_container_width=True)
with next_button:
    st.button('다음 계량기 →', disabled=position == len(options)-1, on_click=move_to,
              args=(options[min(len(options)-1, position+1)],), use_container_width=True)
st.markdown(f'''<div class="tp-info-box">
<b>검침 위치:</b> {escape(target['location'])} · {escape(target['no'])}<br>
<b>입주사:</b> {escape(target['company'])}<br>
<b>계량기:</b> {escape(target['meter'])}</div>''', unsafe_allow_html=True)
if target['order'] == 28:
    st.info('KODATA: 원격검침 고장으로 5층 옥상에서 직접 검침합니다.')
if target['error']:
    st.error(target['error'])
    st.stop()
st.caption(f"전월 지침: {target['prev_val']:,.3f}".rstrip('0').rstrip('.') + f" kWh · 배율: ×{target['ratio']:g}")
default_value = target['curr_val'] if target['curr_val'] is not None else target['prev_val']
st.markdown('<div class="tp-section-title">당월 지침값 입력</div>', unsafe_allow_html=True)
value = st.number_input('당월 지침값', min_value=0, value=int(default_value), step=1, format='%d',
                         key=f'reading_integer_{selected_month}_{selected}', label_visibility='collapsed')
difference = value - target['prev_val']
usage = difference * target['ratio']
a, b = st.columns(2)
a.metric('지침 차이', f'{difference:,.3f}'.rstrip('0').rstrip('.'))
b.metric('당월 사용량 (배율 적용)', f'{usage:,.3f}'.rstrip('0').rstrip('.') + ' kWh')
if difference < 0:
    st.error('당월 지침이 전월 지침보다 작습니다. 입력값을 확인하세요.')
st.caption(f"저장 대상: {selected_month} · {target['company']} · {target['meter']} · 현재 {selected}행")
go_next = st.checkbox('저장 후 다음 계량기로 이동', value=True)
if st.button('검침 데이터 저장', use_container_width=True, disabled=difference < 0):
    try:
        with st.spinner('입주사·계량기 확인 후 저장 중...'):
            fresh = sheet.get_all_values()
            formulas = sheet.get_all_values(value_render_option='FORMULA')
            planned = plan_save(all_rows, fresh, formulas, target, value)
            updates = [{'range': gspread.utils.rowcol_to_a1(r,c), 'values': [[v]]} for r,c,v in planned]
            sheet.batch_update(updates, value_input_option='RAW')
            load_month_rows.clear(selected_month)
            st.session_state['saved_notice'] = f"{target['company']} / {target['meter']} — {planned[0][0]}행 저장 완료"
            if go_next and position + 1 < len(options):
                st.session_state['next_meter'] = options[position+1]
    except Exception as error:
        if is_quota_error(error):
            show_quota_message()
        else:
            st.error(f'저장하지 못했습니다: {error}')
    else:
        st.rerun()
