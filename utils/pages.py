import pandas as pd
import streamlit as st
from datetime import datetime

try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    st_autorefresh = None

from .constants import DAYS, CAS, ATTENDANCE_COLS, VN_TZ
from .database import (
    now_vn,
    today_full,
    today_short,
    current_day_name,
    load_teacher_fees,
    save_teacher_fees,
    make_student_id,
    get_students_by_slot,
    get_active_students,
    get_finished_students,
    ca_status,
    mark_attendance,
    save_students,
    save_busy_slots,
    teacher_remaining_total,
)
from .ui import topbar, summary_card, student_card


def current_and_next_slot(busy_slots):
    today = current_day_name()
    current = None
    upcoming = None
    now_time = now_vn().time()

    for ca, time_range in CAS.items():
        start_s, end_s = time_range.split(" - ")
        start = datetime.strptime(start_s, "%H:%M").time()
        end = datetime.strptime(end_s, "%H:%M").time()
        slot = f"{today} - {ca}"

        if slot in busy_slots:
            continue

        if start <= now_time < end:
            current = (ca, time_range)
            break

        if now_time < start and upcoming is None:
            upcoming = (ca, time_range)

    return current, upcoming


def smart_panel(df, busy_slots):
    active = get_active_students(df)
    almost = active[(active["Tổng buổi"] - active["Đã học"]) <= 2] if not active.empty else active
    unpaid = len(active[active["Đã nhận tiền dạy"] == "Chưa"]) if not active.empty else 0
    teacher_debt = teacher_remaining_total()
    current, upcoming = current_and_next_slot(busy_slots)

    if current:
        current_text = f"Ca đang diễn ra: {current[0]} • {current[1]}"
    elif upcoming:
        current_text = f"Ca tiếp theo: {upcoming[0]} • {upcoming[1]}"
    else:
        current_text = "Hôm nay không còn ca tiếp theo."

    st.markdown(
        f"""
        <div class="smart-panel">
            <div class="smart-title">🔔 Thông báo thông minh</div>
            <div class="smart-item">🕒 {now_vn().strftime('%H:%M:%S')} GMT+7 — {current_text}</div>
            <div class="smart-item">⚠️ {len(almost)} học viên sắp hết khóa trong 1–2 buổi.</div>
            <div class="smart-item">💰 {unpaid} học viên chưa nhận tiền dạy.</div>
            <div class="smart-item">👨‍🏫 Tiền giáo viên còn {teacher_debt} học viên chưa thanh toán.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def today_timeline(df, busy_slots):
    today = current_day_name()
    html = '<div class="report-card"><div class="report-title">📅 Lịch dạy hôm nay</div>'

    for ca, time_range in CAS.items():
        slot = f"{today} - {ca}"
        count = len(get_students_by_slot(df, today, ca))
        status, icon, cls = ca_status(time_range)

        if slot in busy_slots:
            label = "Bận"
            pill_class = "pill-busy"
            icon = "🔴"
        else:
            label = status
            pill_class = f"pill-{cls}"

        html += f"""
        <div class="timeline-row">
            <div class="timeline-time">{time_range.replace(" - ", "<br>")}</div>
            <div>
                <div class="timeline-main">{ca}</div>
                <div class="timeline-sub">{count} học viên</div>
            </div>
            <span class="pill {pill_class}">{icon} {label}</span>
        </div>
        """

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def near_finish_report(df):
    active = get_active_students(df)
    st.markdown('<div class="report-card"><div class="report-title">⚠️ Học viên sắp kết thúc</div>', unsafe_allow_html=True)

    if active.empty:
        st.info("Chưa có học viên đang học.")
        st.markdown("</div>", unsafe_allow_html=True)
        return

    temp = active.copy()
    temp["Còn lại"] = temp["Tổng buổi"] - temp["Đã học"]
    temp = temp[temp["Còn lại"] <= 2].sort_values(["Còn lại", "Họ tên"]).head(8)

    if temp.empty:
        st.success("Không có học viên nào sắp hết buổi.")
    else:
        for _, row in temp.iterrows():
            st.markdown(
                f"""
                <div class="todo-item">
                    <div>{row['Họ tên']}<div class="timeline-sub">{row['Khóa học']} • {row['Đã học']}/{row['Tổng buổi']} buổi</div></div>
                    <div class="todo-pill">Còn {int(row['Còn lại'])} buổi</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)


def teacher_report():
    tdf = load_teacher_fees()
    st.markdown('<div class="report-card"><div class="report-title">👨‍🏫 Tiền giáo viên</div>', unsafe_allow_html=True)

    for _, row in tdf.iterrows():
        total = int(row["Tổng học viên"])
        paid = int(row["Đã thanh toán"])
        remain = max(total - paid, 0)
        pct = 0 if total == 0 else int(paid / total * 100)

        st.markdown(
            f"""
            <div class="todo-item">
                <div>Thầy {row['Thầy']}<div class="timeline-sub">Đã thanh toán {paid}/{total}</div>
                <div class="bar-wrap"><div class="bar-fill" style="width:{pct}%"></div></div></div>
                <div class="todo-pill">Còn {remain}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


def page_dashboard(df, busy_slots):
    topbar()

    active = get_active_students(df)
    finished = get_finished_students(df)
    today = current_day_name()
    today_students = sum(len(get_students_by_slot(df, today, ca)) for ca in CAS)
    almost = len(active[(active["Tổng buổi"] - active["Đã học"]) <= 2]) if not active.empty else 0
    unpaid = len(active[active["Đã nhận tiền dạy"] == "Chưa"]) if not active.empty else 0
    teacher_debt = teacher_remaining_total()

    c1, c2, c3 = st.columns(3)
    with c1:
        summary_card("Đang học", len(active), "👨‍🎓", "Học viên còn trong lịch", "blue")
    with c2:
        summary_card("Kết thúc khóa", len(finished), "🎓", "Tự ẩn khỏi lịch dạy", "green")
    with c3:
        summary_card("Học viên hôm nay", today_students, "📅", today, "teal")

    c4, c5, c6 = st.columns(3)
    with c4:
        summary_card("Sắp hết buổi", almost, "⚠️", "Còn 1–2 buổi", "orange")
    with c5:
        summary_card("Chưa nhận tiền", unpaid, "💰", "Cần kiểm tra", "red")
    with c6:
        summary_card("Tiền GV còn", teacher_debt, "👨‍🏫", "HV chưa thanh toán GV", "purple")

    smart_panel(df, busy_slots)

    left, right = st.columns([1.25, 0.85])
    with left:
        today_timeline(df, busy_slots)
    with right:
        near_finish_report(df)
        teacher_report()

    st.markdown('<div class="quick-grid">', unsafe_allow_html=True)
    quick_items = [
        ("👨‍🎓", "Quản lý học viên"),
        ("📅", "Lịch dạy"),
        ("💰", "Học phí"),
        ("👨‍🏫", "Tiền giáo viên"),
        ("📋", "Điểm danh"),
        ("⚙️", "Cài đặt"),
    ]
    for icon, text in quick_items:
        st.markdown(f'<div class="quick-card"><div class="quick-icon">{icon}</div><div class="quick-text">{text}</div></div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def page_schedule(df, busy_slots):
    topbar()
    st.markdown('<div class="page-title">Lịch dạy</div>', unsafe_allow_html=True)
    st.info(f"Giờ Việt Nam: {now_vn().strftime('%H:%M:%S')} — app tự cập nhật mỗi 60 giây")

    day = st.selectbox("Chọn ngày", DAYS, index=DAYS.index(current_day_name()))

    for ca, time_range in CAS.items():
        slot = f"{day} - {ca}"
        count = len(get_students_by_slot(df, day, ca))
        status, icon, cls = ca_status(time_range)

        if slot in busy_slots:
            label = "Bận"
            pill_class = "pill-busy"
            icon = "🔴"
        else:
            label = status
            pill_class = f"pill-{cls}"

        left, right = st.columns([3, 1])
        with left:
            st.markdown(
                f"""
                <div class="slot-card">
                    <div class="slot-title">{ca} • {time_range}</div>
                    <div class="small">{day}</div>
                    <span class="pill {pill_class}">{icon} {label}</span>
                    <span class="pill pill-ok">{count} học viên</span>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with right:
            if st.button("Mở", key=f"open_{slot}", use_container_width=True):
                st.session_state["selected_day"] = day
                st.session_state["selected_ca"] = ca

    selected_day = st.session_state.get("selected_day", day)
    selected_ca = st.session_state.get("selected_ca", list(CAS.keys())[0])
    selected_slot = f"{selected_day} - {selected_ca}"

    st.markdown("---")
    st.markdown(f"<div class='page-title'>Chi tiết: {selected_slot} • {CAS[selected_ca]}</div>", unsafe_allow_html=True)

    if selected_slot in busy_slots:
        st.error("Ca này đang bận. Vào Cài đặt để mở lại.")
        return

    class_df = get_students_by_slot(df, selected_day, selected_ca)
    if class_df.empty:
        st.warning("Ca này chưa có học viên.")
        return

    for _, row in class_df.iterrows():
        student_card(row)

    with st.expander("Bảng điểm danh 12 buổi"):
        show_cols = ["Họ tên", "Ngày đăng ký", "Trạng thái khóa", "Đã học", "Tổng buổi"] + ATTENDANCE_COLS
        st.dataframe(class_df[show_cols], use_container_width=True, hide_index=True)

    checked = st.multiselect(
        "Chọn học viên đã học buổi này",
        class_df["Mã HV"].tolist(),
        format_func=lambda x: class_df.loc[class_df["Mã HV"] == x, "Họ tên"].values[0],
    )

    if st.button("✅ Điểm danh / ghi ngày hôm nay", use_container_width=True):
        for hv_id in checked:
            df = mark_attendance(df, hv_id)
        save_students(df)
        st.success(f"Đã ghi ngày {now_vn().strftime('%d/%m')} vào điểm danh.")
        st.rerun()


def page_students(df, busy_slots):
    topbar()
    st.markdown('<div class="page-title">Quản lý học viên</div>', unsafe_allow_html=True)

    with st.expander("➕ Thêm học viên mới", expanded=False):
        with st.form("add_student"):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input("Họ tên")
                phone = st.text_input("SĐT")
                course = st.selectbox("Khóa học", ["Ếch", "Sải", "Sải ôn ếch", "Khác"])
            with c2:
                register_date = st.date_input("Ngày đăng ký", value=now_vn().date())
                total = st.number_input("Tổng buổi", min_value=1, value=12)
                learned = st.number_input("Đã học", min_value=0, value=0)
                paid = st.checkbox("Đã nhận tiền dạy")

            note = st.text_area("Ghi chú")
            schedule = []
            for day_name in DAYS:
                available = [ca for ca in CAS if f"{day_name} - {ca}" not in busy_slots]
                selected = st.multiselect(day_name, available, key=f"add_{day_name}")
                schedule += [f"{day_name} - {ca}" for ca in selected]

            if st.form_submit_button("Lưu học viên", use_container_width=True):
                if not name.strip():
                    st.warning("Nhập họ tên trước.")
                elif not schedule:
                    st.warning("Chọn ít nhất một ca học.")
                else:
                    new = {
                        "Mã HV": make_student_id(df),
                        "Họ tên": name.strip(),
                        "SĐT": phone.strip(),
                        "Khóa học": course,
                        "Ngày đăng ký": register_date.strftime("%d/%m/%Y"),
                        "Lịch học": ", ".join(schedule),
                        "Tổng buổi": int(total),
                        "Đã học": int(learned),
                        "Trạng thái khóa": "Kết thúc" if int(learned) >= int(total) else "Đang học",
                        "Đã nhận tiền dạy": "Có" if paid else "Chưa",
                        "Ghi chú": note.strip(),
                    }
                    for col in ATTENDANCE_COLS:
                        new[col] = ""
                    save_students(pd.concat([df, pd.DataFrame([new])], ignore_index=True))
                    st.success("Đã thêm học viên.")
                    st.rerun()

    search = st.text_input("Tìm theo tên hoặc số điện thoại")
    show = df.copy()
    if search.strip():
        show = show[
            show["Họ tên"].astype(str).str.contains(search, case=False, na=False)
            | show["SĐT"].astype(str).str.contains(search, case=False, na=False)
        ]

    for _, row in show.iterrows():
        student_card(row)

    with st.expander("📋 Toàn bộ điểm danh"):
        show_cols = ["Mã HV", "Họ tên", "Ngày đăng ký", "Trạng thái khóa", "Đã học", "Tổng buổi"] + ATTENDANCE_COLS
        st.dataframe(df[show_cols], use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown('<div class="page-title">Sửa / Kết thúc / Xóa học viên</div>', unsafe_allow_html=True)

    if not df.empty:
        sid = st.selectbox(
            "Chọn học viên",
            df["Mã HV"].tolist(),
            format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0],
        )
        idx = df[df["Mã HV"] == sid].index[0]

        with st.form("edit_student"):
            c1, c2 = st.columns(2)
            with c1:
                ename = st.text_input("Họ tên", df.loc[idx, "Họ tên"])
                ephone = st.text_input("SĐT", str(df.loc[idx, "SĐT"]))
                options = ["Ếch", "Sải", "Sải ôn ếch", "Khác"]
                old_course = df.loc[idx, "Khóa học"]
                ecourse = st.selectbox("Khóa", options, index=options.index(old_course) if old_course in options else 3)
                ereg = st.text_input("Ngày đăng ký", str(df.loc[idx, "Ngày đăng ký"]))
            with c2:
                etotal = st.number_input("Tổng buổi", min_value=1, value=int(df.loc[idx, "Tổng buổi"]))
                elearned = st.number_input("Đã học", min_value=0, value=int(df.loc[idx, "Đã học"]))
                old_status = df.loc[idx, "Trạng thái khóa"]
                estatus = st.selectbox("Trạng thái khóa", ["Đang học", "Kết thúc"], index=1 if old_status == "Kết thúc" else 0)
                emoney = st.selectbox("Tiền dạy", ["Chưa", "Có"], index=1 if df.loc[idx, "Đã nhận tiền dạy"] == "Có" else 0)

            eschedule = st.text_area("Lịch học", str(df.loc[idx, "Lịch học"]))
            enote = st.text_area("Ghi chú", str(df.loc[idx, "Ghi chú"]))

            if st.form_submit_button("Cập nhật", use_container_width=True):
                final_status = "Kết thúc" if int(elearned) >= int(etotal) else estatus
                df.loc[idx, [
                    "Họ tên", "SĐT", "Khóa học", "Ngày đăng ký", "Lịch học",
                    "Tổng buổi", "Đã học", "Trạng thái khóa", "Đã nhận tiền dạy", "Ghi chú"
                ]] = [
                    ename, ephone, ecourse, ereg, eschedule,
                    int(etotal), int(elearned), final_status, emoney, enote
                ]
                save_students(df)
                st.success("Đã cập nhật.")
                st.rerun()

        if st.button("🎓 Kết thúc khóa học viên này", use_container_width=True):
            df.loc[df["Mã HV"] == sid, "Trạng thái khóa"] = "Kết thúc"
            save_students(df)
            st.success("Đã kết thúc khóa. Học viên sẽ không còn xuất hiện trong lịch dạy.")
            st.rerun()

        confirm = st.checkbox("Tôi xác nhận muốn xóa học viên này")
        if st.button("Xóa học viên", use_container_width=True):
            if confirm:
                save_students(df[df["Mã HV"] != sid])
                st.success("Đã xóa.")
                st.rerun()
            else:
                st.warning("Tick xác nhận trước khi xóa.")


def page_money(df):
    topbar()
    st.markdown('<div class="page-title">Học phí & tiền dạy</div>', unsafe_allow_html=True)
    if df.empty:
        st.warning("Chưa có học viên.")
        return

    unpaid = df[df["Đã nhận tiền dạy"] == "Chưa"]
    paid = df[df["Đã nhận tiền dạy"] == "Có"]

    c1, c2 = st.columns(2)
    with c1:
        summary_card("Chưa nhận", len(unpaid), "🔴", "Cần kiểm tra", "red")
    with c2:
        summary_card("Đã nhận", len(paid), "🟢", "Đã hoàn tất", "green")

    sid = st.selectbox("Chọn học viên", df["Mã HV"].tolist(), format_func=lambda x: df.loc[df["Mã HV"] == x, "Họ tên"].values[0])
    current = df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"].values[0]
    status = st.radio("Trạng thái", ["Chưa", "Có"], horizontal=True, index=1 if current == "Có" else 0)

    if st.button("Lưu trạng thái", use_container_width=True):
        df.loc[df["Mã HV"] == sid, "Đã nhận tiền dạy"] = status
        save_students(df)
        st.success("Đã lưu.")
        st.rerun()

    st.dataframe(
        df[["Họ tên", "Khóa học", "Trạng thái khóa", "Đã học", "Tổng buổi", "Đã nhận tiền dạy"]],
        use_container_width=True,
        hide_index=True,
    )


def page_teacher_fee():
    topbar()
    st.markdown('<div class="page-title">Quản lý tiền thầy</div>', unsafe_allow_html=True)
    tdf = load_teacher_fees()
    st.info("Có học viên mới: bấm +1 học viên. Khi thanh toán thêm: bấm Thanh toán 1 HV.")

    for teacher in ["Đạt", "Long"]:
        idx = tdf[tdf["Thầy"] == teacher].index[0]
        total = int(tdf.loc[idx, "Tổng học viên"])
        paid = int(tdf.loc[idx, "Đã thanh toán"])
        remain = max(total - paid, 0)
        pct = 0 if total == 0 else int(paid / total * 100)

        st.markdown(
            f"""
            <div class="student-card">
                <div class="student-name">👨‍🏫 Thầy {teacher}</div>
                <div class="small">Tổng học viên: <b>{total}</b> • Đã thanh toán: <b>{paid}</b> • Còn lại: <b>{remain}</b></div>
                <div class="progress-wrap"><div class="progress-bar" style="width:{pct}%"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("+1 học viên", key=f"add_{teacher}", use_container_width=True):
                tdf.loc[idx, "Tổng học viên"] = total + 1
                save_teacher_fees(tdf)
                st.rerun()
        with c2:
            if st.button("Thanh toán 1 HV", key=f"pay_{teacher}", use_container_width=True, disabled=paid >= total):
                tdf.loc[idx, "Đã thanh toán"] = min(paid + 1, total)
                save_teacher_fees(tdf)
                st.rerun()
        with c3:
            if st.button("Trừ 1 thanh toán", key=f"undo_{teacher}", use_container_width=True, disabled=paid <= 0):
                tdf.loc[idx, "Đã thanh toán"] = max(paid - 1, 0)
                save_teacher_fees(tdf)
                st.rerun()

        with st.expander(f"Chỉnh tay thầy {teacher}"):
            ntotal = st.number_input(f"Tổng học viên - {teacher}", min_value=0, value=total, key=f"total_{teacher}")
            npaid = st.number_input(f"Đã thanh toán - {teacher}", min_value=0, max_value=int(ntotal), value=min(paid, int(ntotal)), key=f"paid_{teacher}")
            if st.button(f"Lưu thầy {teacher}", key=f"save_{teacher}", use_container_width=True):
                tdf.loc[idx, "Tổng học viên"] = int(ntotal)
                tdf.loc[idx, "Đã thanh toán"] = int(npaid)
                save_teacher_fees(tdf)
                st.rerun()

    tdf["Còn lại"] = tdf["Tổng học viên"] - tdf["Đã thanh toán"]
    st.dataframe(tdf, use_container_width=True, hide_index=True)


def page_settings(busy_slots):
    topbar()
    st.markdown('<div class="page-title">Cài đặt lịch bận</div>', unsafe_allow_html=True)
    new_slots = set()

    for day in DAYS:
        st.markdown(f"### {day}")
        cols = st.columns(2)
        for i, ca in enumerate(CAS):
            slot = f"{day} - {ca}"
            with cols[i % 2]:
                if st.checkbox(f"{ca} • {CAS[ca]}", value=slot in busy_slots, key=f"busy_{slot}"):
                    new_slots.add(slot)

    if st.button("Lưu lịch bận", use_container_width=True):
        save_busy_slots(new_slots)
        st.success("Đã lưu lịch bận.")
        st.rerun()
