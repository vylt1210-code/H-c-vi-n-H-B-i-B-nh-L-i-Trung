import streamlit as st

from .constants import ASSETS, ATTENDANCE_COLS
from .database import progress_pct


def setup_page():
    st.markdown("""
    <style>
    :root {
        --bg: #eef2f5;
        --card: #ffffff;
        --teal: #008f8f;
        --text: #425563;
        --muted: #6b7d88;
        --line: #d8e0e5;
        --red: #ef4444;
        --green: #22c55e;
        --blue: #3b82f6;
        --yellow: #f59e0b;
        --purple: #7b2cbf;
    }

    .stApp {
        background: var(--bg);
    }

    .block-container {
        max-width: 1280px;
        padding-top: 1rem;
        padding-bottom: 3rem;
    }

    [data-testid="stSidebar"] {
        background: white;
        border-right: 1px solid var(--line);
    }

    [data-testid="stSidebar"] * {
        color: #425563;
    }

    .topbar {
        background: white;
        border-radius: 0 0 18px 18px;
        padding: 15px 24px;
        display: flex;
        align-items: center;
        justify-content: space-between;
        box-shadow: 0 8px 20px rgba(30, 50, 70, .08);
        margin-bottom: 18px;
    }

    .brand {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .hamb {
        font-size: 28px;
        color: var(--teal);
        font-weight: 900;
    }

    .brand-main {
        font-size: 30px;
        font-weight: 950;
        color: var(--teal);
        line-height: 1;
    }

    .brand-sub {
        font-size: 11px;
        color: #ef4444;
        font-weight: 900;
        letter-spacing: 1.5px;
        margin-top: 3px;
    }

    .user {
        display: flex;
        align-items: center;
        gap: 10px;
        color: #333;
        font-weight: 800;
    }

    .avatar-mini {
        width: 38px;
        height: 38px;
        border-radius: 50%;
        background: #e8f7f7;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        border: 1px solid var(--line);
    }

    .page-title {
        color: var(--teal);
        font-size: 26px;
        font-weight: 950;
        margin-bottom: 14px;
    }

    .card,
    .student-card,
    .slot-card,
    .report-card {
        background: white;
        border-radius: 18px;
        padding: 22px;
        box-shadow: 0 8px 24px rgba(40, 60, 80, .05);
        margin-bottom: 18px;
    }

    .summary-grid {
        display: grid;
        grid-template-columns: repeat(3, minmax(0, 1fr));
        gap: 16px;
        margin: 12px 0 18px;
    }

    .summary-card {
        background: linear-gradient(135deg, white, #f8fdff);
        border-radius: 22px;
        padding: 20px;
        box-shadow: 0 12px 30px rgba(2, 62, 138, .10);
        border: 1px solid #e7f3f7;
        min-height: 128px;
        position: relative;
        overflow: hidden;
    }

    .summary-card::after {
        content: "";
        position: absolute;
        right: -32px;
        top: -32px;
        width: 110px;
        height: 110px;
        border-radius: 50%;
        background: rgba(0, 180, 216, .10);
    }

    .summary-card.green {
        border-left: 6px solid var(--green);
    }

    .summary-card.orange {
        border-left: 6px solid var(--yellow);
    }

    .summary-card.red {
        border-left: 6px solid var(--red);
    }

    .summary-card.blue {
        border-left: 6px solid #00b4d8;
    }

    .summary-card.purple {
        border-left: 6px solid var(--purple);
    }

    .summary-card.teal {
        border-left: 6px solid var(--teal);
    }

    .summary-label {
        font-size: 14px;
        color: #607887;
        font-weight: 900;
    }

    .summary-value {
        font-size: 38px;
        color: #023e8a;
        font-weight: 950;
        margin-top: 6px;
        line-height: 1;
    }

    .summary-note {
        margin-top: 10px;
        color: #6b7f8a;
        font-weight: 700;
        font-size: 13px;
    }

    .summary-icon {
        font-size: 28px;
        position: absolute;
        right: 18px;
        bottom: 16px;
    }

    .smart-panel {
        background: linear-gradient(135deg, #023e8a, #0077b6 52%, #00b4d8);
        color: white;
        border-radius: 26px;
        padding: 22px;
        box-shadow: 0 18px 38px rgba(2, 62, 138, .22);
        margin: 14px 0 18px;
    }

    .smart-title {
        font-size: 21px;
        font-weight: 950;
        margin-bottom: 10px;
    }

    .smart-item {
        background: rgba(255, 255, 255, .14);
        border: 1px solid rgba(255, 255, 255, .18);
        padding: 11px 13px;
        border-radius: 16px;
        margin-top: 8px;
        font-weight: 750;
    }

    .report-title {
        color: #023e8a;
        font-weight: 950;
        font-size: 20px;
        margin-bottom: 12px;
    }

    .todo-item {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        align-items: center;
        padding: 12px 0;
        border-bottom: 1px solid #edf5f8;
        color: #425563;
        font-weight: 780;
    }

    .todo-item:last-child {
        border-bottom: none;
    }

    .todo-pill {
        padding: 6px 10px;
        border-radius: 999px;
        background: #e8f7ff;
        color: #006494;
        font-weight: 900;
        white-space: nowrap;
        font-size: 12px;
    }

    .timeline-row {
        display: grid;
        grid-template-columns: 92px 1fr 100px;
        gap: 12px;
        align-items: center;
        padding: 13px 0;
        border-bottom: 1px solid #edf5f8;
    }

    .timeline-row:last-child {
        border-bottom: none;
    }

    .timeline-time {
        color: #607887;
        font-weight: 950;
        font-size: 13px;
    }

    .timeline-main {
        font-weight: 950;
        color: #123;
    }

    .timeline-sub,
    .small {
        font-size: 13px;
        color: #6b7f8a;
        margin-top: 2px;
        font-weight: 700;
    }

    .quick-grid {
        display: grid;
        grid-template-columns: repeat(6, 1fr);
        gap: 18px;
    }

    .quick-card {
        background: white;
        border-radius: 16px;
        padding: 24px 16px;
        text-align: center;
        box-shadow: 0 8px 24px rgba(40, 60, 80, .05);
        min-height: 128px;
        transition: .15s;
    }

    .quick-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 30px rgba(40, 60, 80, .09);
    }

    .quick-icon {
        color: var(--teal);
        font-size: 34px;
        font-weight: 900;
    }

    .quick-text {
        color: #6a7b84;
        font-size: 16px;
        font-weight: 950;
        margin-top: 10px;
        line-height: 1.25;
    }

    .slot-title,
    .student-name {
        color: #0a4f93;
        font-size: 22px;
        font-weight: 950;
    }

    .pill {
        display: inline-block;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 900;
        text-align: center;
        white-space: nowrap;
        margin-top: 6px;
    }

    .pill-now {
        background: #fff3bf;
        color: #7a5c00;
    }

    .pill-soon {
        background: #dff6ff;
        color: #005f8f;
    }

    .pill-past {
        background: #e9ecef;
        color: #495057;
    }

    .pill-busy {
        background: #ffe3e8;
        color: #b00020;
    }

    .pill-ok {
        background: #d8fbe0;
        color: #087f23;
    }

    .pill-warn {
        background: #fff3bf;
        color: #7a5c00;
    }

    .progress-wrap,
    .bar-wrap {
        background: #e8f6fb;
        height: 12px;
        border-radius: 999px;
        overflow: hidden;
        margin: 12px 0 8px;
    }

    .progress-bar,
    .bar-fill {
        height: 12px;
        background: linear-gradient(90deg, #00b4d8, var(--green));
        border-radius: 999px;
    }

    div.stButton > button {
        border-radius: 12px;
        font-weight: 900;
        border: 1px solid #d6e5ea;
    }

    @media(max-width: 900px) {
        .summary-grid {
            grid-template-columns: 1fr;
        }

        .quick-grid {
            grid-template-columns: repeat(2, 1fr);
        }

        .timeline-row {
            grid-template-columns: 78px 1fr;
        }

        .timeline-row .pill {
            grid-column: 2;
            width: fit-content;
        }

        .brand-main {
            font-size: 21px;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def sidebar_menu():
    with st.sidebar:
        if (ASSETS / "logo.png").exists():
            st.image(str(ASSETS / "logo.png"), width=125)

        st.markdown("## BLT Manager")

        page = st.radio(
            "Điều hướng",
            [
                "🏠 Dashboard",
                "📅 Lịch dạy",
                "👨‍🎓 Học viên",
                "💰 Học phí",
                "👨‍🏫 Tiền thầy",
                "⚙️ Cài đặt",
            ],
            label_visibility="collapsed",
        )

        st.caption("Final clean • GMT+7")

    return page


def topbar():
    st.markdown(
        """
        <div class="topbar">
            <div class="brand">
                <div class="hamb">☰</div>
                <div>
                    <div class="brand-main">BLT SWIMMING</div>
                    <div class="brand-sub">SWIM MANAGEMENT SYSTEM</div>
                </div>
            </div>
            <div class="user">
                <div class="avatar-mini">🏊</div>
                <div>Hồ bơi Bình Lợi Trung ▾</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def summary_card(label, value, icon, note="", color="blue"):
    st.markdown(
        f"""
        <div class="summary-card {color}">
            <div class="summary-label">{label}</div>
            <div class="summary-value">{value}</div>
            <div class="summary-note">{note}</div>
            <div class="summary-icon">{icon}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def student_card(row):
    pct = progress_pct(row)
    remaining = int(row["Tổng buổi"]) - int(row["Đã học"])
    money = row.get("Đã nhận tiền dạy", "Chưa")
    course_status = row.get("Trạng thái khóa", "Đang học")

    money_class = "pill-ok" if money == "Có" else "pill-warn"
    status_class = "pill-past" if course_status == "Kết thúc" else ("pill-warn" if remaining <= 2 else "pill-soon")
    status = course_status if course_status == "Kết thúc" else ("Sắp hết" if remaining <= 2 else "Đang học")

    dates = " • ".join([str(row[c]) for c in ATTENDANCE_COLS if str(row[c]).strip() not in ["", "nan"]])

    st.markdown(
        f"""
        <div class="student-card">
            <div class="student-name">👤 {row['Họ tên']}</div>
            <div class="small">📱 {row.get('SĐT','')} • 🏊 {row.get('Khóa học','')} • 🗓️ ĐK: {row.get('Ngày đăng ký','')}</div>
            <div class="progress-wrap"><div class="progress-bar" style="width:{pct}%"></div></div>
            <div class="small"><b>{row['Đã học']}/{row['Tổng buổi']}</b> buổi • Còn {max(remaining, 0)} buổi</div>
            <span class="pill {money_class}">💰 Tiền dạy: {money}</span>
            <span class="pill {status_class}">🎓 {status}</span>
            <div class="small" style="margin-top:8px">📅 {row.get('Lịch học','')}</div>
            <div class="small">✅ Điểm danh: {dates if dates else 'Chưa có'}</div>
            <div class="small">📝 {row.get('Ghi chú','')}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
