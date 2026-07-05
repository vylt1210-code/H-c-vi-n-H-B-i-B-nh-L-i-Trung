import streamlit as st
from utils.style import setup_page, sidebar_brand, hero
from utils.database import load_students, save_students, highlight_done

setup_page('Học phí | BLT Swimming')
sidebar_brand()
hero('💰 Học phí & tiền dạy', 'Theo dõi trạng thái đã nhận tiền dạy')

df = load_students()

if df.empty:
    st.warning('Chưa có học viên.')
else:
    df_view = df.copy()
    df_view['Còn lại'] = df_view['Tổng buổi'] - df_view['Đã học']
    st.dataframe(
        df_view[['Mã HV','Họ tên','SĐT','Khóa học','Đã học','Tổng buổi','Còn lại','Đã nhận tiền dạy','Ghi chú']].style.apply(highlight_done, axis=1),
        use_container_width=True,
        hide_index=True
    )

    st.markdown('---')
    st.subheader('Cập nhật tiền dạy')
    money_id = st.selectbox('Chọn học viên', df['Mã HV'].tolist(), format_func=lambda x: df.loc[df['Mã HV'] == x, 'Họ tên'].values[0])
    current = df.loc[df['Mã HV'] == money_id, 'Đã nhận tiền dạy'].values[0]
    new_status = st.selectbox('Trạng thái', ['Chưa', 'Có'], index=1 if current == 'Có' else 0)
    if st.button('💾 Lưu trạng thái', use_container_width=True):
        df.loc[df['Mã HV'] == money_id, 'Đã nhận tiền dạy'] = new_status
        save_students(df)
        st.success('Đã cập nhật tiền dạy.')
        st.rerun()

    st.markdown('---')
    unpaid = df[df['Đã nhận tiền dạy'].astype(str) == 'Chưa']
    st.subheader(f'Danh sách chưa nhận tiền: {len(unpaid)} học viên')
    if not unpaid.empty:
        st.dataframe(unpaid[['Mã HV','Họ tên','SĐT','Khóa học','Đã học','Tổng buổi']], use_container_width=True, hide_index=True)
