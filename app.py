import streamlit as st
import pandas as pd
from pathlib import Path

DATA_FILE = Path("hoc_vien.csv")

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
    "Tổng buổi", "Đã học", "Ghi chú"
]


def load_data():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)

        for col in COLUMNS:
            if col not in df.columns:
                df[col] = ""

        if df["Mã HV"].isna().all() or (df["Mã HV"].astype(str).str.strip() == "").all():
            df["Mã HV"] = range(1, len(df) + 1)

        df["Mã HV"] = pd.to_numeric(df["Mã HV"], errors="coerce")
        df["Mã HV"] = df["Mã HV"].fillna(pd.Series(range(1, len(df) + 1)))
        df["Mã HV"] = df["Mã HV"].astype(int)

        df["Tổng buổi"] = pd.to_numeric(df["Tổng buổi"], errors="coerce").fillna(12).astype(int)
        df["Đã học"] = pd.to_numeric(df["Đã học"], errors="coerce").fillna(0).astype(int)

        return df[COLUMNS]

    return pd.DataFrame(columns=COLUMNS)


def save_data(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def make_student_id(df):
    if df.empty or "Mã HV" not in df.columns:
        return 1

    max_id = pd.to_numeric(df["Mã HV"], errors="coerce").max()

    if pd.isna(max_id):
        return 1

    return int(max_id) + 1


def get_students_by_slot(df, day, ca):
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)

    slot = f"{day} - {ca}"
    return df[df["Lịch học"].astype(str).str.contains(slot, na=False)].copy()


st.set_page_config(page_title="Quản lý học viên hồ bơi", layout="wide")
st.title("🏊 QUẢN LÝ HỌC VIÊN & LỊCH DẠY")

df = load_data()

tab1, tab2, tab3 = st.tabs([
    "➕ Thêm học viên",
    "📅 Lịch dạy tổng quan",
    "👨‍🎓 Danh sách học viên"
])

with tab1:
    st.subheader("Thêm học viên mới")

    name = st.text_input("Họ tên")
    phone = st.text_input("Số điện thoại")
    course = st.selectbox("Khóa học", ["Ếch", "Sải", "Sải ôn ếch", "Khác"])
    total_lessons = st.number_input("Tổng số buổi", min_value=1, value=12)
    learned_lessons = st.number_input("Đã học", min_value=0, value=0)
    note = st.text_area("Ghi chú")

    st.write("Chọn lịch học:")

    selected_schedule = []

    for day in DAYS:
        selected_cas = st.multiselect(day, list(CAS.keys()), key=f"add_{day}")
        for ca in selected_cas:
            selected_schedule.append(f"{day} - {ca}")

    if st.button("Lưu học viên"):
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
                "Ghi chú": note.strip()
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Đã thêm học viên thành công.")
            st.rerun()

with tab2:
    st.subheader("Lịch dạy tổng quan")

    schedule_rows = []

    for ca, time in CAS.items():
        row = {"Ca": ca, "Thời gian": time}

        for day in DAYS:
            class_df = get_students_by_slot(df, day, ca)
            count = len(class_df)
            row[day] = f"{count} HV"

        schedule_rows.append(row)

    overview_df = pd.DataFrame(schedule_rows)
    st.dataframe(overview_df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Bấm chọn ca để xem học viên")

    col1, col2 = st.columns(2)

    with col1:
        day_pick = st.selectbox("Chọn thứ", DAYS)

    with col2:
        ca_pick = st.selectbox("Chọn ca", list(CAS.keys()))

    selected_slot = f"{day_pick} - {ca_pick}"
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
                "Buổi hiện tại", "Đã học", "Tổng buổi", "Còn lại", "Ghi chú"
            ]],
            use_container_width=True,
            hide_index=True
        )

        checked_ids = st.multiselect(
            "Chọn học viên đã học buổi này",
            class_df["Mã HV"].tolist(),
            format_func=lambda x: class_df.loc[class_df["Mã HV"] == x, "Họ tên"].values[0]
        )

        if st.button("Điểm danh / Tăng buổi"):
            for hv_id in checked_ids:
                idx = df[df["Mã HV"] == hv_id].index

                if len(idx) > 0:
                    idx = idx[0]
                    if int(df.loc[idx, "Đã học"]) < int(df.loc[idx, "Tổng buổi"]):
                        df.loc[idx, "Đã học"] += 1

            save_data(df)
            st.success("Đã cập nhật số buổi.")
            st.rerun()

with tab3:
    st.subheader("Danh sách học viên")

    if df.empty:
        st.warning("Chưa có học viên.")
    else:
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()

    st.subheader("Xóa học viên")

    if not df.empty:
        delete_id = st.selectbox(
            "Chọn học viên cần xóa",
            df["Mã HV"].tolist(),
            format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0]
        )

        confirm_delete = st.checkbox("Tôi xác nhận muốn xóa học viên này")

        if st.button("Xóa học viên"):
            if confirm_delete:
                deleted_name = df.loc[df["Mã HV"] == delete_id, "Họ tên"].values[0]
                df = df[df["Mã HV"] != delete_id]
                save_data(df)
                st.success(f"Đã xóa học viên: {deleted_name}")
                st.rerun()
            else:
                st.warning("Vui lòng tick xác nhận trước khi xóa.")

    st.divider()

    csv = df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        "Tải danh sách CSV",
        csv,
        "danh_sach_hoc_vien.csv",
        "text/csv"
    )
