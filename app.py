import streamlit as st

from utils.ui import setup_page, sidebar_menu
from utils.database import load_students, load_busy_slots
from utils.pages import (
    page_dashboard,
    page_schedule,
    page_students,
    page_money,
    page_teacher_fee,
    page_settings,
)
from utils.constants import ASSETS


def main():
    icon = str(ASSETS / "logo.png") if (ASSETS / "logo.png").exists() else "🏊"
    st.set_page_config(
        page_title="BLT Manager",
        page_icon=icon,
        layout="wide"
    )

    setup_page()

    df = load_students()
    busy_slots = load_busy_slots()

    page = sidebar_menu()

    if page == "🏠 Dashboard":
        page_dashboard(df, busy_slots)
    elif page == "📅 Lịch dạy":
        page_schedule(df, busy_slots)
    elif page == "👨‍🎓 Học viên":
        page_students(df, busy_slots)
    elif page == "💰 Học phí":
        page_money(df)
    elif page == "👨‍🏫 Tiền thầy":
        page_teacher_fee()
    else:
        page_settings(busy_slots)


if __name__ == "__main__":
    main()
