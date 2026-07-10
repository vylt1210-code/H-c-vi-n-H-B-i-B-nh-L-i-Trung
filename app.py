import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import gspread
from google.oauth2.service_account import Credentials

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

# =========================
# CẤU HÌNH CHUNG
# =========================
BASE = Path(__file__).parent
ASSETS = BASE / "assets"

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

# Google Sheets
try:
    SPREADSHEET_ID = st.secrets["google_sheets"]["spreadsheet_id"]
except KeyError:
    st.error("Thiếu Streamlit Secrets. Hãy dán đúng nội dung file SECRETS_DAN_VAO_STREAMLIT.toml vào Manage app → Settings → Secrets.")
    st.stop()
STUDENTS_SHEET = "hoc_vien"
BUSY_SHEET = "lich_ban"
TEACHER_SHEET = "hoc_phi_thay"

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

CAS = {
    "Ca 1": "08:00 - 09:00",
    "Ca 2": "09:00 - 10:00",
    "Ca 3": "10:00 - 11:00",
    "Ca 4": "13:00 - 14:00",
    "Ca 5": "14:00 - 15:00",
    "Ca 6": "15:00 - 16:00",
    "Ca 7": "16:00 - 17:00",
    "Ca 8": "17:00 - 18:00",
    "Ca 9": "18:00 - 19:00",
    "Ca 10": "19:00 - 20:00",
}

ATTENDANCE_COLS = [f"Buổi {i}" for i in range(1, 13)]

STUDENT_COLUMNS = [
    "Mã HV", "Họ tên", "SĐT", "Khóa học", "Ngày đăng ký", "Lịch học",
    "Tổng buổi", "Đã học", "Trạng thái khóa", "Đã nhận tiền dạy", "Ghi chú"
] + ATTENDANCE_COLS

TEACHER_COLUMNS = ["Thầy", "Tổng học viên", "Đã thanh toán"]


# =========================
# HÀM DỮ LIỆU GOOGLE SHEETS
# =========================
def today_full():
    return datetime.now(VN_TZ).strftime("%d/%m/%Y")


def today_short():
    return datetime.now(VN_TZ).strftime("%d/%m")


def current_vn_day():
    return DAYS[datetime.now(VN_TZ).weekday()]


@st.cache_resource
def get_spreadsheet():
    try:
        raw_json = st.secrets["credentials"]["service_account_json"]
        info = json.loads(raw_json)
    except (KeyError, TypeError, json.JSONDecodeError):
        info = dict(st.secrets["gcp_service_account"])

    if "private_key" in info:
        info["private_key"] = str(info["private_key"]).replace("\\n", "\n")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    credentials = Credentials.from_service_account_info(info, scopes=scopes)
    client = gspread.authorize(credentials)
    return client.open_by_key(SPREADSHEET_ID)


def get_or_create_worksheet(title, rows=1000, cols=40):
    spreadsheet = get_spreadsheet()
    try:
        return spreadsheet.worksheet(title)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=title, rows=rows, cols=cols)


def read_sheet_dataframe(title):
    ws = get_or_create_worksheet(title)
    values = ws.get_all_values()
    if not values:
        return pd.DataFrame()
    headers = values[0]
    if not any(str(h).strip() for h in headers):
        return pd.DataFrame()
    rows = values[1:]
    width = len(headers)
    normalized = [(row + [""] * width)[:width] for row in rows]
    return pd.DataFrame(normalized, columns=headers)


def write_sheet_dataframe(title, df):
    ws = get_or_create_worksheet(
        title,
        rows=max(len(df) + 20, 100),
        cols=max(len(df.columns) + 5, 20),
    )
    clean = df.copy().fillna("")
    for col in clean.columns:
        clean[col] = clean[col].map(
            lambda x: int(x) if isinstance(x, float) and x.is_integer() else x
        )
    values = [clean.columns.astype(str).tolist()] + clean.astype(object).values.tolist()
    ws.clear()
    ws.update(range_name="A1", values=values, value_input_option="USER_ENTERED")


def load_students():
    df = read_sheet_dataframe(STUDENTS_SHEET)

    if df.empty:
        df = pd.DataFrame(columns=STUDENT_COLUMNS)

    for col in STUDENT_COLUMNS:
        if col not in df.columns:
            if col == "Tổng buổi":
                df[col] = 12
            elif col == "Đã học":
                df[col] = 0
            elif col == "Đã nhận tiền dạy":
                df[col] = "Chưa"
            elif col == "Trạng thái khóa":
                df[col] = "Đang học"
            elif col == "Ngày đăng ký":
                df[col] = today_full()
            else:
                df[col] = ""

    if len(df) > 0:
        df["Mã HV"] = pd.to_numeric(df["Mã HV"], errors="coerce")
        missing = df["Mã HV"].isna()
        if missing.any():
            used = set(pd.to_numeric(df["Mã HV"], errors="coerce").dropna().astype(int).tolist())
            next_id = 1
            for idx in df[missing].index:
                while next_id in used:
                    next_id += 1
                df.loc[idx, "Mã HV"] = next_id
                used.add(next_id)

        df["Mã HV"] = df["Mã HV"].astype(int)
        df["Tổng buổi"] = pd.to_numeric(df["Tổng buổi"], errors="coerce").fillna(12).astype(int)
        df["Đã học"] = pd.to_numeric(df["Đã học"], errors="coerce").fillna(0).astype(int)
        df["Đã nhận tiền dạy"] = df["Đã nhận tiền dạy"].fillna("Chưa").replace({True: "Có", False: "Chưa"})
        df["Trạng thái khóa"] = df["Trạng thái khóa"].fillna("Đang học")
        df.loc[df["Đã học"] >= df["Tổng buổi"], "Trạng thái khóa"] = "Kết thúc"

        for col in ATTENDANCE_COLS:
            df[col] = df[col].fillna("").astype(str).replace("nan", "")

    return df[STUDENT_COLUMNS]


def save_students(df):
    write_sheet_dataframe(STUDENTS_SHEET, df[STUDENT_COLUMNS])


def load_busy_slots():
    df = read_sheet_dataframe(BUSY_SHEET)
    if "Slot" in df.columns:
        return set(df["Slot"].dropna().astype(str).tolist())
    return set()


def save_busy_slots(slots):
    write_sheet_dataframe(BUSY_SHEET, pd.DataFrame({"Slot": sorted(list(slots))}))


def load_teacher_fees():
    df = read_sheet_dataframe(TEACHER_SHEET)

    if df.empty:
        df = pd.DataFrame([
            {"Thầy": "Đạt", "Tổng học viên": 0, "Đã thanh toán": 0},
            {"Thầy": "Long", "Tổng học viên": 0, "Đã thanh toán": 0},
        ])

    for col in TEACHER_COLUMNS:
        if col not in df.columns:
            df[col] = 0 if col != "Thầy" else ""

    for teacher in ["Đạt", "Long"]:
        if teacher not in df["Thầy"].astype(str).tolist():
            df = pd.concat([
                df,
                pd.DataFrame([{"Thầy": teacher, "Tổng học viên": 0, "Đã thanh toán": 0}])
            ], ignore_index=True)

    df["Tổng học viên"] = pd.to_numeric(df["Tổng học viên"], errors="coerce").fillna(0).astype(int)
    df["Đã thanh toán"] = pd.to_numeric(df["Đã thanh toán"], errors="coerce").fillna(0).astype(int)
    df.loc[df["Đã thanh toán"] > df["Tổng học viên"], "Đã thanh toán"] = df["Tổng học viên"]
    return df[TEACHER_COLUMNS]


def save_teacher_fees(df):
    write_sheet_dataframe(TEACHER_SHEET, df[TEACHER_COLUMNS])


def make_student_id(df):
    if df.empty:
        return 1
    mx = pd.to_numeric(df["Mã HV"], errors="coerce").max()
    return 1 if pd.isna(mx) else int(mx) + 1


def get_students_by_slot(df, day, ca):
    if df.empty:
        return pd.DataFrame(columns=STUDENT_COLUMNS)
    slot = f"{day} - {ca}"
    matched = df[df["Lịch học"].astype(str).str.contains(slot, na=False, regex=False)].copy()

    if "Trạng thái khóa" in matched.columns:
        matched = matched[matched["Trạng thái khóa"].astype(str) != "Kết thúc"].copy()

    return matched


def ca_status(time_range):
    now = datetime.now(VN_TZ).time()
    start_s, end_s = time_range.split(" - ")
    start = datetime.strptime(start_s, "%H:%M").time()
    end = datetime.strptime(end_s, "%H:%M").time()

    if start <= now < end:
        return "Đang diễn ra", "🟡", "now"
    if now < start:
        return "Sắp tới", "🔵", "soon"
    return "Đã qua", "⚫", "past"


def mark_attendance(df, hv_id):
    idx = df[df["Mã HV"] == hv_id].index
    if len(idx) == 0:
        return df

    idx = idx[0]
    learned = int(df.loc[idx, "Đã học"])
    total = int(df.loc[idx, "Tổng buổi"])

    if learned >= total:
        return df

    next_session = learned + 1

    if next_session <= len(ATTENDANCE_COLS):
        df.loc[idx, ATTENDANCE_COLS[next_session - 1]] = today_short()

    df.loc[idx, "Đã học"] = next_session

    if next_session >= total:
        df.loc[idx, "Trạng thái khóa"] = "Kết thúc"

    return df

    return df


def progress_pct(row):
    total = max(int(row.get("Tổng buổi", 12)), 1)
    done = int(row.get("Đã học", 0))
    return min(100, int(done / total * 100))
def students_by_month(df, year=None, months=[6, 7, 8, 9]):
    if df.empty:
        return {m: 0 for m in months}

    temp = df.copy()
    temp["Ngày đăng ký"] = pd.to_datetime(
        temp["Ngày đăng ký"],
        format="%d/%m/%Y",
        errors="coerce"
    )

    if year is None:
        year = datetime.now(VN_TZ).year

    temp = temp[temp["Ngày đăng ký"].dt.year == year]

    result = {}

    for m in months:
        result[m] = len(temp[temp["Ngày đăng ký"].dt.month == m])

    return result

# =========================
# GIAO DIỆN
# =========================
def asset(name):
    return ASSETS / name


def show_image(name, caption=None):
    path = asset(name)
    if path.exists():
        st.image(str(path), use_container_width=True, caption=caption)


def css():
    bg = asset("background.jpg")
    bg_css = ""
    if bg.exists():
        bg_css = f"""
        background-image:
        linear-gradient(rgba(246,251,255,.92), rgba(246,251,255,.96)),
        url('{bg.as_posix()}');
        background-size: cover;
        background-attachment: fixed;
        background-position: center;
        """

    st.markdown(f"""
    <style>
    .stApp {{ {bg_css} }}
    .block-container {{ padding-top: 1rem; max-width: 1120px; }}
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg,#023e8a,#0077b6,#00a6c8); }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    .hero {{
        background: linear-gradient(135deg, rgba(0,119,182,.96), rgba(0,180,216,.88));
        padding: 24px;
        border-radius: 28px;
        color:white;
        box-shadow: 0 16px 36px rgba(2,62,138,.20);
        margin-bottom: 16px;
    }}
    .hero h1 {{ margin:0; font-size: 36px; font-weight: 900; }}
    .hero p {{ margin:.5rem 0 0; font-size: 17px; opacity:.95; }}
    .metric-card, .student-card, .slot-card {{
        background: rgba(255,255,255,.92);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255,255,255,.86);
        border-radius: 24px;
        box-shadow: 0 12px 28px rgba(2,62,138,.10);
        padding: 18px;
        margin-bottom: 14px;
    }}
    .metric-label {{ color:#426579; font-weight:800; font-size:14px; }}
    .metric-value {{ color:#023e8a; font-size:34px; font-weight:950; margin-top:5px; }}
    .section-title {{ color:#023e8a; font-weight:950; font-size:24px; margin: 18px 0 10px; }}
    .student-name, .slot-title {{ color:#023e8a; font-size:20px; font-weight:950; }}
    .small {{ color:#607887; font-size:14px; }}
    .progress-wrap {{ background:#e9f6fb; height:12px; border-radius:999px; overflow:hidden; margin:12px 0 7px; }}
    .progress-bar {{ height:12px; background:linear-gradient(90deg,#00b4d8,#2dc653); border-radius:999px; }}
    .pill {{
        display:inline-block;
        padding:7px 11px;
        border-radius:999px;
        font-size:13px;
        font-weight:850;
        margin:5px 4px 0 0;
    }}
    .pill-now {{ background:#fff3bf; color:#7a5c00; }}
    .pill-soon {{ background:#dff6ff; color:#005f8f; }}
    .pill-past {{ background:#e9ecef; color:#495057; }}
    .pill-busy {{ background:#ffe3e8; color:#b00020; }}
    .pill-ok {{ background:#d8fbe0; color:#087f23; }}
    .pill-warn {{ background:#fff3bf; color:#7a5c00; }}
    div.stButton > button {{
        border-radius: 16px;
        font-weight: 850;
        border: 1px solid #d9f1fa;
        box-shadow: 0 6px 16px rgba(0,119,182,.08);
    }}
    div.stButton > button:hover {{
        border-color:#00b4d8;
        color:#0077b6;
    }}
    </style>
    """, unsafe_allow_html=True)


def hero(title, subtitle):
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def metric(label, value, icon):
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>{icon} {label}</div>
        <div class='metric-value'>{value}</div>
    </div>
    """, unsafe_allow_html=True)


def student_card(row):
    pct = progress_pct(row)
    remaining = int(row["Tổng buổi"]) - int(row["Đã học"])
    money = row.get("Đã nhận tiền dạy", "Chưa")
    money_class = "pill-ok" if money == "Có" else "pill-warn"
    status_class = "pill-ok" if remaining <= 0 else ("pill-warn" if remaining <= 2 else "pill-soon")
    status_text = "Đủ buổi" if remaining <= 0 else ("Sắp hết" if remaining <= 2 else "Đang học")

    attendance_text = " • ".join([str(row[c]) for c in ATTENDANCE_COLS if str(row[c]).strip() not in ["", "nan"]])

    st.markdown(f"""
    <div class='student-card'>
        <div class='student-name'>👤 {row['Họ tên']}</div>
        <div class='small'>📱 {row.get('SĐT','')} • 🏊 {row.get('Khóa học','')} • 🗓️ ĐK: {row.get('Ngày đăng ký','')}</div>
        <div class='progress-wrap'><div class='progress-bar' style='width:{pct}%'></div></div>
        <div class='small'><b>{row['Đã học']}/{row['Tổng buổi']}</b> buổi • Còn {max(remaining,0)} buổi</div>
        <span class='pill {money_class}'>💰 Tiền dạy: {money}</span>
        <span class='pill {status_class}'>📌 {status_text}</span>
        <span class='pill {'pill-past' if row.get('Trạng thái khóa','Đang học') == 'Kết thúc' else 'pill-ok'}'>🎓 {row.get('Trạng thái khóa','Đang học')}</span>
        <div class='small' style='margin-top:8px'>📅 {row.get('Lịch học','')}</div>
        <div class='small'>✅ Điểm danh: {attendance_text if attendance_text else 'Chưa có'}</div>
        <div class='small'>📝 {row.get('Ghi chú','')}</div>
    </div>
    """, unsafe_allow_html=True)


# =========================
# TRANG
# =========================
def page_dashboard(df, busy_slots):
    now = datetime.now(VN_TZ)
    hero("🏊 BLT Swimming Club", f"Dashboard nhanh • {now.strftime('%H:%M:%S')} GMT+7 • {now.strftime('%d/%m/%Y')}")
    show_image("dashboard.jpg")

    today = current_vn_day()
    today_students = sum(len(get_students_by_slot(df, today, ca)) for ca in CAS)
    almost_done = len(df[(df["Tổng buổi"] - df["Đã học"]) <= 2]) if not df.empty else 0
    unpaid = len(df[df["Đã nhận tiền dạy"] == "Chưa"]) if not df.empty else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1: metric("Tổng học viên", len(df), "👨‍🎓")
    with c2: metric("HV hôm nay", today_students, "📅")
    with c3: metric("Sắp hết buổi", almost_done, "⚠️")
    with c4: metric("Chưa nhận tiền", unpaid, "💰")
    report = students_by_month(df)

    st.markdown(
        "<div class='section-title'>📊 Báo cáo học viên theo tháng</div>",
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(4)

    with m1:
        metric("Tháng 6", report[6], "👨‍🎓")

    with m2:
        metric("Tháng 7", report[7], "👨‍🎓")

    with m3:
        metric("Tháng 8", report[8], "👨‍🎓")

    with m4:
        metric("Tháng 9", report[9], "👨‍🎓")
    st.markdown("<div class='section-title'>Lịch hôm nay</div>", unsafe_allow_html=True)
    for ca, tr in CAS.items():
        slot = f"{today} - {ca}"
        status, icon, cls = ca_status(tr)
        count = len(get_students_by_slot(df, today, ca))
        busy = slot in busy_slots
        pill_class = "pill-busy" if busy else f"pill-{cls}"
        label = "🔴 Bận" if busy else f"{icon} {status}"

        st.markdown(f"""
        <div class='slot-card'>
            <div class='slot-title'>{ca} • {tr}</div>
            <div class='small'>{today}</div>
            <span class='pill {pill_class}'>{label}</span>
            <span class='pill pill-ok'>{count} học viên</span>
        </div>
        """, unsafe_allow_html=True)


def page_schedule(df, busy_slots):
    hero("📅 Lịch dạy", "Bấm vào card ca học để xem học viên và điểm danh nhanh")
    show_image("pool.jpg")
    now = datetime.now(VN_TZ)
    st.info(f"🕒 Giờ Việt Nam: {now.strftime('%H:%M:%S')} — tự cập nhật mỗi 60 giây")

    if hasattr(st, "segmented_control"):
        day = st.segmented_control("Chọn ngày", DAYS, default=current_vn_day())
    else:
        day = st.selectbox("Chọn ngày", DAYS, index=DAYS.index(current_vn_day()))

    st.markdown("<div class='section-title'>Các ca trong ngày</div>", unsafe_allow_html=True)

    for ca, tr in CAS.items():
        slot = f"{day} - {ca}"
        status, icon, cls = ca_status(tr)
        count = len(get_students_by_slot(df, day, ca))
        busy = slot in busy_slots
        label = "🔴 Bận" if busy else f"{icon} {status} • {count} HV"

        c1, c2 = st.columns([3, 1])
        with c1:
            st.markdown(f"""
            <div class='slot-card'>
                <div class='slot-title'>{ca} • {tr}</div>
                <div class='small'>{day}</div>
                <span class='pill {'pill-busy' if busy else 'pill-' + cls}'>{label}</span>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            if st.button("Mở", key=f"open_{slot}", use_container_width=True):
                st.session_state["selected_day"] = day
                st.session_state["selected_ca"] = ca

    selected_day = st.session_state.get("selected_day", day)
    selected_ca = st.session_state.get("selected_ca", list(CAS.keys())[0])
    selected_slot = f"{selected_day} - {selected_ca}"

    st.markdown("---")
    st.markdown(f"<div class='section-title'>Chi tiết: {selected_slot} • {CAS[selected_ca]}</div>", unsafe_allow_html=True)

    if selected_slot in busy_slots:
        st.error("Ca này đang bận. Vào Cài đặt để mở lại.")
        return

    class_df = get_students_by_slot(df, selected_day, selected_ca)

    if class_df.empty:
        st.warning("Ca này chưa có học viên.")
        return

    for _, row in class_df.iterrows():
        student_card(row)

    with st.expander("📋 Bảng điểm danh 12 buổi"):
        show_cols = ["Họ tên", "Ngày đăng ký", "Trạng thái khóa", "Đã học", "Tổng buổi"] + ATTENDANCE_COLS
        st.dataframe(class_df[show_cols], use_container_width=True, hide_index=True)

    checked_ids = st.multiselect(
        "Chọn học viên đã học buổi này",
        class_df["Mã HV"].tolist(),
        format_func=lambda x: class_df.loc[class_df["Mã HV"] == x, "Họ tên"].values[0],
    )

    if st.button("✅ Điểm danh / Ghi ngày hôm nay", use_container_width=True):
        for hv_id in checked_ids:
            df = mark_attendance(df, hv_id)
        save_students(df)
        st.success(f"Đã điểm danh và ghi ngày {today_short()}.")
        st.rerun()


def page_students(df, busy_slots):
    hero("👨‍🎓 Học viên", "Thêm, tìm kiếm, sửa và xóa học viên trên cùng một màn hình")
    show_image("student.jpg")

    with st.expander("➕ Thêm học viên mới", expanded=False):
        with st.form("add_student_form"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Họ tên")
                phone = st.text_input("Số điện thoại")
                course = st.selectbox("Khóa học", ["Ếch", "Sải", "Sải ôn ếch", "Khác"])
            with c2:
                total = st.number_input("Tổng buổi", min_value=1, value=12)
                learned = st.number_input("Đã học", min_value=0, value=0)
                register_date = st.date_input("Ngày đăng ký", value=datetime.now(VN_TZ).date())
                paid = st.checkbox("Đã nhận tiền dạy")

            note = st.text_area("Ghi chú")
            schedule = []

            for day in DAYS:
                available = [ca for ca in CAS if f"{day} - {ca}" not in busy_slots]
                selected = st.multiselect(day, available, key=f"add_{day}")
                schedule += [f"{day} - {ca}" for ca in selected]

            submitted = st.form_submit_button("💾 Lưu học viên", use_container_width=True)

            if submitted:
                if not name.strip():
                    st.warning("Nhập họ tên trước.")
                elif not schedule:
                    st.warning("Chọn ít nhất một ca học.")
                else:
                    new = {
                        "Mã HV": make_student_id(df),
                        "Họ tên": name.strip(),
                        "SĐT": phone.strip(),
                        "Khóa học": course,
                        "Ngày đăng ký": register_date.strftime("%d/%m/%Y"),
                        "Lịch học": ", ".join(schedule),
                        "Tổng buổi": int(total),
                        "Đã học": int(learned),
                        "Trạng thái khóa": "Kết thúc" if int(learned) >= int(total) else "Đang học",
                        "Đã nhận tiền dạy": "Có" if paid else "Chưa",
                        "Ghi chú": note.strip(),
                    }
                    for col in ATTENDANCE_COLS:
                        new[col] = ""

                    save_students(pd.concat([df, pd.DataFrame([new])], ignore_index=True))
                    st.success("Đã thêm học viên.")
                    st.rerun()

    search = st.text_input("🔍 Tìm theo tên hoặc số điện thoại")
    show = df.copy()

    if search.strip():
        show = show[
            show["Họ tên"].astype(str).str.contains(search, case=False, na=False)
            | show["SĐT"].astype(str).str.contains(search, case=False, na=False)
        ]

    for _, row in show.iterrows():
        student_card(row)

    with st.expander("📋 Xem toàn bộ bảng điểm danh"):
        show_cols = ["Mã HV", "Họ tên", "Ngày đăng ký", "Trạng thái khóa", "Đã học", "Tổng buổi"] + ATTENDANCE_COLS
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("<div class='section-title'>Sửa / Xóa nhanh</div>", unsafe_allow_html=True)

    if not df.empty:
        sid = st.selectbox("Chọn học viên", df["Mã HV"].tolist(), format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0])
        idx = df[df["Mã HV"] == sid].index[0]

        with st.form("edit_student"):
            c1, c2 = st.columns(2)
            with c1:
                ename = st.text_input("Họ tên", df.loc[idx, "Họ tên"])
                ephone = st.text_input("SĐT", str(df.loc[idx, "SĐT"]))
                course_options = ["Ếch", "Sải", "Sải ôn ếch", "Khác"]
                old_course = df.loc[idx, "Khóa học"]
                ecourse = st.selectbox("Khóa", course_options, index=course_options.index(old_course) if old_course in course_options else 3)
                eregister = st.text_input("Ngày đăng ký", str(df.loc[idx, "Ngày đăng ký"]))
            with c2:
                etotal = st.number_input("Tổng buổi", min_value=1, value=int(df.loc[idx, "Tổng buổi"]))
                elearned = st.number_input("Đã học", min_value=0, value=int(df.loc[idx, "Đã học"]))
                old_status = df.loc[idx, "Trạng thái khóa"] if "Trạng thái khóa" in df.columns else "Đang học"
                estatus = st.selectbox(
                    "Trạng thái khóa",
                    ["Đang học", "Kết thúc"],
                    index=1 if old_status == "Kết thúc" else 0
                )
                emoney = st.selectbox("Tiền dạy", ["Chưa", "Có"], index=1 if df.loc[idx, "Đã nhận tiền dạy"] == "Có" else 0)

            eschedule = st.text_area("Lịch học", str(df.loc[idx, "Lịch học"]))
            enote = st.text_area("Ghi chú", str(df.loc[idx, "Ghi chú"]))
            save_btn = st.form_submit_button("💾 Cập nhật", use_container_width=True)

        if save_btn:
            df.loc[idx, "Họ tên"] = ename
            df.loc[idx, "SĐT"] = ephone
            df.loc[idx, "Khóa học"] = ecourse
            df.loc[idx, "Ngày đăng ký"] = eregister
            df.loc[idx, "Lịch học"] = eschedule
            df.loc[idx, "Tổng buổi"] = int(etotal)
            df.loc[idx, "Đã học"] = int(elearned)
            df.loc[idx, "Trạng thái khóa"] = estatus
            df.loc[idx, "Đã nhận tiền dạy"] = emoney
            df.loc[idx, "Ghi chú"] = enote
        
            save_students(df)
            st.success("Đã cập nhật.")
            st.rerun()

        if st.button("🎓 Kết thúc khóa học viên này", use_container_width=True):
            df.loc[df["Mã HV"] == sid, "Trạng thái khóa"] = "Kết thúc"
            save_students(df)
            st.success("Đã kết thúc khóa. Học viên sẽ không còn xuất hiện trong lịch dạy.")
            st.rerun()

        confirm = st.checkbox("Tôi xác nhận muốn xóa học viên này")

        if st.button("🗑 Xóa học viên", use_container_width=True):
            if confirm:
                save_students(df[df["Mã HV"] != sid])
                st.success("Đã xóa.")
                st.rerun()
            else:
                st.warning("Tick xác nhận trước khi xóa.")


def page_money(df):
    hero("💰 Học phí & tiền dạy", "Theo dõi nhanh trạng thái đã nhận tiền dạy")

    if df.empty:
        st.warning("Chưa có học viên.")
        return

    unpaid = df[df["Đã nhận tiền dạy"] == "Chưa"]
    paid = df[df["Đã nhận tiền dạy"] == "Có"]

    c1, c2 = st.columns(2)
    with c1: metric("Chưa nhận", len(unpaid), "🔴")
    with c2: metric("Đã nhận", len(paid), "🟢")

    sid = st.selectbox("Chọn học viên cập nhật tiền dạy", df["Mã HV"].tolist(), format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0])
    current = df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"].values[0]
    status = st.radio("Trạng thái", ["Chưa", "Có"], horizontal=True, index=1 if current == "Có" else 0)

    if st.button("💾 Lưu trạng thái", use_container_width=True):
        df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"] = status
        save_students(df)
        st.success("Đã lưu.")
        st.rerun()

    st.dataframe(df[["Họ tên", "Khóa học", "Trạng thái khóa", "Đã học", "Tổng buổi", "Đã nhận tiền dạy"]], use_container_width=True, hide_index=True)


def page_teacher_fee():
    hero("👨‍🏫 Tiền thầy", "Quản lý học phí thầy Đạt và thầy Long")
    tdf = load_teacher_fees()

    st.info("Ví dụ: thầy Đạt có 10 học viên, đã thanh toán 9 thì còn 1. Có học viên mới bấm +1 học viên. Trả thêm 1 học viên thì bấm Thanh toán 1 HV.")

    for teacher in ["Đạt", "Long"]:
        idx = tdf[tdf["Thầy"] == teacher].index[0]
        total = int(tdf.loc[idx, "Tổng học viên"])
        paid = int(tdf.loc[idx, "Đã thanh toán"])
        remain = max(total - paid, 0)
        pct = 0 if total == 0 else int(paid / total * 100)

        st.markdown(f"""
        <div class='student-card'>
            <div class='student-name'>👨‍🏫 Thầy {teacher}</div>
            <div class='small'>Tổng học viên: <b>{total}</b> • Đã thanh toán: <b>{paid}</b> • Còn lại: <b>{remain}</b></div>
            <div class='progress-wrap'><div class='progress-bar' style='width:{pct}%'></div></div>
            <span class='pill pill-ok'>✅ Đã thanh toán: {paid}</span>
            <span class='pill {'pill-warn' if remain > 0 else 'pill-ok'}'>📌 Còn lại: {remain}</span>
        </div>
        """, unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button(f"➕ +1 học viên", key=f"add_{teacher}", use_container_width=True):
                tdf.loc[idx, "Tổng học viên"] = total + 1
                save_teacher_fees(tdf)
                st.rerun()

        with c2:
            if st.button(f"💵 Thanh toán 1 HV", key=f"pay_{teacher}", use_container_width=True, disabled=paid >= total):
                tdf.loc[idx, "Đã thanh toán"] = min(paid + 1, total)
                save_teacher_fees(tdf)
                st.rerun()

        with c3:
            if st.button(f"↩️ Trừ 1 thanh toán", key=f"undo_{teacher}", use_container_width=True, disabled=paid <= 0):
                tdf.loc[idx, "Đã thanh toán"] = max(paid - 1, 0)
                save_teacher_fees(tdf)
                st.rerun()

        with st.expander(f"✏️ Chỉnh tay thầy {teacher}"):
            new_total = st.number_input(f"Tổng học viên - {teacher}", min_value=0, value=total, key=f"total_{teacher}")
            new_paid = st.number_input(f"Đã thanh toán - {teacher}", min_value=0, max_value=int(new_total), value=min(paid, int(new_total)), key=f"paid_{teacher}")

            if st.button(f"💾 Lưu thầy {teacher}", key=f"save_{teacher}", use_container_width=True):
                tdf.loc[idx, "Tổng học viên"] = int(new_total)
                tdf.loc[idx, "Đã thanh toán"] = int(new_paid)
                save_teacher_fees(tdf)
                st.rerun()

    st.markdown("---")
    tdf["Còn lại"] = tdf["Tổng học viên"] - tdf["Đã thanh toán"]
    st.dataframe(tdf, use_container_width=True, hide_index=True)


def page_settings(busy_slots):
    hero("⚙️ Cài đặt", "Lịch bận, khôi phục và sao lưu dữ liệu")

    with st.expander("📥 Khôi phục học viên từ CSV", expanded=False):
        st.caption("Dùng file hoc_vien.csv đã khôi phục. Dữ liệu hiện tại trên Google Sheets sẽ được thay thế.")
        uploaded = st.file_uploader("Chọn file CSV", type=["csv"], key="restore_students_csv")
        confirm_restore = st.checkbox("Tôi xác nhận thay thế dữ liệu học viên hiện tại", key="confirm_restore")

        if st.button("Khôi phục lên Google Sheets", use_container_width=True):
            if uploaded is None:
                st.warning("Hãy chọn file CSV trước.")
            elif not confirm_restore:
                st.warning("Hãy tick xác nhận trước khi khôi phục.")
            else:
                try:
                    restored = pd.read_csv(uploaded)
                    for col in STUDENT_COLUMNS:
                        if col not in restored.columns:
                            restored[col] = ""
                    restored["Mã HV"] = pd.to_numeric(restored["Mã HV"], errors="coerce")
                    restored["Tổng buổi"] = pd.to_numeric(restored["Tổng buổi"], errors="coerce").fillna(12).astype(int)
                    restored["Đã học"] = pd.to_numeric(restored["Đã học"], errors="coerce").fillna(0).astype(int)

                    missing_ids = restored["Mã HV"].isna()
                    next_id = 1
                    used = set(restored["Mã HV"].dropna().astype(int).tolist())
                    for idx in restored[missing_ids].index:
                        while next_id in used:
                            next_id += 1
                        restored.loc[idx, "Mã HV"] = next_id
                        used.add(next_id)

                    restored["Mã HV"] = restored["Mã HV"].astype(int)
                    restored = restored[STUDENT_COLUMNS]
                    save_students(restored)
                    st.success(f"Đã khôi phục {len(restored)} học viên lên Google Sheets.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Không thể đọc hoặc khôi phục file CSV: {exc}")

    current_students = load_students()
    if not current_students.empty:
        export_csv = current_students.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            "📤 Tải bản sao lưu học viên",
            data=export_csv,
            file_name=f"hoc_vien_backup_{datetime.now(VN_TZ).strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True,
        )

    st.markdown("---")
    new_slots = set()

    for day in DAYS:
        st.markdown(f"<div class='section-title'>{day}</div>", unsafe_allow_html=True)
        cols = st.columns(2)

        for i, ca in enumerate(CAS):
            slot = f"{day} - {ca}"

            with cols[i % 2]:
                if st.checkbox(f"{ca} • {CAS[ca]}", value=slot in busy_slots, key=f"busy_{slot}"):
                    new_slots.add(slot)

    if st.button("💾 Lưu lịch bận", use_container_width=True):
        save_busy_slots(new_slots)
        st.success("Đã lưu lịch bận.")
        st.rerun()


# =========================
# MAIN
# =========================
def main():
    icon = str(asset("logo.png")) if asset("logo.png").exists() else "🏊"
    st.set_page_config(page_title="BLT Manager Professional", page_icon=icon, layout="wide")
    css()

    if st_autorefresh:
        st_autorefresh(interval=60_000, key="blt_realtime")

    df = load_students()
    busy_slots = load_busy_slots()

    with st.sidebar:
        if asset("logo.png").exists():
            st.image(str(asset("logo.png")), width=125)

        st.markdown("## BLT Manager")
        page = st.radio(
            "Điều hướng",
            ["🏠 Dashboard", "📅 Lịch dạy", "👨‍🎓 Học viên", "💰 Học phí", "👨‍🏫 Tiền thầy", "⚙️ Cài đặt"],
            label_visibility="collapsed",
        )
        st.caption("Mobile-first • Giờ Việt Nam GMT+7")

    if page == "🏠 Dashboard":
        page_dashboard(df, busy_slots)
    elif page == "📅 Lịch dạy":
        page_schedule(df, busy_slots)
    elif page == "👨‍🎓 Học viên":
        page_students(df, busy_slots)
    elif page == "💰 Học phí":
        page_money(df)
    elif page == "👨‍🏫 Tiền thầy":
        page_teacher_fee()
    else:
        page_settings(busy_slots)


if __name__ == "__main__":
    main()
