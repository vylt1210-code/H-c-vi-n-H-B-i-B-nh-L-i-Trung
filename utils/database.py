import pandas as pd
from datetime import datetime

from .constants import (
    BASE,
    DATA_DIR,
    VN_TZ,
    DAYS,
    CAS,
    ATTENDANCE_COLS,
    STUDENT_COLUMNS,
    TEACHER_COLUMNS,
)


def resolve_file(name: str):
    data_file = DATA_DIR / name
    root_file = BASE / name
    if data_file.exists():
        return data_file
    if root_file.exists():
        return root_file
    return data_file


DATA_FILE = resolve_file("hoc_vien.csv")
BUSY_FILE = resolve_file("lich_ban.csv")
TEACHER_FILE = resolve_file("hoc_phi_thay.csv")


def now_vn():
    return datetime.now(VN_TZ)


def today_full():
    return now_vn().strftime("%d/%m/%Y")


def today_short():
    return now_vn().strftime("%d/%m")


def current_day_name():
    return DAYS[now_vn().weekday()]


def load_students():
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=STUDENT_COLUMNS)

    for col in STUDENT_COLUMNS:
        if col not in df.columns:
            if col == "Tổng buổi":
                df[col] = 12
            elif col == "Đã học":
                df[col] = 0
            elif col == "Đã nhận tiền dạy":
                df[col] = "Chưa"
            elif col == "Trạng thái khóa":
                df[col] = "Đang học"
            elif col == "Ngày đăng ký":
                df[col] = today_full()
            else:
                df[col] = ""

    if not df.empty:
        df["Mã HV"] = pd.to_numeric(df["Mã HV"], errors="coerce")
        used_ids = set(pd.to_numeric(df["Mã HV"], errors="coerce").dropna().astype(int).tolist())
        next_id = 1
        for idx in df[df["Mã HV"].isna()].index:
            while next_id in used_ids:
                next_id += 1
            df.loc[idx, "Mã HV"] = next_id
            used_ids.add(next_id)

        df["Mã HV"] = df["Mã HV"].astype(int)
        df["Tổng buổi"] = pd.to_numeric(df["Tổng buổi"], errors="coerce").fillna(12).astype(int)
        df["Đã học"] = pd.to_numeric(df["Đã học"], errors="coerce").fillna(0).astype(int)
        df["Đã nhận tiền dạy"] = (
            df["Đã nhận tiền dạy"]
            .fillna("Chưa")
            .replace({True: "Có", False: "Chưa"})
        )
        df["Trạng thái khóa"] = df["Trạng thái khóa"].fillna("Đang học")
        df.loc[df["Đã học"] >= df["Tổng buổi"], "Trạng thái khóa"] = "Kết thúc"

        for col in ATTENDANCE_COLS:
            df[col] = df[col].fillna("").astype(str).replace("nan", "")

    return df[STUDENT_COLUMNS]


def save_students(df):
    df.to_csv(DATA_FILE, index=False, encoding="utf-8-sig")


def load_busy_slots():
    if BUSY_FILE.exists():
        df = pd.read_csv(BUSY_FILE)
        if "Slot" in df.columns:
            return set(df["Slot"].dropna().astype(str).tolist())
    return set()


def save_busy_slots(slots):
    pd.DataFrame({"Slot": sorted(list(slots))}).to_csv(BUSY_FILE, index=False, encoding="utf-8-sig")


def load_teacher_fees():
    if TEACHER_FILE.exists():
        df = pd.read_csv(TEACHER_FILE)
    else:
        df = pd.DataFrame([
            {"Thầy": "Đạt", "Tổng học viên": 0, "Đã thanh toán": 0},
            {"Thầy": "Long", "Tổng học viên": 0, "Đã thanh toán": 0},
        ])

    for col in TEACHER_COLUMNS:
        if col not in df.columns:
            df[col] = 0 if col != "Thầy" else ""

    for teacher in ["Đạt", "Long"]:
        if teacher not in df["Thầy"].astype(str).tolist():
            df = pd.concat([
                df,
                pd.DataFrame([{"Thầy": teacher, "Tổng học viên": 0, "Đã thanh toán": 0}]),
            ], ignore_index=True)

    df["Tổng học viên"] = pd.to_numeric(df["Tổng học viên"], errors="coerce").fillna(0).astype(int)
    df["Đã thanh toán"] = pd.to_numeric(df["Đã thanh toán"], errors="coerce").fillna(0).astype(int)
    df.loc[df["Đã thanh toán"] > df["Tổng học viên"], "Đã thanh toán"] = df["Tổng học viên"]
    return df[TEACHER_COLUMNS]


def save_teacher_fees(df):
    df.to_csv(TEACHER_FILE, index=False, encoding="utf-8-sig")


def make_student_id(df):
    if df.empty:
        return 1
    max_id = pd.to_numeric(df["Mã HV"], errors="coerce").max()
    return 1 if pd.isna(max_id) else int(max_id) + 1


def get_active_students(df):
    if df.empty:
        return df.copy()
    return df[df["Trạng thái khóa"].astype(str) != "Kết thúc"].copy()


def get_finished_students(df):
    if df.empty:
        return df.copy()
    return df[df["Trạng thái khóa"].astype(str) == "Kết thúc"].copy()


def get_students_by_slot(df, day, ca, include_finished=False):
    if df.empty:
        return pd.DataFrame(columns=STUDENT_COLUMNS)

    slot = f"{day} - {ca}"
    matched = df[df["Lịch học"].astype(str).str.contains(slot, na=False, regex=False)].copy()

    if not include_finished and "Trạng thái khóa" in matched.columns:
        matched = matched[matched["Trạng thái khóa"].astype(str) != "Kết thúc"].copy()

    return matched


def ca_status(time_range):
    current = now_vn().time()
    start_s, end_s = time_range.split(" - ")
    start = datetime.strptime(start_s, "%H:%M").time()
    end = datetime.strptime(end_s, "%H:%M").time()

    if start <= current < end:
        return "Đang diễn ra", "now", "●"
    if current < start:
        return "Sắp tới", "soon", "●"
    return "Đã qua", "past", "●"


def mark_attendance(df, hv_id):
    idx = df[df["Mã HV"] == hv_id].index
    if len(idx) == 0:
        return df

    idx = idx[0]
    learned = int(df.loc[idx, "Đã học"])
    total = int(df.loc[idx, "Tổng buổi"])

    if learned >= total:
        df.loc[idx, "Trạng thái khóa"] = "Kết thúc"
        return df

    for col in ATTENDANCE_COLS:
        value = str(df.loc[idx, col]).strip()
        if value == "" or value.lower() == "nan":
            df.loc[idx, col] = today_short()
            break

    new_learned = learned + 1
    df.loc[idx, "Đã học"] = new_learned

    if new_learned >= total:
        df.loc[idx, "Trạng thái khóa"] = "Kết thúc"

    return df


def progress_pct(row):
    total = max(int(row.get("Tổng buổi", 12)), 1)
    done = int(row.get("Đã học", 0))
    return min(100, int(done / total * 100))


def teacher_remaining_total():
    tdf = load_teacher_fees()
    return int((tdf["Tổng học viên"] - tdf["Đã thanh toán"]).clip(lower=0).sum())
