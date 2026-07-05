import streamlit as st
import pandas as pd
from datetime import datetime
from utils.style import setup_page, sidebar_brand, hero, metric_card, section_image
from utils.database import load_students, load_busy_slots, get_students_by_slot, remaining_lessons
from utils.constants import DAYS, CAS, BANNER_PATH, DASHBOARD_IMAGE_PATH
from pathlib import Path

setup_page('Dashboard | BLT Swimming')
sidebar_brand()

df = load_students()
busy_slots = load_busy_slots()

hero('BLT SWIMMING CLUB', 'Dashboard quản lý học viên & lịch dạy')

section_image(BANNER_PATH)

remain = remaining_lessons(df)
total_students = len(df)
done_students = int((remain <= 0).sum()) if not df.empty else 0
almost_done = int(((remain > 0) & (remain <= 2)).sum()) if not df.empty else 0
not_paid = int((df['Đã nhận tiền dạy'].astype(str) == 'Chưa').sum()) if not df.empty else 0
busy_count = len(busy_slots)

c1, c2, c3, c4, c5 = st.columns(5)
with c1: metric_card('Tổng học viên', total_students, 'Đang quản lý', '👨‍🎓')
with c2: metric_card('Đã đủ buổi', done_students, 'Tô xanh lá', '✅')
with c3: metric_card('Sắp hết buổi', almost_done, 'Còn 1–2 buổi', '⚠️')
with c4: metric_card('Chưa nhận tiền', not_paid, 'Tiền dạy GV', '💰')
with c5: metric_card('Ca bận', busy_count, 'Đang khóa lịch', '🔒')

st.markdown('---')
st.subheader('📌 Lịch hôm nay')

weekday_map = {
    0: 'Thứ 2', 1: 'Thứ 3', 2: 'Thứ 4', 3: 'Thứ 5', 4: 'Thứ 6', 5: 'Thứ 7', 6: 'Chủ nhật'
}
today = weekday_map[datetime.now().weekday()]
st.info(f'Hôm nay: **{today}**')

cols = st.columns(5)
for i, (ca, time) in enumerate(CAS.items()):
    slot = f'{today} - {ca}'
    count = len(get_students_by_slot(df, today, ca))
    if slot in busy_slots:
        status = '🔴 Bận'
        cls = 'badge-red'
    elif count > 0:
        status = f'🟢 {count} học viên'
        cls = 'badge-green'
    else:
        status = '⚪ Trống'
        cls = 'badge-blue'
    with cols[i % 5]:
        st.markdown(f'''
<div class="student-card">
  <div class="student-name">{ca}</div>
  <div class="small-muted">{time}</div>
  <span class="badge {cls}">{status}</span>
</div>
''', unsafe_allow_html=True)

st.markdown('---')
st.subheader('⚠️ Học viên cần chú ý')
if df.empty:
    st.warning('Chưa có học viên.')
else:
    warning_df = df.copy()
    warning_df['Còn lại'] = warning_df['Tổng buổi'] - warning_df['Đã học']
    warning_df = warning_df[warning_df['Còn lại'] <= 2]
    if warning_df.empty:
        st.success('Chưa có học viên nào sắp hết buổi.')
    else:
        st.dataframe(warning_df[['Mã HV','Họ tên','SĐT','Khóa học','Đã học','Tổng buổi','Còn lại','Đã nhận tiền dạy']], use_container_width=True, hide_index=True)
