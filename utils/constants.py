from pathlib import Path
from zoneinfo import ZoneInfo

BASE = Path(__file__).resolve().parents[1]
DATA_DIR = BASE / "data"
ASSETS = BASE / "assets"
DATA_DIR.mkdir(exist_ok=True)

VN_TZ = ZoneInfo("Asia/Ho_Chi_Minh")

DAYS = ["Thứ 2", "Thứ 3", "Thứ 4", "Thứ 5", "Thứ 6", "Thứ 7", "Chủ nhật"]

CAS = {
    "Ca 1": "08:00 - 09:00",
    "Ca 2": "09:00 - 10:00",
    "Ca 3": "10:00 - 11:00",
    "Ca 4": "13:00 - 14:00",
    "Ca 5": "14:00 - 15:00",
    "Ca 6": "15:00 - 16:00",
    "Ca 7": "16:00 - 17:00",
    "Ca 8": "17:00 - 18:00",
    "Ca 9": "18:00 - 19:00",
    "Ca 10": "19:00 - 20:00",
}

ATTENDANCE_COLS = [f"Buổi {i}" for i in range(1, 13)]

STUDENT_COLUMNS = [
    "Mã HV",
    "Họ tên",
    "SĐT",
    "Khóa học",
    "Ngày đăng ký",
    "Lịch học",
    "Tổng buổi",
    "Đã học",
    "Trạng thái khóa",
    "Đã nhận tiền dạy",
    "Ghi chú",
] + ATTENDANCE_COLS

TEACHER_COLUMNS = ["Thầy", "Tổng học viên", "Đã thanh toán"]
