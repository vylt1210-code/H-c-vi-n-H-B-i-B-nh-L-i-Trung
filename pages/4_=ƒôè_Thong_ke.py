import streamlit as st
import pandas as pd
from utils.style import setup_page, sidebar_brand, hero, metric_card, section_image
from utils.database import load_students, load_busy_slots, remaining_lessons

setup_page('Thống kê | BLT Swimming')
sidebar_brand()
hero('📊 Thống kê', 'Tổng quan học viên, khóa học và tình trạng buổi học')

df = load_students()
busy_slots = load_busy_slots()

if df.empty:
    st.warning('Chưa có dữ liệu để thống kê.')
else:
    remain = remaining_lessons(df)
    c1, c2, c3, c4 = st.columns(4)
    with c1: metric_card('Tổng học viên', len(df))
    with c2: metric_card('Đủ buổi', int((remain <= 0).sum()))
    with c3: metric_card('Sắp hết', int(((remain > 0) & (remain <= 2)).sum()))
    with c4: metric_card('Chưa nhận tiền', int((df['Đã nhận tiền dạy'] == 'Chưa').sum()))

    st.markdown('---')
    st.subheader('Học viên theo khóa học')
    course_counts = df['Khóa học'].value_counts().reset_index()
    course_counts.columns = ['Khóa học', 'Số học viên']
    st.bar_chart(course_counts.set_index('Khóa học'))

    st.subheader('Tình trạng tiền dạy')
    paid_counts = df['Đã nhận tiền dạy'].value_counts().reset_index()
    paid_counts.columns = ['Trạng thái', 'Số học viên']
    st.bar_chart(paid_counts.set_index('Trạng thái'))

    st.subheader('Phân bố số buổi còn lại')
    temp = pd.DataFrame({'Còn lại': remain})
    st.bar_chart(temp['Còn lại'].value_counts().sort_index())
