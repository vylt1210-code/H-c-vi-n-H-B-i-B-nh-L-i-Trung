# BLT Manager Clean

Bản cấu trúc sạch, tách file để dễ bảo trì.

## Chạy local
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Dữ liệu
App tự đọc dữ liệu cũ nếu bạn để `hoc_vien.csv`, `lich_ban.csv`, `hoc_phi_thay.csv` ở thư mục gốc hoặc trong thư mục `data/`.

## Tính năng
- Dashboard báo cáo tổng quát
- Lịch dạy realtime giờ Việt Nam
- Điểm danh 12 buổi tự ghi ngày
- Kết thúc khóa tự ẩn khỏi lịch
- Học phí và tiền giáo viên
- Cài đặt lịch bận
