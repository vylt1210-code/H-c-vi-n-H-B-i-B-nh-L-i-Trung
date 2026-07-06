import streamlit as st
import pandas as pd
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from utils.style import setup_page, sidebar_brand, hero, section_image
from utils.database import load_students, save_students, load_busy_slots, get_students_by_slot, highlight_done
from utils.constants import DAYS, CAS, POOL_IMAGE_PATH

setup_page('Lịch dạy | BLT Swimming')
sidebar_brand()

st_autorefresh(interval=60000, key="lich_day_refresh")

hero('📅 Lịch dạy', 'Lịch tự cập nhật theo thời gian thực')
section_image(POOL_IMAGE_PATH)

df = load_students()
busy_slots = load_busy_slots()

def get_ca_status(time_range):
    now = datetime.now().time()
    start_str, end_str = time_range.split(" - ")
    start = datetime.strptime(start_str, "%H:%M").time()
    end = datetime.strptime(end_str, "%H:%M").time()

    if start <= now < end:
        return "🟡 Đang diễn ra"
    elif now < start:
        return "🔵 Sắp tới"
    else:
        return "⚫ Đã qua"

now_text = datetime.now().strftime("%H:%M:%S")
st.info(f"🕒 Thời gian hiện tại: {now_text} — app tự cập nhật mỗi 60 giây")

st.subheader('Lịch tổng quan')
st.caption('🔴 Bận | 🟡 Đang diễn ra | 🔵 Sắp tới | ⚫ Đã qua')

header_cols = st.columns([1.2] + [1]*len(DAYS))
header_cols[0].markdown('**Ca / Thứ**')

for i, day in enumerate(DAYS):
    header_cols[i+1].markdown(f'**{day}**')

for ca, time_range in CAS.items():
    cols = st.columns([1.2] + [1]*len(DAYS))
    status = get_ca_status(time_range)

    cols[0].markdown(
        f'**{ca}**<br><span class="small-muted">{time_range}</span><br>{status}',
        unsafe_allow_html=True
    )

    for i, day in enumerate(DAYS):
        slot = f'{day} - {ca}'
        count = len(get_students_by_slot(df, day, ca))

        if slot in busy_slots:
            label = '🔴 Bận'
        elif count > 0:
            label = f'{status} | {count} HV'
        else:
            label = f'{status} | Trống'

        if cols[i+1].button(label, key=f'slot_{slot}', use_container_width=True):
            st.session_state['selected_day'] = day
            st.session_state['selected_ca'] = ca

st.markdown('---')

selected_day = st.session_state.get('selected_day', DAYS[0])
selected_ca = st.session_state.get('selected_ca', list(CAS.keys())[0])
selected_slot = f'{selected_day} - {selected_ca}'
selected_status = get_ca_status(CAS[selected_ca])

st.subheader(f'Chi tiết: {selected_slot} | {CAS[selected_ca]}')
st.write(f"Trạng thái ca: **{selected_status}**")

if selected_slot in busy_slots:
    st.error('Đây là ca bận. Vào trang Cài đặt để mở lại ca này.')
else:
    class_df = get_students_by_slot(df, selected_day, selected_ca)

    if class_df.empty:
        st.warning('Ca này chưa có học viên.')
    else:
        class_df['Buổi hiện tại'] = class_df['Đã học'] + 1
        class_df['Còn lại'] = class_df['Tổng buổi'] - class_df['Đã học']

        st.dataframe(
            class_df[
                ['Mã HV','Họ tên','SĐT','Khóa học','Buổi hiện tại',
                 'Đã học','Tổng buổi','Còn lại','Đã nhận tiền dạy','Ghi chú']
            ].style.apply(highlight_done, axis=1),
            use_container_width=True,
            hide_index=True
        )

        checked_ids = st.multiselect(
            'Chọn học viên đã học buổi này',
            class_df['Mã HV'].tolist(),
            format_func=lambda x: class_df.loc[class_df['Mã HV'] == x, 'Họ tên'].values[0]
        )

        if st.button('✅ Điểm danh / Tăng buổi', use_container_width=True):
            for hv_id in checked_ids:
                idx = df[df['Mã HV'] == hv_id].index

                if len(idx) > 0:
                    idx = idx[0]

                    if int(df.loc[idx, 'Đã học']) < int(df.loc[idx, 'Tổng buổi']):
                        df.loc[idx, 'Đã học'] += 1

            save_students(df)
            st.success('Đã cập nhật số buổi.')
            st.rerun()
