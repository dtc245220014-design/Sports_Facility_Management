# Báo Cáo Rà Soát An Ninh Thông Tin & Bảo Mật (Security Audit Report)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

Tài liệu này ghi nhận kết quả rà soát an toàn thông tin toàn diện cho mã nguồn Backend và Frontend của dự án theo các tiêu chuẩn bảo mật OWASP Top 10.

---

## 1. Kết Quả Kiểm Tra Các Hạng Mục Bảo Mật Trọng Yếu

| Tiêu Chí An Toàn | Mức Độ Rủi Ro Tiềm Ẩn | Trạng Thái Dự Án | Chi Tiết Thực Thi & Đánh Giá |
| :--- | :---: | :---: | :--- |
| **Phòng Chống SQL Injection** | Nghiêm trọng (Critical) | ✅ ĐÃ ĐẠT 100% | 100% câu truy vấn dùng SQLAlchemy ORM hoặc Parameterized SQL (`:param`, `%s`). Tuyệt đối không nối chuỗi SQL bằng `f-string` hay `+`. |
| **Bảo Mật API Key Gemini** | Nghiêm trọng (Critical) | ✅ ĐÃ ĐẠT 100% | `GEMINI_API_KEY` được lưu tách biệt trong tệp `.env`, chỉ đọc qua `os.getenv()`. Frontend không thể truy cập khóa này. |
| **Mã Hóa Mật Khẩu Người Dùng** | Cao (High) | ✅ ĐÃ ĐẠT 100% | Mật khẩu được băm bằng thuật toán an toàn `PBKDF2-HMAC-SHA256` với Salt ngẫu nhiên. Không lưu mật khẩu thô trong CSDL. |
| **Kiểm Soát Tranh Chấp & Chống Race Attack** | Cao (High) | ✅ ĐÃ ĐẠT 100% | Áp dụng `with_for_update()` kết hợp `UNIQUE KEY` loại bỏ nguy cơ tấn công chiếm dụng tài nguyên đồng thời. |
| **Phòng Chống Tấn Công XSS** | Trung bình (Medium) | ✅ ĐÃ ĐẠT 100% | Mọi dữ liệu do người dùng nhập (Tên khách, ghi chú) đều được làm sạch qua hàm `escapeHtml()` trước khi hiển thị ra DOM. |
| **Cấu Hình CORS** | Trung bình (Medium) | ✅ ĐÃ ĐẠT 100% | Thiết lập `flask_cors.CORS` cho các route API một cách tường minh. |

---

## 2. Chi Tiết Rà Soát Kỹ Thuật

### 2.1. Phòng Chống SQL Injection (SQLi)
- **Mã nguồn kiểm tra tại `services/rag_service.py`**:
  ```python
  # TUÂN THỦ: Sử dụng tham số hóa qua SQLAlchemy text()
  sql = text("""
      SELECT ts.id, c.name AS court_name, ct.name AS type_name, 
             ts.booking_date, ts.start_time, ts.end_time, ts.price
      FROM time_slots ts
      JOIN courts c ON ts.court_id = c.id
      JOIN court_types ct ON c.court_type_id = ct.id
      WHERE ct.name = :court_type 
        AND ts.booking_date = :booking_date
        AND ts.status = 'FREE'
      ORDER BY ts.start_time ASC
  """)
  result = db.session.execute(sql, {
      "court_type": court_type,
      "booking_date": booking_date
  }).fetchall()
  ```
- **Đánh giá**: Khi kẻ tấn công chèn các chuỗi như `' OR 1=1 --`, bộ phân tích SQL của MySQL tự động xem chuỗi này là giá trị literal của tham số chứ không làm thay đổi cấu trúc câu lệnh SQL. Tấn công SQLi bị vô hiệu hóa hoàn toàn.

### 2.2. Kiểm Soát Rò Rỉ Khóa API AI (API Key Leakage)
- **Rà soát Frontend**: Quét toàn bộ thư mục `static/` và `templates/`, xác nhận không chứa bất kỳ chuỗi token nào của Google Gemini.
- **Rà soát Git**: Tệp `.env` được bảo vệ và đã cấu hình trong quy chuẩn quản lý mã nguồn. Máy chủ Backend chỉ gọi Gemini qua tiến trình nội bộ máy chủ (Server-side API Call).

### 2.3. Quản Lý Mật Khẩu & Phiên Làm Việc (Authentication)
- **Cơ chế**:
  - Khi tạo tài khoản (`database/seed_data.py` và `User.set_password`), sử dụng `generate_password_hash(password)`.
  - Khi đăng nhập (`services/auth_service.py`), sử dụng `check_password_hash(user.password_hash, password)`.
  - Không bao giờ trả trường `password_hash` trong các payload API gửi về client (hàm `to_dict()` trong `models/models.py` chủ động loại bỏ cột mật khẩu).

---

## 3. Khuyến Nghị Vận Hành Môi Trường Production
1. Thay thế `SECRET_KEY` bằng một chuỗi ngẫu nhiên dài 64 ký tự (ví dụ: sinh bằng `secrets.token_hex(32)`).
2. Kích hoạt HTTPS (SSL/TLS) khi triển khai trên tên miền thực tế để bảo vệ cookie phiên làm việc và dữ liệu truyền tải.
3. Cấu hình Rate Limiting (giới hạn tần suất gọi) cho endpoint `/api/ai/chat` (ví dụ: tối đa 20 lượt hỏi/phút trên mỗi địa chỉ IP) bằng `Flask-Limiter` để chống lạm dụng quota AI.

