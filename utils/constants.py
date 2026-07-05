from pathlib import Path

DATA_FILE = Path('hoc_vien.csv')
BUSY_FILE = Path('lich_ban.csv')
ASSETS_DIR = Path('assets')
LOGO_PATH = ASSETS_DIR / 'logo.png'
FAVICON_PATH = ASSETS_DIR / 'favicon.png'
BANNER_PATH = ASSETS_DIR / 'banner.jpg'
BACKGROUND_PATH = ASSETS_DIR / 'background.jpg'
DASHBOARD_IMAGE_PATH = ASSETS_DIR / 'dashboard.jpg'
POOL_IMAGE_PATH = ASSETS_DIR / 'pool.jpg'
STUDENTS_IMAGE_PATH = ASSETS_DIR / 'students.jpg'

DAYS = ['Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7', 'Chủ nhật']
CAS = {
    'Ca 1': '08:00 - 09:00',
    'Ca 2': '09:00 - 10:00',
    'Ca 3': '10:00 - 11:00',
    'Ca 4': '13:00 - 14:00',
    'Ca 5': '14:00 - 15:00',
    'Ca 6': '15:00 - 16:00',
    'Ca 7': '16:00 - 17:00',
    'Ca 8': '17:00 - 18:00',
    'Ca 9': '18:00 - 19:00',
    'Ca 10': '19:00 - 20:00',
}
COLUMNS = [
    'Mã HV', 'Họ tên', 'SĐT', 'Khóa học', 'Lịch học',
    'Tổng buổi', 'Đã học', 'Đã nhận tiền dạy', 'Ngày bắt đầu', 'Ghi chú'
]
COURSES = ['Ếch', 'Sải', 'Sải ôn ếch', 'Khác']
