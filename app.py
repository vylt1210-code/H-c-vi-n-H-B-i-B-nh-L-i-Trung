import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None


# =============================
# CONFIG
# =============================
BASE = Path(__file__).parent
DATA_DIR = BASE / "data"
ASSETS = BASE / "assets"
DATA_DIR.mkdir(exist_ok=True)

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

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
    "Tổng buổi", "Đã học", "Đã nhận tiền dạy", "Ghi chú"
] + ATTENDANCE_COLS

TEACHER_COLUMNS = ["Thầy", "Tổng học viên", "Đã thanh toán"]


def resolve_file(name: str) -> Path:
    data_file = DATA_DIR / name
    root_file = BASE / name

    if data_file.exists():
        return data_file
    if root_file.exists():
        return root_file
    return data_file


DATA_FILE = resolve_file("hoc_vien.csv")
BUSY_FILE = resolve_file("lich_ban.csv")
TEACHER_FILE = resolve_file("hoc_phi_thay.csv")


# =============================
# DATA FUNCTIONS
# =============================
def now_vn():
    return datetime.now(VN_TZ)


def today_full():
    return now_vn().strftime("%d/%m/%Y")


def today_short():
    return now_vn().strftime("%d/%m")


def current_day_name():
    return DAYS[now_vn().weekday()]


def load_students():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=STUDENT_COLUMNS)

    for col in STUDENT_COLUMNS:
        if col not in df.columns:
            if col == "Tổng buổi":
                df[col] = 12
            elif col == "Đã học":
                df[col] = 0
            elif col == "Đã nhận tiền dạy":
                df[col] = "Chưa"
            elif col == "Ngày đăng ký":
                df[col] = today_full()
            else:
                df[col] = ""

    if not df.empty:
        df["Mã HV"] = pd.to_numeric(df["Mã HV"], errors="coerce")

        used_ids = set(
            pd.to_numeric(df["Mã HV"], errors="coerce")
            .dropna()
            .astype(int)
            .tolist()
        )

        next_id = 1
        for idx in df[df["Mã HV"].isna()].index:
            while next_id in used_ids:
                next_id += 1
            df.loc[idx, "Mã HV"] = next_id
            used_ids.add(next_id)

        df["Mã HV"] = df["Mã HV"].astype(int)
        df["Tổng buổi"] = pd.to_numeric(df["Tổng buổi"], errors="coerce").fillna(12).astype(int)
        df["Đã học"] = pd.to_numeric(df["Đã học"], errors="coerce").fillna(0).astype(int)
        df["Đã nhận tiền dạy"] = (
            df["Đã nhận tiền dạy"]
            .fillna("Chưa")
            .replace({True: "Có", False: "Chưa"})
        )

        for col in ATTENDANCE_COLS:
            df[col] = df[col].fillna("").astype(str).replace("nan", "")

    return df[STUDENT_COLUMNS]


def save_students(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def load_busy_slots():
    if BUSY_FILE.exists():
        df = pd.read_csv(BUSY_FILE)

        if "Slot" in df.columns:
            return set(df["Slot"].dropna().astype(str).tolist())

    return set()


def save_busy_slots(slots):
    pd.DataFrame({"Slot": sorted(list(slots))}).to_csv(
        BUSY_FILE, index=False, encoding="utf-8-sig"
    )


def load_teacher_fees():
    if TEACHER_FILE.exists():
        df = pd.read_csv(TEACHER_FILE)
    else:
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
                pd.DataFrame([{
                    "Thầy": teacher,
                    "Tổng học viên": 0,
                    "Đã thanh toán": 0
                }])
            ], ignore_index=True)

    df["Tổng học viên"] = pd.to_numeric(df["Tổng học viên"], errors="coerce").fillna(0).astype(int)
    df["Đã thanh toán"] = pd.to_numeric(df["Đã thanh toán"], errors="coerce").fillna(0).astype(int)
    df.loc[df["Đã thanh toán"] > df["Tổng học viên"], "Đã thanh toán"] = df["Tổng học viên"]

    return df[TEACHER_COLUMNS]


def save_teacher_fees(df):
    df.to_csv(TEACHER_FILE, index=False, encoding="utf-8-sig")


def make_student_id(df):
    if df.empty:
        return 1

    max_id = pd.to_numeric(df["Mã HV"], errors="coerce").max()
    return 1 if pd.isna(max_id) else int(max_id) + 1


def get_students_by_slot(df, day, ca):
    if df.empty:
        return pd.DataFrame(columns=STUDENT_COLUMNS)

    slot = f"{day} - {ca}"
    return df[df["Lịch học"].astype(str).str.contains(slot, na=False, regex=False)].copy()


def ca_status(time_range):
    current = now_vn().time()
    start_s, end_s = time_range.split(" - ")

    start = datetime.strptime(start_s, "%H:%M").time()
    end = datetime.strptime(end_s, "%H:%M").time()

    if start <= current < end:
        return "Đang diễn ra", "now", "●"
    if current < start:
        return "Sắp tới", "soon", "●"
    return "Đã qua", "past", "●"


def mark_attendance(df, hv_id):
    idx = df[df["Mã HV"] == hv_id].index

    if len(idx) == 0:
        return df

    idx = idx[0]
    learned = int(df.loc[idx, "Đã học"])
    total = int(df.loc[idx, "Tổng buổi"])

    if learned >= total:
        return df

    for col in ATTENDANCE_COLS:
        value = str(df.loc[idx, col]).strip()

        if value == "" or value.lower() == "nan":
            df.loc[idx, col] = today_short()
            break

    df.loc[idx, "Đã học"] = learned + 1
    return df


def progress_pct(row):
    total = max(int(row.get("Tổng buổi", 12)), 1)
    done = int(row.get("Đã học", 0))
    return min(100, int(done / total * 100))


# =============================
# UI HELPERS
# =============================
def asset(name: str) -> Path:
    return ASSETS / name


def apply_style():
    st.markdown(
        """
        <style>
        :root {
            --bg: #e9eef2;
            --card: #ffffff;
            --teal: #008f8f;
            --teal-dark: #007373;
            --text: #425563;
            --muted: #6b7d88;
            --line: #d8e0e5;
            --red: #ef4444;
            --orange: #f97316;
            --green: #22c55e;
            --blue: #3b82f6;
            --yellow: #f59e0b;
        }

        .stApp {
            background: var(--bg);
        }

        .block-container {
            max-width: 1280px;
            padding-top: 1rem;
            padding-bottom: 3rem;
        }

        [data-testid="stSidebar"] {
            background: #ffffff;
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] * {
            color: #425563;
        }

        .topbar {
            background: #ffffff;
            border-radius: 0 0 18px 18px;
            padding: 15px 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 8px 20px rgba(30, 50, 70, .08);
            margin-bottom: 18px;
        }

        .brand {
            display: flex;
            align-items: center;
            gap: 14px;
        }

        .hamb {
            font-size: 28px;
            color: var(--teal);
            font-weight: 900;
        }

        .brand-main {
            font-size: 30px;
            font-weight: 950;
            color: var(--teal);
            line-height: 1;
        }

        .brand-sub {
            font-size: 11px;
            color: #ef4444;
            font-weight: 900;
            letter-spacing: 1.5px;
            margin-top: 3px;
        }

        .user {
            display: flex;
            align-items: center;
            gap: 10px;
            color: #333;
            font-weight: 800;
        }

        .avatar-mini {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: #e8f7f7;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            border: 1px solid var(--line);
        }

        .page-title {
            color: var(--teal);
            font-size: 26px;
            font-weight: 950;
            margin-bottom: 14px;
        }

        .card {
            background: #ffffff;
            border-radius: 18px;
            padding: 24px;
            box-shadow: 0 8px 24px rgba(40, 60, 80, .05);
            margin-bottom: 18px;
        }

        .info-card {
            min-height: 256px;
        }

        .card-head {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-bottom: 1px solid var(--line);
            padding-bottom: 14px;
            margin-bottom: 18px;
        }

        .card-head .title {
            color: var(--teal);
            font-size: 25px;
            font-weight: 950;
        }

        .card-head .link {
            color: var(--teal);
            font-size: 14px;
            font-weight: 800;
        }

        .info-grid {
            display: grid;
            grid-template-columns: 150px 1fr 1fr;
            gap: 22px;
            align-items: center;
        }

        .logo-frame {
            width: 135px;
            height: 170px;
            border: 1.5px solid var(--teal);
            border-radius: 8px;
            overflow: hidden;
            background: #eef9f9;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 950;
            color: var(--teal);
        }

        .info-line {
            font-size: 16px;
            color: var(--text);
            margin: 13px 0;
            font-weight: 600;
        }

        .info-line b {
            color: #5c6970;
        }

        .mini-card {
            background: #fff;
            border-radius: 18px;
            padding: 24px 26px;
            box-shadow: 0 8px 24px rgba(40, 60, 80, .05);
            min-height: 132px;
            margin-bottom: 18px;
        }

        .mini-card.teal {
            background: var(--teal);
            color: white;
        }

        .mini-title {
            font-size: 18px;
            font-weight: 950;
            color: inherit;
        }

        .mini-number {
            font-size: 34px;
            font-weight: 950;
            margin-top: 8px;
        }

        .mini-link {
            color: red;
            font-weight: 900;
            margin-top: 2px;
        }

        .mini-card.teal .mini-link {
            color: white;
        }

        .today-card {
            min-height: 420px;
        }

        .today-row {
            display: grid;
            grid-template-columns: 84px 1fr 88px;
            gap: 10px;
            align-items: center;
            padding: 12px 10px;
            border-bottom: 1px solid #eef3f5;
        }

        .today-time {
            font-size: 13px;
            font-weight: 900;
            color: var(--muted);
        }

        .today-title {
            color: #123;
            font-weight: 900;
        }

        .today-sub {
            color: var(--muted);
            font-size: 13px;
        }

        .pill {
            display: inline-block;
            padding: 6px 10px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: 900;
            text-align: center;
            white-space: nowrap;
        }

        .pill-now { background: #fff3bf; color: #7a5c00; }
        .pill-soon { background: #dff6ff; color: #005f8f; }
        .pill-past { background: #e9ecef; color: #495057; }
        .pill-busy { background: #ffe3e8; color: #b00020; }
        .pill-ok { background: #d8fbe0; color: #087f23; }
        .pill-warn { background: #fff3bf; color: #7a5c00; }

        .quick-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 18px;
        }

        .quick-card {
            background: #ffffff;
            border-radius: 16px;
            padding: 24px 16px;
            text-align: center;
            box-shadow: 0 8px 24px rgba(40, 60, 80, .05);
            min-height: 128px;
            transition: transform .15s ease, box-shadow .15s ease;
        }

        .quick-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 30px rgba(40, 60, 80, .09);
        }

        .quick-icon {
            color: var(--teal);
            font-size: 34px;
            font-weight: 900;
        }

        .quick-text {
            color: #6a7b84;
            font-size: 16px;
            font-weight: 950;
            margin-top: 10px;
            line-height: 1.25;
        }

        .slot-card, .student-card {
            background: #ffffff;
            border-radius: 18px;
            padding: 20px;
            box-shadow: 0 8px 24px rgba(40, 60, 80, .05);
            margin-bottom: 14px;
        }

        .slot-title, .student-name {
            color: #0a4f93;
            font-size: 22px;
            font-weight: 950;
        }

        .small {
            color: #657884;
            font-size: 14px;
        }

        .progress-wrap {
            background: #e8f6fb;
            height: 12px;
            border-radius: 999px;
            overflow: hidden;
            margin: 12px 0 8px;
        }

        .progress-bar {
            height: 12px;
            background: linear-gradient(90deg, #00b4d8, #22c55e);
            border-radius: 999px;
        }

        div.stButton > button {
            border-radius: 12px;
            font-weight: 900;
            border: 1px solid #d6e5ea;
        }

        @media(max-width: 900px) {
            .info-grid {
                grid-template-columns: 1fr;
            }

            .quick-grid {
                grid-template-columns: repeat(2, 1fr);
            }

            .today-row {
                grid-template-columns: 74px 1fr;
            }

            .today-row .pill {
                grid-column: 2;
                width: fit-content;
            }

            .brand-main {
                font-size: 21px;
            }
        }
        </style>
        """,
        unsafe_allow_html=True
    )


def topbar():
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">
                <div class="hamb">☰</div>
                <div>
                    <div class="brand-main">BLT SWIMMING</div>
                    <div class="brand-sub">SWIM MANAGEMENT SYSTEM</div>
                </div>
            </div>
            <div class="user">
                <div class="avatar-mini">🏊</div>
                <div>Hồ bơi Bình Lợi Trung ▾</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def metric_box(title, number, link="Xem chi tiết", teal=False):
    cls = "mini-card teal" if teal else "mini-card"

    st.markdown(
        f"""
        <div class="{cls}">
            <div class="mini-title">{title}</div>
            <div class="mini-number">{number}</div>
            <div class="mini-link">{link}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def student_card(row):
    pct = progress_pct(row)
    remaining = int(row["Tổng buổi"]) - int(row["Đã học"])
    money = row.get("Đã nhận tiền dạy", "Chưa")

    money_class = "pill-ok" if money == "Có" else "pill-warn"
    status_class = "pill-ok" if remaining <= 0 else ("pill-warn" if remaining <= 2 else "pill-soon")
    status = "Đủ buổi" if remaining <= 0 else ("Sắp hết" if remaining <= 2 else "Đang học")

    dates = " • ".join([
        str(row[col]) for col in ATTENDANCE_COLS
        if str(row[col]).strip() not in ["", "nan"]
    ])

    st.markdown(
        f"""
        <div class="student-card">
            <div class="student-name">👤 {row['Họ tên']}</div>
            <div class="small">📱 {row.get('SĐT','')} • 🏊 {row.get('Khóa học','')} • 🗓️ ĐK: {row.get('Ngày đăng ký','')}</div>
            <div class="progress-wrap"><div class="progress-bar" style="width:{pct}%"></div></div>
            <div class="small"><b>{row['Đã học']}/{row['Tổng buổi']}</b> buổi • Còn {max(remaining, 0)} buổi</div>
            <span class="pill {money_class}">💰 Tiền dạy: {money}</span>
            <span class="pill {status_class}">📌 {status}</span>
            <div class="small" style="margin-top:8px">📅 {row.get('Lịch học','')}</div>
            <div class="small">✅ Điểm danh: {dates if dates else 'Chưa có'}</div>
            <div class="small">📝 {row.get('Ghi chú','')}</div>
        </div>
        """,
        unsafe_allow_html=True
    )


def dashboard_today_html(df, busy_slots):
    today = current_day_name()

    html = """
    <div class="card today-card">
        <div class="card-head">
            <div class="title" style="font-size:18px">Lịch dạy hôm nay</div>
            <div class="link">%s</div>
        </div>
    """ % today

    for ca, time_range in CAS.items():
        slot = f"{today} - {ca}"
        count = len(get_students_by_slot(df, today, ca))
        status, cls, dot = ca_status(time_range)

        if slot in busy_slots:
            label = "Bận"
            pill = "pill-busy"
        else:
            label = status
            pill = f"pill-{cls}"

        html += f"""
        <div class="today-row">
            <div class="today-time">{time_range.replace(' - ', '<br>')}</div>
            <div>
                <div class="today-title">{ca}</div>
                <div class="today-sub">{count} học viên</div>
            </div>
            <div><span class="pill {pill}">{dot} {label}</span></div>
        </div>
        """

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


# =============================
# PAGES
# =============================
def page_dashboard(df, busy_slots):
    topbar()

    left, right = st.columns([1.75, 1])

    with left:
        st.markdown(
            """
            <div class="card info-card">
                <div class="card-head">
                    <div class="title">Thông tin hồ bơi</div>
                    <div class="link">BLT SWIMMING CLUB</div>
                </div>
                <div class="info-grid">
            """,
            unsafe_allow_html=True
        )

        if asset("logo.png").exists():
            st.image(str(asset("logo.png")), width=135)
        else:
            st.markdown("<div class='logo-frame'>BLT</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)

        today_students = sum(
            len(get_students_by_slot(df, current_day_name(), ca))
            for ca in CAS
        )

        current_slots = []
        for ca, time_range in CAS.items():
            status, _, _ = ca_status(time_range)
            if status == "Đang diễn ra":
                current_slots.append(ca)

        with c1:
            st.markdown(
                f"""
                <div class="info-line"><b>Tên:</b> Hồ bơi Bình Lợi Trung</div>
                <div class="info-line"><b>Ngày:</b> {today_full()}</div>
                <div class="info-line"><b>Giờ VN:</b> {now_vn().strftime('%H:%M:%S')}</div>
                <div class="info-line"><b>Trạng thái:</b> Đang hoạt động</div>
                """,
                unsafe_allow_html=True
            )

        with c2:
            st.markdown(
                f"""
                <div class="info-line"><b>Tổng học viên:</b> {len(df)}</div>
                <div class="info-line"><b>Học viên hôm nay:</b> {today_students}</div>
                <div class="info-line"><b>Ca đang diễn ra:</b> {', '.join(current_slots) if current_slots else 'Không có'}</div>
                <div class="info-line"><b>Dữ liệu:</b> CSV nội bộ</div>
                """,
                unsafe_allow_html=True
            )

        st.markdown("</div></div>", unsafe_allow_html=True)

        m1, m2 = st.columns(2)

        with m1:
            almost_done = len(df[(df["Tổng buổi"] - df["Đã học"]) <= 2]) if not df.empty else 0
            metric_box("Sắp hết buổi", almost_done)

        with m2:
            unpaid = len(df[df["Đã nhận tiền dạy"] == "Chưa"]) if not df.empty else 0
            metric_box("Chưa nhận tiền dạy", unpaid, teal=True)

    with right:
        dashboard_today_html(df, busy_slots)

    st.markdown('<div class="quick-grid">', unsafe_allow_html=True)

    quick_items = [
        ("👨‍🎓", "Quản lý học viên"),
        ("📅", "Lịch dạy"),
        ("💰", "Học phí"),
        ("👨‍🏫", "Tiền giáo viên"),
        ("📋", "Điểm danh"),
        ("⚙️", "Cài đặt"),
    ]

    for icon, text in quick_items:
        st.markdown(
            f"""
            <div class="quick-card">
                <div class="quick-icon">{icon}</div>
                <div class="quick-text">{text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


def page_schedule(df, busy_slots):
    topbar()
    st.markdown('<div class="page-title">Lịch dạy</div>', unsafe_allow_html=True)
    st.info(f"Giờ Việt Nam: {now_vn().strftime('%H:%M:%S')} — app tự cập nhật mỗi 60 giây")

    day = st.selectbox("Chọn ngày", DAYS, index=DAYS.index(current_day_name()))

    for ca, time_range in CAS.items():
        slot = f"{day} - {ca}"
        count = len(get_students_by_slot(df, day, ca))
        status, cls, dot = ca_status(time_range)

        if slot in busy_slots:
            label = "Bận"
            pill_class = "pill-busy"
        else:
            label = status
            pill_class = f"pill-{cls}"

        left, right = st.columns([3, 1])

        with left:
            st.markdown(
                f"""
                <div class="slot-card">
                    <div class="slot-title">{ca} • {time_range}</div>
                    <div class="small">{day}</div>
                    <span class="pill {pill_class}">{dot} {label}</span>
                    <span class="pill pill-ok">{count} học viên</span>
                </div>
                """,
                unsafe_allow_html=True
            )

        with right:
            if st.button("Mở", key=f"open_{slot}", use_container_width=True):
                st.session_state["selected_day"] = day
                st.session_state["selected_ca"] = ca

    selected_day = st.session_state.get("selected_day", day)
    selected_ca = st.session_state.get("selected_ca", list(CAS.keys())[0])
    selected_slot = f"{selected_day} - {selected_ca}"

    st.markdown("---")
    st.markdown(
        f"<div class='page-title'>Chi tiết: {selected_slot} • {CAS[selected_ca]}</div>",
        unsafe_allow_html=True
    )

    if selected_slot in busy_slots:
        st.error("Ca này đang bận. Vào Cài đặt để mở lại.")
        return

    class_df = get_students_by_slot(df, selected_day, selected_ca)

    if class_df.empty:
        st.warning("Ca này chưa có học viên.")
        return

    for _, row in class_df.iterrows():
        student_card(row)

    with st.expander("Bảng điểm danh 12 buổi"):
        show_cols = ["Họ tên", "Ngày đăng ký", "Đã học", "Tổng buổi"] + ATTENDANCE_COLS
        st.dataframe(class_df[show_cols], use_container_width=True, hide_index=True)

    checked = st.multiselect(
        "Chọn học viên đã học buổi này",
        class_df["Mã HV"].tolist(),
        format_func=lambda x: class_df.loc[class_df["Mã HV"] == x, "Họ tên"].values[0],
    )

    if st.button("✅ Điểm danh / ghi ngày hôm nay", use_container_width=True):
        for hv_id in checked:
            df = mark_attendance(df, hv_id)

        save_students(df)
        st.success(f"Đã ghi ngày {today_short()} vào điểm danh.")
        st.rerun()


def page_students(df, busy_slots):
    topbar()
    st.markdown('<div class="page-title">Quản lý học viên</div>', unsafe_allow_html=True)

    with st.expander("➕ Thêm học viên mới", expanded=False):
        with st.form("add_student"):
            c1, c2 = st.columns(2)

            with c1:
                name = st.text_input("Họ tên")
                phone = st.text_input("SĐT")
                course = st.selectbox("Khóa học", ["Ếch", "Sải", "Sải ôn ếch", "Khác"])

            with c2:
                register_date = st.date_input("Ngày đăng ký", value=now_vn().date())
                total = st.number_input("Tổng buổi", min_value=1, value=12)
                learned = st.number_input("Đã học", min_value=0, value=0)
                paid = st.checkbox("Đã nhận tiền dạy")

            note = st.text_area("Ghi chú")
            schedule = []

            for day_name in DAYS:
                available = [
                    ca for ca in CAS
                    if f"{day_name} - {ca}" not in busy_slots
                ]

                selected = st.multiselect(day_name, available, key=f"add_{day_name}")
                schedule += [f"{day_name} - {ca}" for ca in selected]

            if st.form_submit_button("Lưu học viên", use_container_width=True):
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
                        "Đã nhận tiền dạy": "Có" if paid else "Chưa",
                        "Ghi chú": note.strip(),
                    }

                    for col in ATTENDANCE_COLS:
                        new[col] = ""

                    save_students(pd.concat([df, pd.DataFrame([new])], ignore_index=True))
                    st.success("Đã thêm học viên.")
                    st.rerun()

    search = st.text_input("Tìm theo tên hoặc số điện thoại")
    show = df.copy()

    if search.strip():
        show = show[
            show["Họ tên"].astype(str).str.contains(search, case=False, na=False)
            | show["SĐT"].astype(str).str.contains(search, case=False, na=False)
        ]

    for _, row in show.iterrows():
        student_card(row)

    with st.expander("📋 Toàn bộ điểm danh"):
        show_cols = ["Mã HV", "Họ tên", "Ngày đăng ký", "Đã học", "Tổng buổi"] + ATTENDANCE_COLS
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="page-title">Sửa / Xóa học viên</div>', unsafe_allow_html=True)

    if not df.empty:
        sid = st.selectbox(
            "Chọn học viên",
            df["Mã HV"].tolist(),
            format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0]
        )

        idx = df[df["Mã HV"] == sid].index[0]

        with st.form("edit_student"):
            c1, c2 = st.columns(2)

            with c1:
                ename = st.text_input("Họ tên", df.loc[idx, "Họ tên"])
                ephone = st.text_input("SĐT", str(df.loc[idx, "SĐT"]))

                course_options = ["Ếch", "Sải", "Sải ôn ếch", "Khác"]
                old_course = df.loc[idx, "Khóa học"]
                ecourse = st.selectbox(
                    "Khóa",
                    course_options,
                    index=course_options.index(old_course) if old_course in course_options else 3
                )
                eregister = st.text_input("Ngày đăng ký", str(df.loc[idx, "Ngày đăng ký"]))

            with c2:
                etotal = st.number_input("Tổng buổi", min_value=1, value=int(df.loc[idx, "Tổng buổi"]))
                elearned = st.number_input("Đã học", min_value=0, value=int(df.loc[idx, "Đã học"]))
                emoney = st.selectbox(
                    "Tiền dạy",
                    ["Chưa", "Có"],
                    index=1 if df.loc[idx, "Đã nhận tiền dạy"] == "Có" else 0
                )

            eschedule = st.text_area("Lịch học", str(df.loc[idx, "Lịch học"]))
            enote = st.text_area("Ghi chú", str(df.loc[idx, "Ghi chú"]))

            if st.form_submit_button("Cập nhật", use_container_width=True):
                df.loc[idx, [
                    "Họ tên", "SĐT", "Khóa học", "Ngày đăng ký", "Lịch học",
                    "Tổng buổi", "Đã học", "Đã nhận tiền dạy", "Ghi chú"
                ]] = [
                    ename, ephone, ecourse, eregister, eschedule,
                    int(etotal), int(elearned), emoney, enote
                ]

                save_students(df)
                st.success("Đã cập nhật.")
                st.rerun()

        confirm = st.checkbox("Tôi xác nhận muốn xóa học viên này")

        if st.button("Xóa học viên", use_container_width=True):
            if confirm:
                save_students(df[df["Mã HV"] != sid])
                st.success("Đã xóa.")
                st.rerun()
            else:
                st.warning("Tick xác nhận trước khi xóa.")


def page_money(df):
    topbar()
    st.markdown('<div class="page-title">Học phí & tiền dạy</div>', unsafe_allow_html=True)

    if df.empty:
        st.warning("Chưa có học viên.")
        return

    unpaid = df[df["Đã nhận tiền dạy"] == "Chưa"]
    paid = df[df["Đã nhận tiền dạy"] == "Có"]

    c1, c2 = st.columns(2)

    with c1:
        metric_box("Chưa nhận", len(unpaid))

    with c2:
        metric_box("Đã nhận", len(paid), teal=True)

    sid = st.selectbox(
        "Chọn học viên",
        df["Mã HV"].tolist(),
        format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0]
    )

    current = df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"].values[0]
    status = st.radio(
        "Trạng thái",
        ["Chưa", "Có"],
        horizontal=True,
        index=1 if current == "Có" else 0
    )

    if st.button("Lưu trạng thái", use_container_width=True):
        df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"] = status
        save_students(df)
        st.success("Đã lưu.")
        st.rerun()

    st.dataframe(
        df[["Họ tên", "Khóa học", "Đã học", "Tổng buổi", "Đã nhận tiền dạy"]],
        use_container_width=True,
        hide_index=True
    )


def page_teacher_fee():
    topbar()
    st.markdown('<div class="page-title">Quản lý tiền thầy</div>', unsafe_allow_html=True)

    tdf = load_teacher_fees()

    st.info("Có học viên mới: bấm +1 học viên. Khi thanh toán thêm: bấm Thanh toán 1 HV.")

    for teacher in ["Đạt", "Long"]:
        idx = tdf[tdf["Thầy"] == teacher].index[0]

        total = int(tdf.loc[idx, "Tổng học viên"])
        paid = int(tdf.loc[idx, "Đã thanh toán"])
        remain = max(total - paid, 0)
        pct = 0 if total == 0 else int(paid / total * 100)

        st.markdown(
            f"""
            <div class="student-card">
                <div class="student-name">👨‍🏫 Thầy {teacher}</div>
                <div class="small">Tổng học viên: <b>{total}</b> • Đã thanh toán: <b>{paid}</b> • Còn lại: <b>{remain}</b></div>
                <div class="progress-wrap"><div class="progress-bar" style="width:{pct}%"></div></div>
            </div>
            """,
            unsafe_allow_html=True
        )

        c1, c2, c3 = st.columns(3)

        with c1:
            if st.button("+1 học viên", key=f"add_{teacher}", use_container_width=True):
                tdf.loc[idx, "Tổng học viên"] = total + 1
                save_teacher_fees(tdf)
                st.rerun()

        with c2:
            if st.button("Thanh toán 1 HV", key=f"pay_{teacher}", use_container_width=True, disabled=paid >= total):
                tdf.loc[idx, "Đã thanh toán"] = min(paid + 1, total)
                save_teacher_fees(tdf)
                st.rerun()

        with c3:
            if st.button("Trừ 1 thanh toán", key=f"undo_{teacher}", use_container_width=True, disabled=paid <= 0):
                tdf.loc[idx, "Đã thanh toán"] = max(paid - 1, 0)
                save_teacher_fees(tdf)
                st.rerun()

        with st.expander(f"Chỉnh tay thầy {teacher}"):
            new_total = st.number_input(
                f"Tổng học viên - {teacher}",
                min_value=0,
                value=total,
                key=f"total_{teacher}"
            )

            new_paid = st.number_input(
                f"Đã thanh toán - {teacher}",
                min_value=0,
                max_value=int(new_total),
                value=min(paid, int(new_total)),
                key=f"paid_{teacher}"
            )

            if st.button(f"Lưu thầy {teacher}", key=f"save_{teacher}", use_container_width=True):
                tdf.loc[idx, "Tổng học viên"] = int(new_total)
                tdf.loc[idx, "Đã thanh toán"] = int(new_paid)
                save_teacher_fees(tdf)
                st.rerun()

    tdf["Còn lại"] = tdf["Tổng học viên"] - tdf["Đã thanh toán"]
    st.dataframe(tdf, use_container_width=True, hide_index=True)


def page_settings(busy_slots):
    topbar()
    st.markdown('<div class="page-title">Cài đặt lịch bận</div>', unsafe_allow_html=True)

    new_slots = set()

    for day in DAYS:
        st.markdown(f"### {day}")
        cols = st.columns(2)

        for i, ca in enumerate(CAS):
            slot = f"{day} - {ca}"

            with cols[i % 2]:
                if st.checkbox(f"{ca} • {CAS[ca]}", value=slot in busy_slots, key=f"busy_{slot}"):
                    new_slots.add(slot)

    if st.button("Lưu lịch bận", use_container_width=True):
        save_busy_slots(new_slots)
        st.success("Đã lưu lịch bận.")
        st.rerun()


# =============================
# MAIN
# =============================
def main():
    icon = str(asset("logo.png")) if asset("logo.png").exists() else "🏊"

    st.set_page_config(
        page_title="BLT Manager",
        page_icon=icon,
        layout="wide"
    )

    apply_style()

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
            [
                "🏠 Dashboard",
                "📅 Lịch dạy",
                "👨‍🎓 Học viên",
                "💰 Học phí",
                "👨‍🏫 Tiền thầy",
                "⚙️ Cài đặt",
            ],
            label_visibility="collapsed"
        )

        st.caption("UTH style • Mobile-first • GMT+7")

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
