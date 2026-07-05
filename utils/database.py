import pandas as pd
from .constants import DATA_FILE, BUSY_FILE, COLUMNS


def load_students() -> pd.DataFrame:
    if DATA_FILE.exists():
        df = pd.read_csv(DATA_FILE)
    else:
        df = pd.DataFrame(columns=COLUMNS)

    for col in COLUMNS:
        if col not in df.columns:
            if col == 'Tổng buổi':
                df[col] = 12
            elif col == 'Đã học':
                df[col] = 0
            elif col == 'Đã nhận tiền dạy':
                df[col] = 'Chưa'
            else:
                df[col] = ''

    if len(df) > 0:
        df['Mã HV'] = pd.to_numeric(df['Mã HV'], errors='coerce')
        df['Mã HV'] = df['Mã HV'].fillna(pd.Series(range(1, len(df)+1))).astype(int)
        df['Tổng buổi'] = pd.to_numeric(df['Tổng buổi'], errors='coerce').fillna(12).astype(int)
        df['Đã học'] = pd.to_numeric(df['Đã học'], errors='coerce').fillna(0).astype(int)
        df['Đã học'] = df['Đã học'].clip(lower=0)
        df['Đã nhận tiền dạy'] = df['Đã nhận tiền dạy'].fillna('Chưa')
        df['Ngày bắt đầu'] = df['Ngày bắt đầu'].fillna('')
        df['Ghi chú'] = df['Ghi chú'].fillna('')
    return df[COLUMNS]


def save_students(df: pd.DataFrame) -> None:
    df.to_csv(DATA_FILE, index=False, encoding='utf-8-sig')


def load_busy_slots() -> set[str]:
    if BUSY_FILE.exists():
        df = pd.read_csv(BUSY_FILE)
        if 'Slot' in df.columns:
            return set(df['Slot'].dropna().astype(str).tolist())
    return set()


def save_busy_slots(slots: set[str]) -> None:
    pd.DataFrame({'Slot': sorted(list(slots))}).to_csv(BUSY_FILE, index=False, encoding='utf-8-sig')


def make_student_id(df: pd.DataFrame) -> int:
    if df.empty or 'Mã HV' not in df.columns:
        return 1
    max_id = pd.to_numeric(df['Mã HV'], errors='coerce').max()
    return 1 if pd.isna(max_id) else int(max_id) + 1


def get_students_by_slot(df: pd.DataFrame, day: str, ca: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=COLUMNS)
    slot = f'{day} - {ca}'
    return df[df['Lịch học'].astype(str).str.contains(slot, na=False, regex=False)].copy()


def schedule_count(df: pd.DataFrame, day: str, ca: str) -> int:
    return len(get_students_by_slot(df, day, ca))


def remaining_lessons(df: pd.DataFrame) -> pd.Series:
    if df.empty:
        return pd.Series(dtype=int)
    return df['Tổng buổi'].astype(int) - df['Đã học'].astype(int)


def highlight_done(row):
    remain = int(row['Tổng buổi']) - int(row['Đã học'])
    if remain <= 0:
        return ['background-color: #D8F3DC; color: #1B4332; font-weight: 700'] * len(row)
    if remain <= 2:
        return ['background-color: #FFF3BF; color: #7A4F01; font-weight: 600'] * len(row)
    return [''] * len(row)
