import streamlit as st
import pandas as pd
from utils.style import setup_page, sidebar_brand, hero
from utils.database import load_busy_slots, save_busy_slots, load_students, save_students
from utils.constants import DAYS, CAS

setup_page('Cài đặt | BLT Swimming')
sidebar_brand()
hero('⚙️ Cài đặt', 'Cài lịch bận, sao lưu và phục hồi dữ liệu')

busy_slots = load_busy_slots()

tab1, tab2 = st.tabs(['Lịch bận', 'Sao lưu dữ liệu'])

with tab1:
    st.subheader('Cài đặt lịch bận')
    st.info('Tick vào ca bạn bận. Ca bận sẽ không hiện khi thêm học viên.')
    new_busy_slots = set()
    for day in DAYS:
        st.markdown(f'### {day}')
        cols = st.columns(5)
        for i, ca in enumerate(CAS.keys()):
            slot = f'{day} - {ca}'
            with cols[i % 5]:
                checked = st.checkbox(f'{ca} | {CAS[ca]}', value=slot in busy_slots, key=f'busy_{slot}')
                if checked:
                    new_busy_slots.add(slot)
    if st.button('💾 Lưu lịch bận', use_container_width=True):
        save_busy_slots(new_busy_slots)
        st.success('Đã lưu lịch bận.')
        st.rerun()
    st.markdown('---')
    if busy_slots:
        st.dataframe(pd.DataFrame({'Ca bận': sorted(list(busy_slots))}), use_container_width=True, hide_index=True)
    else:
        st.info('Hiện chưa có ca bận.')

with tab2:
    st.subheader('Sao lưu học viên')
    df = load_students()
    csv = df.to_csv(index=False).encode('utf-8-sig')
    st.download_button('📥 Tải file học viên CSV', csv, 'hoc_vien_backup.csv', 'text/csv', use_container_width=True)
    st.warning('Phục hồi dữ liệu sẽ ghi đè danh sách hiện tại. Hãy tải backup trước khi phục hồi.')
    uploaded = st.file_uploader('Upload file hoc_vien_backup.csv để phục hồi', type=['csv'])
    if uploaded is not None:
        new_df = pd.read_csv(uploaded)
        st.dataframe(new_df.head(20), use_container_width=True)
        if st.button('♻️ Phục hồi dữ liệu từ file này', use_container_width=True):
            save_students(new_df)
            st.success('Đã phục hồi dữ liệu.')
            st.rerun()
