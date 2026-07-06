import streamlit as st
import pandas as pd
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

BASE = Path(__file__).parent
DATA_ROOT = BASE
DATA_DIR = BASE / "data"
ASSETS = BASE / "assets"

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
COLUMNS = ["Mã HV", "Họ tên", "SĐT", "Khóa học", "Lịch học", "Tổng buổi", "Đã học", "Đã nhận tiền dạy", "Ghi chú"]
VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")


def resolve_file(name: str) -> Path:
    root_file = DATA_ROOT / name
    data_file = DATA_DIR / name
    if root_file.exists():
        return root_file
    if data_file.exists():
        return data_file
    return root_file

DATA_FILE = resolve_file("hoc_vien.csv")
BUSY_FILE = resolve_file("lich_ban.csv")


def load_students() -> pd.DataFrame:
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=COLUMNS)
    for col in COLUMNS:
        if col not in df.columns:
            if col == "Tổng buổi": df[col] = 12
            elif col == "Đã học": df[col] = 0
            elif col == "Đã nhận tiền dạy": df[col] = "Chưa"
            else: df[col] = ""
    if len(df) > 0:
        df["Mã HV"] = pd.to_numeric(df["Mã HV"], errors="coerce")
        missing = df["Mã HV"].isna()
        df.loc[missing, "Mã HV"] = range(1, int(missing.sum()) + 1)
        df["Mã HV"] = df["Mã HV"].astype(int)
        df["Tổng buổi"] = pd.to_numeric(df["Tổng buổi"], errors="coerce").fillna(12).astype(int)
        df["Đã học"] = pd.to_numeric(df["Đã học"], errors="coerce").fillna(0).astype(int)
        df["Đã nhận tiền dạy"] = df["Đã nhận tiền dạy"].fillna("Chưa").replace({True: "Có", False: "Chưa"})
    return df[COLUMNS]


def save_students(df: pd.DataFrame):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def load_busy_slots() -> set:
    if BUSY_FILE.exists():
        bdf = pd.read_csv(BUSY_FILE)
        if "Slot" in bdf.columns:
            return set(bdf["Slot"].dropna().astype(str).tolist())
    return set()


def save_busy_slots(slots: set):
    pd.DataFrame({"Slot": sorted(list(slots))}).to_csv(BUSY_FILE, index=False, encoding="utf-8-sig")


def make_student_id(df):
    if df.empty: return 1
    mx = pd.to_numeric(df["Mã HV"], errors="coerce").max()
    return 1 if pd.isna(mx) else int(mx) + 1


def get_students_by_slot(df, day, ca):
    if df.empty: return pd.DataFrame(columns=COLUMNS)
    slot = f"{day} - {ca}"
    return df[df["Lịch học"].astype(str).str.contains(slot, na=False, regex=False)].copy()


def ca_status(time_range):
    now = datetime.now(VN_TZ).time()
    start_s, end_s = time_range.split(" - ")
    start = datetime.strptime(start_s, "%H:%M").time()
    end = datetime.strptime(end_s, "%H:%M").time()
    if start <= now < end: return "Đang diễn ra", "🟡", "now"
    if now < start: return "Sắp tới", "🔵", "soon"
    return "Đã qua", "⚫", "past"


def current_vn_day():
    return DAYS[datetime.now(VN_TZ).weekday()]


def progress_pct(row):
    total = max(int(row.get("Tổng buổi", 12)), 1)
    done = int(row.get("Đã học", 0))
    return min(100, int(done / total * 100))


def render_css():
    bg = ASSETS / "background.jpg"
    bg_css = f"background-image: linear-gradient(rgba(246,251,255,.88), rgba(246,251,255,.95)), url('{bg.as_posix()}');" if bg.exists() else ""
    st.markdown(f"""
    <style>
    .stApp {{ {bg_css} background-size: cover; background-attachment: fixed; }}
    .block-container {{ padding-top: 1rem; max-width: 1200px; }}
    [data-testid="stSidebar"] {{ background: linear-gradient(180deg,#023e8a,#0077b6); }}
    [data-testid="stSidebar"] * {{ color: white !important; }}
    .hero {{ background: linear-gradient(135deg, rgba(0,119,182,.96), rgba(0,180,216,.88)); padding: 22px; border-radius: 28px; color:white; box-shadow: 0 16px 35px rgba(0,73,115,.22); margin-bottom:18px; }}
    .hero h1 {{ margin:0; font-size: 34px; }}
    .hero p {{ margin:.35rem 0 0; opacity:.96; font-size: 16px; }}
    .metric-card {{ background: rgba(255,255,255,.84); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,.8); border-radius: 24px; padding: 18px; box-shadow: 0 12px 30px rgba(2,62,138,.10); }}
    .metric-card .label {{ color:#426579; font-weight:700; font-size:13px; }}
    .metric-card .value {{ color:#023e8a; font-size:32px; font-weight:900; margin-top:3px; }}
    .slot-card {{ background:white; border-radius:22px; padding:16px; margin-bottom:12px; box-shadow: 0 10px 24px rgba(2,62,138,.10); border: 1px solid #e6f5fb; }}
    .slot-title {{ font-weight:900; font-size:18px; color:#023e8a; }}
    .slot-sub {{ color:#5f7481; font-size:13px; }}
    .pill {{ display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:800; margin-top:8px; }}
    .pill-now {{ background:#fff3bf; color:#7a5c00; }} .pill-soon {{ background:#dff6ff; color:#005f8f; }} .pill-past {{ background:#e9ecef; color:#495057; }} .pill-busy {{ background:#ffe3e8; color:#b00020; }} .pill-ok {{ background:#d8fbe0; color:#087f23; }} .pill-warn {{ background:#fff3bf; color:#7a5c00; }}
    .student-card {{ background: rgba(255,255,255,.92); border-radius:22px; padding:16px; margin-bottom:12px; box-shadow:0 10px 24px rgba(2,62,138,.10); border:1px solid #edf8fc; }}
    .student-name {{ font-weight:900; font-size:19px; color:#023e8a; }}
    .progress-wrap {{ background:#e9f6fb; height:10px; border-radius:999px; overflow:hidden; margin:10px 0 6px; }}
    .progress-bar {{ height:10px; background:linear-gradient(90deg,#00b4d8,#2dc653); border-radius:999px; }}
    .small {{ color:#567; font-size:13px; }}
    .section-title {{ font-size:22px; font-weight:900; color:#023e8a; margin:18px 0 10px; }}
    div.stButton > button {{ border-radius: 16px; font-weight: 800; border: 1px solid #d9f1fa; box-shadow: 0 6px 16px rgba(0,119,182,.08); }}
    div.stButton > button:hover {{ border-color:#00b4d8; color:#0077b6; }}
    </style>
    """, unsafe_allow_html=True)


def hero(title, subtitle):
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p></div>", unsafe_allow_html=True)


def metric_card(label, value, icon):
    st.markdown(f"<div class='metric-card'><div class='label'>{icon} {label}</div><div class='value'>{value}</div></div>", unsafe_allow_html=True)

def image_banner(filename, height=220):
    path = ASSETS / filename
    if path.exists():
        st.markdown(
            f"""
            <div style="
                width:100%;
                height:{height}px;
                border-radius:28px;
                overflow:hidden;
                margin: 10px 0 18px 0;
                box-shadow:0 16px 35px rgba(2,62,138,.16);
                background-image: linear-gradient(90deg, rgba(2,62,138,.25), rgba(0,180,216,.10)), url('{path.as_posix()}');
                background-size: cover;
                background-position: center;
            "></div>
            """,
            unsafe_allow_html=True
        )


def student_card(row):
    pct = progress_pct(row)
    remaining = int(row["Tổng buổi"]) - int(row["Đã học"])
    money = row.get("Đã nhận tiền dạy", "Chưa")
    money_class = "pill-ok" if money == "Có" else "pill-warn"
    done_class = "pill-ok" if remaining <= 0 else ("pill-warn" if remaining <= 2 else "pill-soon")
    st.markdown(f"""
    <div class='student-card'>
      <div class='student-name'>👤 {row['Họ tên']}</div>
      <div class='small'>📱 {row.get('SĐT','')} &nbsp; • &nbsp; 🏊 {row.get('Khóa học','')}</div>
      <div class='progress-wrap'><div class='progress-bar' style='width:{pct}%'></div></div>
      <div class='small'><b>{row['Đã học']}/{row['Tổng buổi']}</b> buổi • Còn {max(remaining,0)} buổi</div>
      <span class='pill {money_class}'>💰 Tiền dạy: {money}</span>
      <span class='pill {done_class}'>📌 {'Đủ buổi' if remaining <= 0 else 'Sắp hết' if remaining <=2 else 'Đang học'}</span>
      <div class='small' style='margin-top:8px'>📅 {row.get('Lịch học','')}</div>
      <div class='small'>📝 {row.get('Ghi chú','')}</div>
    </div>
    """, unsafe_allow_html=True)


def page_dashboard(df, busy_slots):
    now = datetime.now(VN_TZ)
    hero("🏊 BLT Swimming Club", f"Dashboard nhanh • {now.strftime('%H:%M:%S')} GMT+7 • {now.strftime('%d/%m/%Y')}")
    image_banner("dashboard.jpg", 230)
    if (ASSETS / "banner.jpg").exists():
        st.image(str(ASSETS / "banner.jpg"), use_container_width=True)
    today = current_vn_day()
    today_students = sum(len(get_students_by_slot(df, today, ca)) for ca in CAS)
    almost_done = len(df[(df["Tổng buổi"] - df["Đã học"]) <= 2]) if not df.empty else 0
    cols = st.columns(4)
    with cols[0]: metric_card("Tổng học viên", len(df), "👨‍🎓")
    with cols[1]: metric_card("HV hôm nay", today_students, "📅")
    with cols[2]: metric_card("Sắp hết buổi", almost_done, "⚠️")
    with cols[3]: metric_card("Chưa nhận tiền", len(df[df["Đã nhận tiền dạy"] == "Chưa"]) if not df.empty else 0, "💰")
    st.markdown("<div class='section-title'>Lịch hôm nay</div>", unsafe_allow_html=True)
    for ca, tr in CAS.items():
        slot = f"{today} - {ca}"
        status, icon, cls = ca_status(tr)
        count = len(get_students_by_slot(df, today, ca))
        busy = slot in busy_slots
        st.markdown(f"<div class='slot-card'><div class='slot-title'>{ca} • {tr}</div><div class='slot-sub'>{today}</div><span class='pill {'pill-busy' if busy else 'pill-'+cls}'>{'🔴 Bận' if busy else icon+' '+status}</span> <span class='pill pill-ok'>{count} học viên</span></div>", unsafe_allow_html=True)


def page_schedule(df, busy_slots):
    hero("📅 Lịch dạy", "Bấm vào card ca học để xem học viên và điểm danh nhanh")
    image_banner("pool.jpg", 210)
    now = datetime.now(VN_TZ)
    st.info(f"🕒 Giờ Việt Nam: {now.strftime('%H:%M:%S')} — tự cập nhật mỗi 60 giây")
    day = st.segmented_control("Chọn ngày", DAYS, default=current_vn_day()) if hasattr(st, "segmented_control") else st.selectbox("Chọn ngày", DAYS, index=DAYS.index(current_vn_day()))
    st.markdown("<div class='section-title'>Các ca trong ngày</div>", unsafe_allow_html=True)
    for ca, tr in CAS.items():
        slot = f"{day} - {ca}"
        status, icon, cls = ca_status(tr)
        count = len(get_students_by_slot(df, day, ca))
        busy = slot in busy_slots
        label = f"{'🔴 Bận' if busy else icon + ' ' + status} • {count} HV"
        c1, c2 = st.columns([3,1])
        with c1:
            st.markdown(f"<div class='slot-card'><div class='slot-title'>{ca} • {tr}</div><div class='slot-sub'>{day}</div><span class='pill {'pill-busy' if busy else 'pill-'+cls}'>{label}</span></div>", unsafe_allow_html=True)
        with c2:
            if st.button("Mở", key=f"open_{slot}", use_container_width=True):
                st.session_state["selected_slot"] = slot
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
    checked_ids = st.multiselect("Chọn học viên đã học buổi này", class_df["Mã HV"].tolist(), format_func=lambda x: class_df.loc[class_df["Mã HV"] == x, "Họ tên"].values[0])
    if st.button("✅ Điểm danh / Tăng buổi", use_container_width=True):
        for hv_id in checked_ids:
            idx = df[df["Mã HV"] == hv_id].index
            if len(idx) > 0:
                idx = idx[0]
                if int(df.loc[idx, "Đã học"]) < int(df.loc[idx, "Tổng buổi"]):
                    df.loc[idx, "Đã học"] += 1
        save_students(df)
        st.success("Đã cập nhật số buổi.")
        st.rerun()


def page_students(df, busy_slots):
    hero("👨‍🎓 Học viên", "Thêm, tìm kiếm, sửa và xóa học viên trên cùng một màn hình")
    image_banner("student.jpg", 210)
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
                paid = st.checkbox("Đã nhận tiền dạy")
            note = st.text_area("Ghi chú")
            schedule = []
            for day in DAYS:
                av = [ca for ca in CAS if f"{day} - {ca}" not in busy_slots]
                selected = st.multiselect(day, av, key=f"add_{day}")
                schedule += [f"{day} - {ca}" for ca in selected]
            submitted = st.form_submit_button("💾 Lưu học viên", use_container_width=True)
            if submitted:
                if not name.strip(): st.warning("Nhập họ tên trước.")
                elif not schedule: st.warning("Chọn ít nhất một ca học.")
                else:
                    new = {"Mã HV": make_student_id(df), "Họ tên": name.strip(), "SĐT": phone.strip(), "Khóa học": course, "Lịch học": ", ".join(schedule), "Tổng buổi": int(total), "Đã học": int(learned), "Đã nhận tiền dạy": "Có" if paid else "Chưa", "Ghi chú": note.strip()}
                    save_students(pd.concat([df, pd.DataFrame([new])], ignore_index=True))
                    st.success("Đã thêm học viên.")
                    st.rerun()
    search = st.text_input("🔍 Tìm theo tên hoặc số điện thoại")
    show = df.copy()
    if search.strip():
        show = show[show["Họ tên"].astype(str).str.contains(search, case=False, na=False) | show["SĐT"].astype(str).str.contains(search, case=False, na=False)]
    for _, row in show.iterrows():
        student_card(row)
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
                ecourse = st.selectbox("Khóa", ["Ếch", "Sải", "Sải ôn ếch", "Khác"], index=["Ếch", "Sải", "Sải ôn ếch", "Khác"].index(df.loc[idx, "Khóa học"]) if df.loc[idx, "Khóa học"] in ["Ếch", "Sải", "Sải ôn ếch", "Khác"] else 3)
            with c2:
                etotal = st.number_input("Tổng buổi", min_value=1, value=int(df.loc[idx, "Tổng buổi"]))
                elearned = st.number_input("Đã học", min_value=0, value=int(df.loc[idx, "Đã học"]))
                emoney = st.selectbox("Tiền dạy", ["Chưa", "Có"], index=1 if df.loc[idx, "Đã nhận tiền dạy"] == "Có" else 0)
            eschedule = st.text_area("Lịch học", str(df.loc[idx, "Lịch học"]))
            enote = st.text_area("Ghi chú", str(df.loc[idx, "Ghi chú"]))
            save_btn = st.form_submit_button("💾 Cập nhật", use_container_width=True)
            if save_btn:
                df.loc[idx, ["Họ tên","SĐT","Khóa học","Lịch học","Tổng buổi","Đã học","Đã nhận tiền dạy","Ghi chú"]] = [ename, ephone, ecourse, eschedule, int(etotal), int(elearned), emoney, enote]
                save_students(df)
                st.success("Đã cập nhật.")
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
        st.warning("Chưa có học viên."); return
    unpaid = df[df["Đã nhận tiền dạy"] == "Chưa"]
    paid = df[df["Đã nhận tiền dạy"] == "Có"]
    c1, c2 = st.columns(2)
    with c1: metric_card("Chưa nhận", len(unpaid), "🔴")
    with c2: metric_card("Đã nhận", len(paid), "🟢")
    sid = st.selectbox("Chọn học viên cập nhật tiền dạy", df["Mã HV"].tolist(), format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0])
    status = st.radio("Trạng thái", ["Chưa", "Có"], horizontal=True, index=1 if df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"].values[0] == "Có" else 0)
    if st.button("💾 Lưu trạng thái", use_container_width=True):
        df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"] = status
        save_students(df)
        st.success("Đã lưu.")
        st.rerun()
    st.dataframe(df[["Họ tên","Khóa học","Đã học","Tổng buổi","Đã nhận tiền dạy"]], use_container_width=True, hide_index=True)


def page_settings(busy_slots):
    hero("⚙️ Cài đặt", "Tick ca bận trực tiếp trên app, không cần sửa code")
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


def main():
    st.set_page_config(page_title="BLT Manager v3", page_icon=str(ASSETS / "logo.png") if (ASSETS / "logo.png").exists() else "🏊", layout="wide")
    render_css()
    if st_autorefresh:
        st_autorefresh(interval=60_000, key="blt_realtime")
    df = load_students()
    busy_slots = load_busy_slots()
    with st.sidebar:
        if (ASSETS / "logo.png").exists(): st.image(str(ASSETS / "logo.png"), width=120)
        st.markdown("## BLT Manager v3")
        page = st.radio("Điều hướng", ["🏠 Dashboard", "📅 Lịch dạy", "👨‍🎓 Học viên", "💰 Học phí", "⚙️ Cài đặt"], label_visibility="collapsed")
        st.caption("Mobile-first • Giờ Việt Nam GMT+7")
    if page == "🏠 Dashboard": page_dashboard(df, busy_slots)
    elif page == "📅 Lịch dạy": page_schedule(df, busy_slots)
    elif page == "👨‍🎓 Học viên": page_students(df, busy_slots)
    elif page == "💰 Học phí": page_money(df)
    else: page_settings(busy_slots)

if __name__ == "__main__":
    main()
