from pathlib import Path

src = Path("/mnt/data/app_blt_v5_fix_anh_tien_thay.py")
if not src.exists():
    src = Path("/mnt/data/app.py")
text = src.read_text(encoding="utf-8")

text = text.replace(
'COLUMNS = ["Mã HV", "Họ tên", "SĐT", "Khóa học", "Lịch học", "Tổng buổi", "Đã học", "Đã nhận tiền dạy", "Ghi chú"]',
'ATTENDANCE_COLS = [f"Buổi {i}" for i in range(1, 13)]\nCOLUMNS = ["Mã HV", "Họ tên", "SĐT", "Khóa học", "Ngày đăng ký", "Lịch học", "Tổng buổi", "Đã học", "Đã nhận tiền dạy", "Ghi chú"] + ATTENDANCE_COLS'
)

text = text.replace(
'''    for col in COLUMNS:
        if col not in df.columns:
            if col == "Tổng buổi": df[col] = 12
            elif col == "Đã học": df[col] = 0
            elif col == "Đã nhận tiền dạy": df[col] = "Chưa"
            else: df[col] = ""''',
'''    for col in COLUMNS:
        if col not in df.columns:
            if col == "Tổng buổi":
                df[col] = 12
            elif col == "Đã học":
                df[col] = 0
            elif col == "Đã nhận tiền dạy":
                df[col] = "Chưa"
            elif col == "Ngày đăng ký":
                df[col] = datetime.now(VN_TZ).strftime("%d/%m/%Y")
            else:
                df[col] = ""'''
)

anchor = '''def get_students_by_slot(df, day, ca):
    if df.empty: return pd.DataFrame(columns=COLUMNS)
    slot = f"{day} - {ca}"
    return df[df["Lịch học"].astype(str).str.contains(slot, na=False, regex=False)].copy()
'''
helper = '''
def mark_attendance_for_student(df, hv_id):
    today = datetime.now(VN_TZ).strftime("%d/%m")
    idx = df[df["Mã HV"] == hv_id].index

    if len(idx) == 0:
        return df

    idx = idx[0]
    total = int(df.loc[idx, "Tổng buổi"])
    learned = int(df.loc[idx, "Đã học"])

    if learned >= total:
        return df

    for col in ATTENDANCE_COLS:
        val = str(df.loc[idx, col]).strip()
        if val == "" or val.lower() == "nan":
            df.loc[idx, col] = today
            break

    df.loc[idx, "Đã học"] = learned + 1
    return df
'''
if "def mark_attendance_for_student" not in text:
    text = text.replace(anchor, anchor + helper)

text = text.replace(
'''      <div class='small'>📱 {row.get('SĐT','')} &nbsp; • &nbsp; 🏊 {row.get('Khóa học','')}</div>''',
'''      <div class='small'>📱 {row.get('SĐT','')} &nbsp; • &nbsp; 🏊 {row.get('Khóa học','')} &nbsp; • &nbsp; 🗓️ ĐK: {row.get('Ngày đăng ký','')}</div>'''
)

text = text.replace(
'''        for hv_id in checked_ids:
            idx = df[df["Mã HV"] == hv_id].index
            if len(idx) > 0:
                idx = idx[0]
                if int(df.loc[idx, "Đã học"]) < int(df.loc[idx, "Tổng buổi"]):
                    df.loc[idx, "Đã học"] += 1
        save_students(df)''',
'''        for hv_id in checked_ids:
            df = mark_attendance_for_student(df, hv_id)
        save_students(df)'''
)

text = text.replace(
'''                total = st.number_input("Tổng buổi", min_value=1, value=12)
                learned = st.number_input("Đã học", min_value=0, value=0)
                paid = st.checkbox("Đã nhận tiền dạy")''',
'''                total = st.number_input("Tổng buổi", min_value=1, value=12)
                learned = st.number_input("Đã học", min_value=0, value=0)
                register_date = st.date_input("Ngày đăng ký", value=datetime.now(VN_TZ).date())
                paid = st.checkbox("Đã nhận tiền dạy")'''
)

text = text.replace(
'''"Khóa học": course, "Lịch học": ", ".join(schedule), "Tổng buổi": int(total), "Đã học": int(learned), "Đã nhận tiền dạy": "Có" if paid else "Chưa", "Ghi chú": note.strip()}''',
'''"Khóa học": course, "Ngày đăng ký": register_date.strftime("%d/%m/%Y"), "Lịch học": ", ".join(schedule), "Tổng buổi": int(total), "Đã học": int(learned), "Đã nhận tiền dạy": "Có" if paid else "Chưa", "Ghi chú": note.strip()}'''
)

text = text.replace(
'''                ecourse = st.selectbox("Khóa", ["Ếch", "Sải", "Sải ôn ếch", "Khác"], index=["Ếch", "Sải", "Sải ôn ếch", "Khác"].index(df.loc[idx, "Khóa học"]) if df.loc[idx, "Khóa học"] in ["Ếch", "Sải", "Sải ôn ếch", "Khác"] else 3)''',
'''                ecourse = st.selectbox("Khóa", ["Ếch", "Sải", "Sải ôn ếch", "Khác"], index=["Ếch", "Sải", "Sải ôn ếch", "Khác"].index(df.loc[idx, "Khóa học"]) if df.loc[idx, "Khóa học"] in ["Ếch", "Sải", "Sải ôn ếch", "Khác"] else 3)
                eregister = st.text_input("Ngày đăng ký", str(df.loc[idx, "Ngày đăng ký"]))'''
)

text = text.replace(
'''                df.loc[idx, ["Họ tên","SĐT","Khóa học","Lịch học","Tổng buổi","Đã học","Đã nhận tiền dạy","Ghi chú"]] = [ename, ephone, ecourse, eschedule, int(etotal), int(elearned), emoney, enote]''',
'''                df.loc[idx, ["Họ tên","SĐT","Khóa học","Ngày đăng ký","Lịch học","Tổng buổi","Đã học","Đã nhận tiền dạy","Ghi chú"]] = [ename, ephone, ecourse, eregister, eschedule, int(etotal), int(elearned), emoney, enote]'''
)

text = text.replace(
'''    for _, row in class_df.iterrows():
        student_card(row)
    checked_ids = st.multiselect''',
'''    for _, row in class_df.iterrows():
        student_card(row)

    with st.expander("📋 Xem bảng điểm danh 12 buổi"):
        show_cols = ["Họ tên", "Ngày đăng ký", "Đã học", "Tổng buổi"] + ATTENDANCE_COLS
        st.dataframe(class_df[show_cols], use_container_width=True, hide_index=True)

    checked_ids = st.multiselect'''
)

out = Path("/mnt/data/app_blt_v6_diem_danh_ngay_dang_ky.py")
out.write_text(text, encoding="utf-8")
print(out)
