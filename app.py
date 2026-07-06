import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime, date
from zoneinfo import ZoneInfo
import calendar

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

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

def resolve(name):
    data_file = DATA_DIR / name
    root_file = BASE / name
    if data_file.exists():
        return data_file
    if root_file.exists():
        return root_file
    return data_file

DATA_FILE = resolve("hoc_vien.csv")
BUSY_FILE = resolve("lich_ban.csv")
TEACHER_FILE = resolve("hoc_phi_thay.csv")

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
        missing = df["Mã HV"].isna()
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
    pd.DataFrame({"Slot": sorted(list(slots))}).to_csv(BUSY_FILE, index=False, encoding="utf-8-sig")

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
            df = pd.concat([df, pd.DataFrame([{"Thầy": teacher, "Tổng học viên": 0, "Đã thanh toán": 0}])], ignore_index=True)
    df["Tổng học viên"] = pd.to_numeric(df["Tổng học viên"], errors="coerce").fillna(0).astype(int)
    df["Đã thanh toán"] = pd.to_numeric(df["Đã thanh toán"], errors="coerce").fillna(0).astype(int)
    df.loc[df["Đã thanh toán"] > df["Tổng học viên"], "Đã thanh toán"] = df["Tổng học viên"]
    return df[TEACHER_COLUMNS]

def save_teacher_fees(df):
    df.to_csv(TEACHER_FILE, index=False, encoding="utf-8-sig")

def make_student_id(df):
    if df.empty:
        return 1
    mx = pd.to_numeric(df["Mã HV"], errors="coerce").max()
    return 1 if pd.isna(mx) else int(mx) + 1

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
        val = str(df.loc[idx, col]).strip()
        if val == "" or val.lower() == "nan":
            df.loc[idx, col] = today_short()
            break
    df.loc[idx, "Đã học"] = learned + 1
    return df

def progress_pct(row):
    total = max(int(row.get("Tổng buổi", 12)), 1)
    done = int(row.get("Đã học", 0))
    return min(100, int(done / total * 100))

def asset(name):
    return ASSETS / name

def show_asset(name):
    path = asset(name)
    if path.exists():
        st.image(str(path), use_container_width=True)

def apply_style():
    st.markdown("""
    <style>
    :root{
        --teal:#008f8f;
        --teal-dark:#007a7a;
        --bg:#e9eef2;
        --card:#ffffff;
        --text:#3f5663;
        --muted:#6b7f8a;
        --red:#ef4444;
        --green:#22c55e;
        --yellow:#f59e0b;
        --blue:#3b82f6;
    }
    .stApp{background:#e9eef2;}
    .block-container{padding-top:1rem;max-width:1260px;}
    [data-testid="stSidebar"]{background:#ffffff;}
    [data-testid="stSidebar"] *{color:#314b57;}
    .topbar{
        background:white;
        border-radius:0 0 22px 22px;
        padding:14px 22px;
        display:flex;
        align-items:center;
        justify-content:space-between;
        box-shadow:0 8px 22px rgba(30,50,70,.08);
        margin-bottom:18px;
    }
    .brand{display:flex;align-items:center;gap:14px;}
    .hamb{font-size:28px;color:var(--teal);font-weight:900;}
    .brand-title{font-size:28px;font-weight:950;color:var(--teal);}
    .brand-sub{font-size:12px;color:#e11d48;font-weight:900;letter-spacing:1px;}
    .user-chip{display:flex;align-items:center;gap:10px;font-weight:850;color:#333;}
    .page-title{color:var(--teal);font-size:26px;font-weight:950;margin-bottom:14px;}
    .card{
        background:#fff;
        border-radius:18px;
        padding:24px;
        box-shadow:0 8px 22px rgba(40,60,80,.04);
        margin-bottom:18px;
    }
    .student-info-card{min-height:250px;}
    .info-grid{display:grid;grid-template-columns:150px 1fr 1fr;gap:22px;align-items:center;}
    .avatar-box{width:135px;height:170px;border:1.5px solid var(--teal);border-radius:8px;overflow:hidden;display:flex;align-items:center;justify-content:center;background:#eef9f9;}
    .logo-img{max-width:100%;max-height:100%;}
    .info-line{font-size:16px;color:var(--text);margin:13px 0;font-weight:600;}
    .info-line b{color:#5a6870;}
    .mini-card{
        background:#fff;
        border-radius:18px;
        padding:24px;
        box-shadow:0 8px 22px rgba(40,60,80,.04);
        min-height:130px;
    }
    .mini-card.teal{background:var(--teal);color:white;}
    .mini-title{font-weight:900;font-size:18px;}
    .mini-number{font-size:34px;font-weight:950;margin-top:8px;}
    .mini-link{font-weight:900;color:red;margin-top:4px;}
    .mini-card.teal .mini-link{color:white;}
    .calendar-card{min-height:420px;}
    .cal-head{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;}
    .month-box{border:1px solid #ccd5dc;border-radius:6px;padding:8px 14px;color:#333;background:#fff;}
    .cal-grid{display:grid;grid-template-columns:repeat(7,1fr);gap:6px;}
    .cal-day-name{font-weight:900;text-align:center;color:#657580;padding:8px;}
    .cal-day-name.sun{color:#ff5b00;}
    .cal-cell{height:54px;border-radius:9px;background:#fff;display:flex;align-items:center;justify-content:center;position:relative;font-weight:700;color:#111;}
    .cal-cell.has{background:#b7e3e3;}
    .cal-cell.today{outline:2px solid var(--teal);background:#fff;}
    .dot{position:absolute;bottom:8px;width:7px;height:7px;border-radius:50%;}
    .dot.green{background:#84cc16;left:calc(50% - 10px);}
    .dot.blue{background:#60a5fa;left:calc(50% + 3px);}
    .dot.red{background:#e11d48;left:calc(50% - 3px);}
    .quick-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:18px;}
    .quick-card{background:#fff;border-radius:16px;padding:24px;text-align:center;box-shadow:0 8px 22px rgba(40,60,80,.04);min-height:130px;}
    .quick-icon{font-size:32px;color:var(--teal);font-weight:900;}
    .quick-text{font-size:16px;font-weight:900;color:#697984;margin-top:10px;}
    .slot-card,.student-card{
        background:white;
        border-radius:18px;
        padding:20px;
        box-shadow:0 8px 22px rgba(40,60,80,.05);
        margin-bottom:14px;
    }
    .slot-title,.student-name{font-size:22px;font-weight:950;color:#0a4f93;}
    .small{font-size:15px;color:#607887;}
    .pill{display:inline-block;padding:7px 12px;border-radius:999px;font-size:13px;font-weight:900;margin:7px 4px 0 0;}
    .pill-now{background:#fff3bf;color:#7a5c00;}
    .pill-soon{background:#dff6ff;color:#005f8f;}
    .pill-past{background:#e9ecef;color:#495057;}
    .pill-busy{background:#ffe3e8;color:#b00020;}
    .pill-ok{background:#d8fbe0;color:#087f23;}
    .pill-warn{background:#fff3bf;color:#7a5c00;}
    .progress-wrap{background:#e8f6fb;height:12px;border-radius:999px;overflow:hidden;margin:12px 0 8px;}
    .progress-bar{height:12px;background:linear-gradient(90deg,#00b4d8,#22c55e);}
    div.stButton > button{border-radius:12px;font-weight:900;border:1px solid #d6e5ea;}
    @media(max-width:900px){
        .info-grid{grid-template-columns:1fr;}
        .quick-grid{grid-template-columns:repeat(2,1fr);}
        .cal-cell{height:44px;}
        .brand-title{font-size:20px;}
    }
    </style>
    """, unsafe_allow_html=True)

def topbar():
    logo_path = asset("logo.png")
    if logo_path.exists():
        logo_html = f"<img src='data:image/png;base64,{logo_path.read_bytes().hex()}' />"
    st.markdown("""
    <div class="topbar">
        <div class="brand">
            <div class="hamb">☰</div>
            <div>
                <div class="brand-title">BLT SWIMMING</div>
                <div class="brand-sub">SWIM MANAGEMENT SYSTEM</div>
            </div>
        </div>
        <div class="user-chip">🏊 Hồ bơi Bình Lợi Trung ▾</div>
    </div>
    """, unsafe_allow_html=True)

def metric_box(title, number, link="Xem chi tiết", teal=False):
    cls = "mini-card teal" if teal else "mini-card"
    st.markdown(f"""
    <div class="{cls}">
        <div class="mini-title">{title}</div>
        <div class="mini-number">{number}</div>
        <div class="mini-link">{link}</div>
    </div>
    """, unsafe_allow_html=True)

def student_card(row):
    pct = progress_pct(row)
    remaining = int(row["Tổng buổi"]) - int(row["Đã học"])
    money = row.get("Đã nhận tiền dạy", "Chưa")
    money_cls = "pill-ok" if money == "Có" else "pill-warn"
    status_cls = "pill-ok" if remaining <= 0 else ("pill-warn" if remaining <= 2 else "pill-soon")
    status = "Đủ buổi" if remaining <= 0 else ("Sắp hết" if remaining <= 2 else "Đang học")
    dates = " • ".join([str(row[c]) for c in ATTENDANCE_COLS if str(row[c]).strip() not in ["", "nan"]])
    st.markdown(f"""
    <div class="student-card">
        <div class="student-name">👤 {row['Họ tên']}</div>
        <div class="small">📱 {row.get('SĐT','')} • 🏊 {row.get('Khóa học','')} • 🗓️ ĐK: {row.get('Ngày đăng ký','')}</div>
        <div class="progress-wrap"><div class="progress-bar" style="width:{pct}%"></div></div>
        <div class="small"><b>{row['Đã học']}/{row['Tổng buổi']}</b> buổi • Còn {max(remaining,0)} buổi</div>
        <span class="pill {money_cls}">💰 Tiền dạy: {money}</span>
        <span class="pill {status_cls}">📌 {status}</span>
        <div class="small" style="margin-top:8px">📅 {row.get('Lịch học','')}</div>
        <div class="small">✅ Điểm danh: {dates if dates else 'Chưa có'}</div>
        <div class="small">📝 {row.get('Ghi chú','')}</div>
    </div>
    """, unsafe_allow_html=True)

def calendar_html(df):
    now = now_vn()
    year, month = now.year, now.month
    first_weekday, days_in_month = calendar.monthrange(year, month)
    # Python Monday=0. Convert to Sunday-first display
    start_offset = (first_weekday + 1) % 7
    today = now.day

    html = """
    <div class="card calendar-card">
      <div class="cal-head">
        <div class="page-title" style="font-size:18px;margin:0">Lịch theo tháng</div>
        <div class="month-box">tháng %s %s</div>
      </div>
      <div class="cal-grid">
    """ % (month, year)

    names = ["CN", "T2", "T3", "T4", "T5", "T6", "T7"]
    for n in names:
        html += f"<div class='cal-day-name {'sun' if n=='CN' else ''}'>{n}</div>"

    for _ in range(start_offset):
        html += "<div class='cal-cell'></div>"

    for d in range(1, days_in_month + 1):
        has = "has" if d % 2 in [0, 1] else ""
        today_cls = "today" if d == today else ""
        dots = ""
        if d % 3 == 0: dots += "<span class='dot blue'></span>"
        if d % 2 == 0: dots += "<span class='dot green'></span>"
        if d % 5 == 0: dots += "<span class='dot red'></span>"
        html += f"<div class='cal-cell {has} {today_cls}'>{d}{dots}</div>"

    html += "</div></div>"
    st.markdown(html, unsafe_allow_html=True)

def page_dashboard(df, busy_slots):
    topbar()
    left, right = st.columns([1.75, 1])

    with left:
        st.markdown("""
        <div class="card student-info-card">
          <div style="display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #ddd;padding-bottom:14px;margin-bottom:18px">
            <div class="page-title" style="margin:0">Thông tin trung tâm</div>
            <div style="color:#008f8f;font-weight:900">BLT SWIMMING CLUB</div>
          </div>
          <div class="info-grid">
        """, unsafe_allow_html=True)
        if asset("logo.png").exists():
            st.image(str(asset("logo.png")), width=135)
        else:
            st.markdown("<div class='avatar-box'>BLT</div>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"""
            <div class="info-line"><b>Mã hệ thống:</b> BLT-POOL</div>
            <div class="info-line"><b>Tên:</b> Hồ bơi Bình Lợi Trung</div>
            <div class="info-line"><b>Ngày:</b> {today_full()}</div>
            <div class="info-line"><b>Giờ VN:</b> {now_vn().strftime('%H:%M:%S')}</div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="info-line"><b>Học viên:</b> {len(df)}</div>
            <div class="info-line"><b>Ca học:</b> {len(CAS)}</div>
            <div class="info-line"><b>Dữ liệu:</b> CSV nội bộ</div>
            <div class="info-line"><b>Trạng thái:</b> Đang hoạt động</div>
            """, unsafe_allow_html=True)
        st.markdown("</div></div>", unsafe_allow_html=True)

        c3, c4 = st.columns(2)
        today_students = sum(len(get_students_by_slot(df, current_day_name(), ca)) for ca in CAS)
        with c3:
            metric_box("Thông báo / sự kiện", 0)
        with c4:
            metric_box("Lịch học trong ngày", today_students, teal=True)

    with right:
        calendar_html(df)

    st.markdown('<div class="quick-grid">', unsafe_allow_html=True)
    quick_items = [
        ("👨‍🎓", "Quản lý học viên"),
        ("📅", "Lịch dạy"),
        ("💰", "Học phí"),
        ("👨‍🏫", "Tiền thầy"),
        ("⚙️", "Cài đặt lịch bận"),
        ("📋", "Điểm danh 12 buổi"),
    ]
    for icon, text in quick_items:
        st.markdown(f"<div class='quick-card'><div class='quick-icon'>{icon}</div><div class='quick-text'>{text}</div></div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

def page_schedule(df, busy_slots):
    topbar()
    st.markdown('<div class="page-title">Lịch dạy</div>', unsafe_allow_html=True)
    st.info(f"Giờ Việt Nam: {now_vn().strftime('%H:%M:%S')} — app tự cập nhật mỗi 60 giây")

    day = st.selectbox("Chọn ngày", DAYS, index=DAYS.index(current_day_name()))

    for ca, tr in CAS.items():
        slot = f"{day} - {ca}"
        status, cls, dot = ca_status(tr)
        count = len(get_students_by_slot(df, day, ca))
        busy = slot in busy_slots
        label = "Bận" if busy else status
        pill_class = "pill-busy" if busy else f"pill-{cls}"

        left, right = st.columns([3, 1])
        with left:
            st.markdown(f"""
            <div class="slot-card">
                <div class="slot-title">{ca} • {tr}</div>
                <div class="small">{day}</div>
                <span class="pill {pill_class}">{dot} {label}</span>
                <span class="pill pill-ok">{count} học viên</span>
            </div>
            """, unsafe_allow_html=True)
        with right:
            if st.button("Mở", key=f"open_{slot}", use_container_width=True):
                st.session_state["selected_day"] = day
                st.session_state["selected_ca"] = ca

    selected_day = st.session_state.get("selected_day", day)
    selected_ca = st.session_state.get("selected_ca", list(CAS.keys())[0])
    selected_slot = f"{selected_day} - {selected_ca}"

    st.markdown("---")
    st.markdown(f"<div class='page-title'>Chi tiết: {selected_slot} • {CAS[selected_ca]}</div>", unsafe_allow_html=True)

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
            for day in DAYS:
                available = [ca for ca in CAS if f"{day} - {ca}" not in busy_slots]
                selected = st.multiselect(day, available, key=f"add_{day}")
                schedule += [f"{day} - {ca}" for ca in selected]

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
        cols = ["Mã HV", "Họ tên", "Ngày đăng ký", "Đã học", "Tổng buổi"] + ATTENDANCE_COLS
        st.dataframe(df[cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="page-title">Sửa / Xóa học viên</div>', unsafe_allow_html=True)

    if not df.empty:
        sid = st.selectbox("Chọn học viên", df["Mã HV"].tolist(), format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0])
        idx = df[df["Mã HV"] == sid].index[0]

        with st.form("edit_student"):
            c1, c2 = st.columns(2)
            with c1:
                ename = st.text_input("Họ tên", df.loc[idx, "Họ tên"])
                ephone = st.text_input("SĐT", str(df.loc[idx, "SĐT"]))
                options = ["Ếch", "Sải", "Sải ôn ếch", "Khác"]
                old_course = df.loc[idx, "Khóa học"]
                ecourse = st.selectbox("Khóa", options, index=options.index(old_course) if old_course in options else 3)
                ereg = st.text_input("Ngày đăng ký", str(df.loc[idx, "Ngày đăng ký"]))
            with c2:
                etotal = st.number_input("Tổng buổi", min_value=1, value=int(df.loc[idx, "Tổng buổi"]))
                elearned = st.number_input("Đã học", min_value=0, value=int(df.loc[idx, "Đã học"]))
                emoney = st.selectbox("Tiền dạy", ["Chưa", "Có"], index=1 if df.loc[idx, "Đã nhận tiền dạy"] == "Có" else 0)
            eschedule = st.text_area("Lịch học", str(df.loc[idx, "Lịch học"]))
            enote = st.text_area("Ghi chú", str(df.loc[idx, "Ghi chú"]))

            if st.form_submit_button("Cập nhật", use_container_width=True):
                df.loc[idx, ["Họ tên", "SĐT", "Khóa học", "Ngày đăng ký", "Lịch học", "Tổng buổi", "Đã học", "Đã nhận tiền dạy", "Ghi chú"]] = [
                    ename, ephone, ecourse, ereg, eschedule, int(etotal), int(elearned), emoney, enote
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

    sid = st.selectbox("Chọn học viên", df["Mã HV"].tolist(), format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0])
    current = df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"].values[0]
    status = st.radio("Trạng thái", ["Chưa", "Có"], horizontal=True, index=1 if current == "Có" else 0)
    if st.button("Lưu trạng thái", use_container_width=True):
        df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"] = status
        save_students(df)
        st.success("Đã lưu.")
        st.rerun()
    st.dataframe(df[["Họ tên", "Khóa học", "Đã học", "Tổng buổi", "Đã nhận tiền dạy"]], use_container_width=True, hide_index=True)

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

        st.markdown(f"""
        <div class="student-card">
            <div class="student-name">👨‍🏫 Thầy {teacher}</div>
            <div class="small">Tổng học viên: <b>{total}</b> • Đã thanh toán: <b>{paid}</b> • Còn lại: <b>{remain}</b></div>
            <div class="progress-wrap"><div class="progress-bar" style="width:{pct}%"></div></div>
        </div>
        """, unsafe_allow_html=True)

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
            ntotal = st.number_input(f"Tổng học viên - {teacher}", min_value=0, value=total, key=f"total_{teacher}")
            npaid = st.number_input(f"Đã thanh toán - {teacher}", min_value=0, max_value=int(ntotal), value=min(paid, int(ntotal)), key=f"paid_{teacher}")
            if st.button(f"Lưu thầy {teacher}", key=f"save_{teacher}", use_container_width=True):
                tdf.loc[idx, "Tổng học viên"] = int(ntotal)
                tdf.loc[idx, "Đã thanh toán"] = int(npaid)
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

def main():
    icon = str(asset("logo.png")) if asset("logo.png").exists() else "🏊"
    st.set_page_config(page_title="BLT Manager", page_icon=icon, layout="wide")
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
            ["🏠 Dashboard", "📅 Lịch dạy", "👨‍🎓 Học viên", "💰 Học phí", "👨‍🏫 Tiền thầy", "⚙️ Cài đặt"],
            label_visibility="collapsed",
        )
        st.caption("Giao diện tham khảo UTH • GMT+7")

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
