import streamlit as st
import pandas as pd
from pathlib import Path

DATA_FILE = Path("hoc_vien.csv")
BUSY_FILE = Path("lich_ban.csv")
LOGO_PATH = "assets/logo.png"
BANNER_PATH = "assets/banner.png"

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

COLUMNS = [
    "Mã HV", "Họ tên", "SĐT", "Khóa học", "Lịch học",
    "Tổng buổi", "Đã học", "Đã nhận tiền dạy", "Ghi chú"
]


def load_students():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
        for col in COLUMNS:
            if col not in df.columns:
                if col == "Tổng buổi":
                    df[col] = 12
                elif col == "Đã học":
                    df[col] = 0
                elif col == "Đã nhận tiền dạy":
                    df[col] = "Chưa"
                else:
                    df[col] = ""

        df["Mã HV"] = pd.to_numeric(df["Mã HV"], errors="coerce")
        df["Mã HV"] = df["Mã HV"].fillna(pd.Series(range(1, len(df) + 1))).astype(int)
        df["Tổng buổi"] = pd.to_numeric(df["Tổng buổi"], errors="coerce").fillna(12).astype(int)
        df["Đã học"] = pd.to_numeric(df["Đã học"], errors="coerce").fillna(0).astype(int)
        df["Đã nhận tiền dạy"] = df["Đã nhận tiền dạy"].fillna("Chưa")
        return df[COLUMNS]

    return pd.DataFrame(columns=COLUMNS)


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


def make_student_id(df):
    if df.empty:
        return 1
    max_id = pd.to_numeric(df["Mã HV"], errors="coerce").max()
    return 1 if pd.isna(max_id) else int(max_id) + 1


def get_students_by_slot(df, day, ca):
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    slot = f"{day} - {ca}"
    return df[df["Lịch học"].astype(str).str.contains(slot, na=False)].copy()


def highlight_done(row):
    if int(row["Đã học"]) >= int(row["Tổng buổi"]):
        return ["background-color: #b6f2b6"] * len(row)
    return [""] * len(row)


st.set_page_config(
    page_title="BLT Swimming Club",
    page_icon="🏊",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #e0f7ff 0%, #ffffff 45%, #dff6ff 100%);
}

.block-container {
    padding-top: 1.2rem;
}

.header-box {
    background: linear-gradient(90deg, #023e8a, #0096c7);
    padding: 24px;
    border-radius: 24px;
    color: white;
    box-shadow: 0 8px 22px rgba(0,0,0,0.18);
}

.header-box h1 {
    margin: 0;
    font-size: 38px;
}

.header-box p {
    font-size: 18px;
    margin-top: 6px;
}

.card {
    background: white;
    padding: 18px;
    border-radius: 20px;
    box-shadow: 0 5px 18px rgba(0,0,0,0.10);
    text-align: center;
}

.card h3 {
    margin: 0;
    color: #023e8a;
}

.card p {
    margin: 6px 0 0 0;
    font-size: 28px;
    font-weight: bold;
    color: #0077b6;
}

div[data-testid="stTabs"] button {
    font-size: 16px;
    font-weight: 600;
}

.busy-cell {
    background: #ffccd5;
    color: #9d0208;
    font-weight: bold;
}

.free-cell {
    background: #caf0f8;
    color: #023e8a;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)


df = load_students()
busy_slots = load_busy_slots()

col_logo, col_title = st.columns([1, 5])

with col_logo:
    if Path(LOGO_PATH).exists():
        st.image(LOGO_PATH, width=135)
    else:
        st.markdown("## 🏊 BLT")

with col_title:
    st.markdown("""
    <div class="header-box">
        <h1>BLT SWIMMING CLUB</h1>
        <p>Quản lý học viên & lịch dạy Hồ Bơi Bình Lợi Trung</p>
    </div>
    """, unsafe_allow_html=True)

if Path(BANNER_PATH).exists():
    st.image(BANNER_PATH, use_container_width=True)

total_students = len(df)
done_students = len(df[df["Đã học"] >= df["Tổng buổi"]]) if not df.empty else 0
not_paid = len(df[df["Đã nhận tiền dạy"] == "Chưa"]) if not df.empty else 0
almost_done = len(df[(df["Tổng buổi"] - df["Đã học"]) <= 2]) if not df.empty else 0

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(f'<div class="card"><h3>Tổng học viên</h3><p>{total_students}</p></div>', unsafe_allow_html=True)

with c2:
    st.markdown(f'<div class="card"><h3>Đã đủ buổi</h3><p>{done_students}</p></div>', unsafe_allow_html=True)

with c3:
    st.markdown(f'<div class="card"><h3>Sắp hết buổi</h3><p>{almost_done}</p></div>', unsafe_allow_html=True)

with c4:
    st.markdown(f'<div class="card"><h3>Chưa nhận tiền</h3><p>{not_paid}</p></div>', unsafe_allow_html=True)

st.write("")

tab1, tab2, tab3, tab4 = st.tabs([
    "➕ Thêm học viên",
    "📅 Lịch dạy",
    "👨‍🎓 Danh sách học viên",
    "⚙️ Cài đặt lịch bận"
])

with tab1:
    st.subheader("➕ Thêm học viên mới")

    col_a, col_b = st.columns(2)

    with col_a:
        name = st.text_input("Họ tên")
        phone = st.text_input("Số điện thoại")
        course = st.selectbox("Khóa học", ["Ếch", "Sải", "Sải ôn ếch", "Khác"])

    with col_b:
        total_lessons = st.number_input("Tổng số buổi", min_value=1, value=12)
        learned_lessons = st.number_input("Đã học", min_value=0, value=0)
        paid_teaching = st.checkbox("Đã nhận tiền dạy")

    note = st.text_area("Ghi chú")

    st.markdown("### Chọn lịch học")
    selected_schedule = []

    for day in DAYS:
        available_cas = [
            ca for ca in CAS.keys()
            if f"{day} - {ca}" not in busy_slots
        ]

        selected_cas = st.multiselect(day, available_cas, key=f"add_{day}")
        for ca in selected_cas:
            selected_schedule.append(f"{day} - {ca}")

    if st.button("💾 Lưu học viên", use_container_width=True):
        if name.strip() == "":
            st.warning("Vui lòng nhập họ tên.")
        elif len(selected_schedule) == 0:
            st.warning("Vui lòng chọn ít nhất một ca học.")
        else:
            new_row = {
                "Mã HV": make_student_id(df),
                "Họ tên": name.strip(),
                "SĐT": phone.strip(),
                "Khóa học": course,
                "Lịch học": ", ".join(selected_schedule),
                "Tổng buổi": int(total_lessons),
                "Đã học": int(learned_lessons),
                "Đã nhận tiền dạy": "Có" if paid_teaching else "Chưa",
                "Ghi chú": note.strip()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_students(df)
            st.success("Đã thêm học viên.")
            st.rerun()

with tab2:
    st.subheader("📅 Lịch dạy tổng quan")

    rows = []

    for ca, time in CAS.items():
        row = {"Ca": ca, "Thời gian": time}

        for day in DAYS:
            slot = f"{day} - {ca}"

            if slot in busy_slots:
                row[day] = "🔴 BẬN"
            else:
                count = len(get_students_by_slot(df, day, ca))
                row[day] = f"🟢 {count} HV" if count > 0 else "⚪ Trống"

        rows.append(row)

    overview_df = pd.DataFrame(rows)
    st.dataframe(overview_df, use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("👆 Xem chi tiết ca dạy")

    col1, col2 = st.columns(2)

    with col1:
        day_pick = st.selectbox("Chọn thứ", DAYS)

    with col2:
        ca_pick = st.selectbox("Chọn ca", list(CAS.keys()))

    selected_slot = f"{day_pick} - {ca_pick}"

    if selected_slot in busy_slots:
        st.error(f"{selected_slot} là ca bận.")
    else:
        st.info(f"Đang xem: {selected_slot} | {CAS[ca_pick]}")
        class_df = get_students_by_slot(df, day_pick, ca_pick)

        if class_df.empty:
            st.warning("Ca này chưa có học viên.")
        else:
            class_df["Buổi hiện tại"] = class_df["Đã học"] + 1
            class_df["Còn lại"] = class_df["Tổng buổi"] - class_df["Đã học"]

            st.dataframe(
                class_df[[
                    "Mã HV", "Họ tên", "SĐT", "Khóa học",
                    "Buổi hiện tại", "Đã học", "Tổng buổi",
                    "Còn lại", "Đã nhận tiền dạy", "Ghi chú"
                ]].style.apply(highlight_done, axis=1),
                use_container_width=True,
                hide_index=True
            )

            checked_ids = st.multiselect(
                "Chọn học viên đã học buổi này",
                class_df["Mã HV"].tolist(),
                format_func=lambda x: class_df.loc[
                    class_df["Mã HV"] == x, "Họ tên"
                ].values[0]
            )

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

with tab3:
    st.subheader("👨‍🎓 Danh sách học viên")

    search = st.text_input("🔍 Tìm học viên theo tên hoặc số điện thoại")

    show_df = df.copy()

    if search.strip() != "":
        show_df = show_df[
            show_df["Họ tên"].astype(str).str.contains(search, case=False, na=False)
            | show_df["SĐT"].astype(str).str.contains(search, case=False, na=False)
        ]

    if show_df.empty:
        st.warning("Không có học viên phù hợp.")
    else:
        st.dataframe(
            show_df.style.apply(highlight_done, axis=1),
            use_container_width=True,
            hide_index=True
        )

    st.divider()
    st.subheader("💰 Cập nhật tiền dạy")

    if not df.empty:
        money_id = st.selectbox(
            "Chọn học viên",
            df["Mã HV"].tolist(),
            format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0],
            key="money_id"
        )

        current_money = df.loc[df["Mã HV"] == money_id, "Đã nhận tiền dạy"].values[0]

        new_money = st.selectbox(
            "Trạng thái",
            ["Chưa", "Có"],
            index=1 if current_money == "Có" else 0
        )

        if st.button("💾 Cập nhật tiền dạy", use_container_width=True):
            df.loc[df["Mã HV"] == money_id, "Đã nhận tiền dạy"] = new_money
            save_students(df)
            st.success("Đã cập nhật.")
            st.rerun()

    st.divider()
    st.subheader("🗑 Xóa học viên")

    if not df.empty:
        delete_id = st.selectbox(
            "Chọn học viên cần xóa",
            df["Mã HV"].tolist(),
            format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0],
            key="delete_id"
        )

        confirm_delete = st.checkbox("Tôi xác nhận muốn xóa học viên này")

        if st.button("🗑 Xóa học viên", use_container_width=True):
            if confirm_delete:
                deleted_name = df.loc[df["Mã HV"] == delete_id, "Họ tên"].values[0]
                df = df[df["Mã HV"] != delete_id]
                save_students(df)
                st.success(f"Đã xóa học viên: {deleted_name}")
                st.rerun()
            else:
                st.warning("Vui lòng tick xác nhận trước khi xóa.")

    st.divider()

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "📥 Tải danh sách CSV",
        csv,
        "danh_sach_hoc_vien.csv",
        "text/csv",
        use_container_width=True
    )

with tab4:
    st.subheader("⚙️ Cài đặt lịch bận")

    st.info("Tick vào ca bạn bận. Ca bận sẽ không hiện khi thêm học viên.")

    new_busy_slots = set()

    for day in DAYS:
        st.markdown(f"### {day}")
        cols = st.columns(5)

        for i, ca in enumerate(CAS.keys()):
            slot = f"{day} - {ca}"

            with cols[i % 5]:
                checked = st.checkbox(
                    f"{ca} | {CAS[ca]}",
                    value=slot in busy_slots,
                    key=f"busy_{slot}"
                )

                if checked:
                    new_busy_slots.add(slot)

    if st.button("💾 Lưu lịch bận", use_container_width=True):
        save_busy_slots(new_busy_slots)
        st.success("Đã lưu lịch bận.")
        st.rerun()

    st.divider()

    st.subheader("Danh sách ca đang bận")

    if len(busy_slots) == 0:
        st.info("Hiện chưa có ca bận.")
    else:
        busy_df = pd.DataFrame({"Ca bận": sorted(list(busy_slots))})
        st.dataframe(busy_df, use_container_width=True, hide_index=True)
