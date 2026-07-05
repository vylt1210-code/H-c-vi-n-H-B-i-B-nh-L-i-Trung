import streamlit as st
import pandas as pd
from utils.style import setup_page, sidebar_brand, hero, section_image
from utils.database import load_students, save_students, make_student_id, highlight_done
from utils.constants import DAYS, CAS, COURSES, STUDENTS_IMAGE_PATH
from utils.database import load_busy_slots

setup_page('Học viên | BLT Swimming')
sidebar_brand()
hero('👨‍🎓 Quản lý học viên', 'Thêm, sửa, tìm kiếm và xóa học viên')
section_image(STUDENTS_IMAGE_PATH)

df = load_students()
busy_slots = load_busy_slots()

mode = st.radio('Chọn chức năng', ['Thêm học viên', 'Danh sách & tìm kiếm', 'Sửa học viên', 'Xóa học viên'], horizontal=True)

if mode == 'Thêm học viên':
    st.subheader('➕ Thêm học viên mới')
    with st.form('add_student_form'):
        c1, c2 = st.columns(2)
        with c1:
            name = st.text_input('Họ tên *')
            phone = st.text_input('Số điện thoại')
            course = st.selectbox('Khóa học', COURSES)
            start_date = st.date_input('Ngày bắt đầu')
        with c2:
            total_lessons = st.number_input('Tổng số buổi', min_value=1, value=12)
            learned_lessons = st.number_input('Đã học', min_value=0, value=0)
            paid_teaching = st.selectbox('Đã nhận tiền dạy', ['Chưa', 'Có'])
            note = st.text_area('Ghi chú')

        st.markdown('### Chọn lịch học')
        selected_schedule = []
        for day in DAYS:
            available_cas = [ca for ca in CAS.keys() if f'{day} - {ca}' not in busy_slots]
            selected_cas = st.multiselect(day, available_cas, key=f'add_{day}')
            for ca in selected_cas:
                selected_schedule.append(f'{day} - {ca}')

        submitted = st.form_submit_button('💾 Lưu học viên', use_container_width=True)
        if submitted:
            if not name.strip():
                st.warning('Vui lòng nhập họ tên.')
            elif not selected_schedule:
                st.warning('Vui lòng chọn ít nhất một ca học.')
            else:
                new_row = {
                    'Mã HV': make_student_id(df),
                    'Họ tên': name.strip(),
                    'SĐT': phone.strip(),
                    'Khóa học': course,
                    'Lịch học': ', '.join(selected_schedule),
                    'Tổng buổi': int(total_lessons),
                    'Đã học': int(learned_lessons),
                    'Đã nhận tiền dạy': paid_teaching,
                    'Ngày bắt đầu': start_date.strftime('%Y-%m-%d'),
                    'Ghi chú': note.strip(),
                }
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                save_students(df)
                st.success('Đã thêm học viên.')
                st.rerun()

elif mode == 'Danh sách & tìm kiếm':
    st.subheader('🔍 Danh sách học viên')
    search = st.text_input('Tìm theo tên hoặc số điện thoại')
    show_df = df.copy()
    if search.strip():
        show_df = show_df[
            show_df['Họ tên'].astype(str).str.contains(search, case=False, na=False) |
            show_df['SĐT'].astype(str).str.contains(search, case=False, na=False)
        ]
    if show_df.empty:
        st.warning('Không tìm thấy học viên.')
    else:
        st.dataframe(show_df.style.apply(highlight_done, axis=1), use_container_width=True, hide_index=True)
        csv = show_df.to_csv(index=False).encode('utf-8-sig')
        st.download_button('📥 Tải danh sách CSV', csv, 'danh_sach_hoc_vien.csv', 'text/csv', use_container_width=True)

elif mode == 'Sửa học viên':
    st.subheader('✏️ Sửa thông tin học viên')
    if df.empty:
        st.warning('Chưa có học viên.')
    else:
        edit_id = st.selectbox('Chọn học viên', df['Mã HV'].tolist(), format_func=lambda x: df.loc[df['Mã HV'] == x, 'Họ tên'].values[0])
        idx = df[df['Mã HV'] == edit_id].index[0]
        old = df.loc[idx]
        with st.form('edit_student_form'):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input('Họ tên', value=str(old['Họ tên']))
                phone = st.text_input('Số điện thoại', value=str(old['SĐT']))
                course = st.selectbox('Khóa học', COURSES, index=COURSES.index(old['Khóa học']) if old['Khóa học'] in COURSES else 0)
                start_date = st.text_input('Ngày bắt đầu', value=str(old['Ngày bắt đầu']))
            with c2:
                total_lessons = st.number_input('Tổng số buổi', min_value=1, value=int(old['Tổng buổi']))
                learned_lessons = st.number_input('Đã học', min_value=0, value=int(old['Đã học']))
                paid_teaching = st.selectbox('Đã nhận tiền dạy', ['Chưa', 'Có'], index=1 if str(old['Đã nhận tiền dạy']) == 'Có' else 0)
                note = st.text_area('Ghi chú', value=str(old['Ghi chú']))

            st.markdown('### Cập nhật lịch học')
            current = [s.strip() for s in str(old['Lịch học']).split(',') if s.strip()]
            selected_schedule = []
            for day in DAYS:
                available_cas = list(CAS.keys())
                default = [ca for ca in available_cas if f'{day} - {ca}' in current]
                selected_cas = st.multiselect(day, available_cas, default=default, key=f'edit_{day}_{edit_id}')
                for ca in selected_cas:
                    selected_schedule.append(f'{day} - {ca}')
            submitted = st.form_submit_button('💾 Lưu thay đổi', use_container_width=True)
            if submitted:
                if not name.strip():
                    st.warning('Tên không được trống.')
                else:
                    df.loc[idx, 'Họ tên'] = name.strip()
                    df.loc[idx, 'SĐT'] = phone.strip()
                    df.loc[idx, 'Khóa học'] = course
                    df.loc[idx, 'Lịch học'] = ', '.join(selected_schedule)
                    df.loc[idx, 'Tổng buổi'] = int(total_lessons)
                    df.loc[idx, 'Đã học'] = int(learned_lessons)
                    df.loc[idx, 'Đã nhận tiền dạy'] = paid_teaching
                    df.loc[idx, 'Ngày bắt đầu'] = start_date
                    df.loc[idx, 'Ghi chú'] = note.strip()
                    save_students(df)
                    st.success('Đã cập nhật học viên.')
                    st.rerun()

else:
    st.subheader('🗑 Xóa học viên')
    if df.empty:
        st.warning('Chưa có học viên.')
    else:
        delete_id = st.selectbox('Chọn học viên cần xóa', df['Mã HV'].tolist(), format_func=lambda x: df.loc[df['Mã HV'] == x, 'Họ tên'].values[0])
        confirm = st.checkbox('Tôi xác nhận muốn xóa học viên này')
        if st.button('🗑 Xóa học viên', use_container_width=True):
            if not confirm:
                st.warning('Vui lòng tick xác nhận trước khi xóa.')
            else:
                deleted_name = df.loc[df['Mã HV'] == delete_id, 'Họ tên'].values[0]
                df = df[df['Mã HV'] != delete_id]
                save_students(df)
                st.success(f'Đã xóa học viên: {deleted_name}')
                st.rerun()
