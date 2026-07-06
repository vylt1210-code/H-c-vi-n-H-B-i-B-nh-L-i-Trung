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

def load_data():
    columns = [
        "Mã HV", "Họ tên", "SĐT", "Khóa học", "Lịch học",
        "Tổng buổi", "Đã học", "Ghi chú"
    ]

    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)

        if "Mã HV" not in df.columns:
            df.insert(0, "Mã HV", range(1, len(df) + 1))

        for col in columns:
            if col not in df.columns:
                df[col] = ""

        df["Mã HV"] = pd.to_numeric(df["Mã HV"], errors="coerce").fillna(0).astype(int)
        df["Tổng buổi"] = pd.to_numeric(df["Tổng buổi"], errors="coerce").fillna(12).astype(int)
        df["Đã học"] = pd.to_numeric(df["Đã học"], errors="coerce").fillna(0).astype(int)

        return df[columns]

    return pd.DataFrame(columns=columns)

st.set_page_config(page_title="Quản lý học viên", layout="wide")
st.title("QUẢN LÝ HỌC VIÊN & LỊCH DẠY")

df = load_data()

tab1, tab2, tab3 = st.tabs([
    "Thêm học viên",
    "Lịch dạy tổng quan",
    "Danh sách học viên"
])

with tab1:
    st.subheader("Thêm học viên mới")

    name = st.text_input("Họ tên")
    phone = st.text_input("Số điện thoại")
    course = st.selectbox("Khóa học", ["Ếch", "Sải", "Sải ôn ếch"])
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
        if not name:
            st.warning("Vui lòng nhập họ tên.")
        elif not selected_schedule:
            st.warning("Vui lòng chọn lịch học.")
        else:
            new_row = {
                "Mã HV": make_student_id(df),
                "Họ tên": name,
                "SĐT": phone,
                "Khóa học": course,
                "Lịch học": ", ".join(selected_schedule),
                "Tổng buổi": total_lessons,
                "Đã học": learned_lessons,
                "Ghi chú": note
            }

            df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
            save_data(df)
            st.success("Đã thêm học viên.")
            st.rerun()

with tab2:
    st.subheader("Lịch dạy tổng quan")

    schedule_rows = []

    for ca, time in CAS.items():
        row = {"Ca": ca, "Thời gian": time}

        for day in DAYS:
            slot = f"{day} - {ca}"
            if df.empty:
                count = 0
            else:
                count = df["Lịch học"].str.contains(slot, na=False).sum()

            row[day] = f"{count} học viên"

        schedule_rows.append(row)

    overview_df = pd.DataFrame(schedule_rows)
    st.dataframe(overview_df, use_container_width=True)

    st.divider()

    st.subheader("Xem chi tiết ca dạy")

    col1, col2 = st.columns(2)

    with col1:
        day_pick = st.selectbox("Chọn thứ", DAYS)

    with col2:
        ca_pick = st.selectbox("Chọn ca", list(CAS.keys()))

    selected_slot = f"{day_pick} - {ca_pick}"
    st.info(f"Đang xem: {selected_slot} | {CAS[ca_pick]}")

    if df.empty:
        st.warning("Chưa có dữ liệu học viên.")
    else:
        class_df = df[df["Lịch học"].str.contains(selected_slot, na=False)].copy()

        if class_df.empty:
            st.warning("Ca này chưa có học viên.")
        else:
            class_df["Buổi hiện tại"] = class_df["Đã học"] + 1
            class_df["Còn lại"] = class_df["Tổng buổi"] - class_df["Đã học"]

            st.dataframe(class_df[[
                "Mã HV", "Họ tên", "SĐT", "Khóa học",
                "Buổi hiện tại", "Đã học", "Tổng buổi", "Còn lại", "Ghi chú"
            ]], use_container_width=True)

            checked_ids = st.multiselect(
                "Chọn học viên đã học buổi này",
                class_df["Mã HV"].tolist(),
                format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0]
            )

            if st.button("Điểm danh / Tăng buổi"):
                for hv_id in checked_ids:
                    index = df[df["Mã HV"] == hv_id].index[0]

                    if df.loc[index, "Đã học"] < df.loc[index, "Tổng buổi"]:
                        df.loc[index, "Đã học"] += 1

                save_data(df)
                st.success("Đã cập nhật số buổi.")
                st.rerun()

with tab3:
    st.subheader("Danh sách học viên")

    if df.empty:
        st.warning("Chưa có học viên.")
    else:
        st.dataframe(df, use_container_width=True)

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
