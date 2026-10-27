# Đặc Tả Tài Liệu RESTful API (API Specification)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

---

## 1. Quy Chuẩn Chung
- **Base URL**: `http://localhost:5000`
- **Content-Type**: `application/json`
- **Quy ước mã phản hồi (HTTP Status Codes)**:
  - `200 OK`: Truy vấn hoặc cập nhật thành công.
  - `201 Created`: Tạo mới thành công (Đặt sân).
  - `400 Bad Request`: Thiếu tham số hoặc dữ liệu không hợp lệ.
  - `401 Unauthorized`: Sai tài khoản hoặc chưa đăng nhập.
  - `404 Not Found`: Tài nguyên không tồn tại.
  - `409 Conflict`: Xung đột tranh chấp đồng thời (Khung giờ đã bị người khác đặt).
  - `500 Internal Server Error`: Lỗi máy chủ nội bộ.

---

## 2. Nhóm API Xác Thực (Authentication API)

### 2.1. Đăng Nhập
- **Endpoint**: `POST /api/auth/login`
- **Mô tả**: Đăng nhập tài khoản Quản lý hoặc Nhân viên.
- **Request Body**:
  ```json
  {
    "username": "staff1",
    "password": "staff123"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Đăng nhập thành công với vai trò STAFF",
    "user": {
      "id": 2,
      "username": "staff1",
      "full_name": "Trần Thị Thu Ngân",
      "role": "STAFF"
    }
  }
  ```

### 2.2. Kiểm Tra Phiên Đăng Nhập Hiện Tại
- **Endpoint**: `GET /api/auth/me`
- **Response (200 OK)**:
  ```json
  {
    "authenticated": true,
    "user": { "id": 2, "username": "staff1", "role": "STAFF" }
  }
  ```

---

## 3. Nhóm API Quản Lý Sân & Khung Giờ (Courts & Slots API)

### 3.1. Danh Sách Loại Sân
- **Endpoint**: `GET /api/court-types`
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": [
      { "id": 1, "name": "Sân bóng 7 người", "description": "Sân cỏ nhân tạo 7 người tiêu chuẩn mini FIFA" },
      { "id": 3, "name": "Sân Cầu lông", "description": "Sân thảm chuyên dụng chống trơn trượt" }
    ]
  }
  ```

### 3.2. Tra Cứu Sơ Đồ Khung Giờ
- **Endpoint**: `GET /api/slots?date=2026-09-11&court_type_id=1`
- **Tham số truy vấn**:
  - `date`: Ngày cần tra cứu (YYYY-MM-DD).
  - `court_type_id` (Tùy chọn): Lọc theo loại sân.
  - `status` (Tùy chọn): `FREE`, `BOOKED`, `MAINTENANCE`.
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "data": [
      {
        "id": 101,
        "court_id": 1,
        "court_name": "Sân bóng 7 - A",
        "court_type_name": "Sân bóng 7 người",
        "booking_date": "2026-09-11",
        "start_time": "19:00:00",
        "end_time": "20:30:00",
        "price": 500000.0,
        "status": "FREE"
      }
    ]
  }
  ```

### 3.3. Chuyển Trạng Thái Bảo Trì Sân
- **Endpoint**: `PUT /api/courts/<court_id>/maintenance`
- **Request Body**:
  ```json
  { "is_maintenance": true }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Cập nhật trạng thái sân thành MAINTENANCE thành công"
  }
  ```

---

## 4. Nhóm API Quản Lý Đặt Sân (Bookings API)

### 4.1. Đặt Sân Mới (Pessimistic Lock)
- **Endpoint**: `POST /api/bookings`
- **Mô tả**: Bắt đầu transaction khóa dòng `time_slots`.
- **Request Body**:
  ```json
  {
    "slot_id": 101,
    "customer_name": "Nguyễn Văn Tuấn",
    "customer_phone": "0988776655",
    "deposit_amount": 200000,
    "note": "Chuẩn bị bóng thi đấu số 5"
  }
  ```
- **Response Thành Công (201 Created)**:
  ```json
  {
    "success": true,
    "booking": {
      "id": 25,
      "slot_id": 101,
      "customer_name": "Nguyễn Văn Tuấn",
      "customer_phone": "0988776655",
      "deposit_amount": 200000.0,
      "total_price": 500000.0,
      "remaining_amount": 300000.0,
      "status": "CONFIRMED",
      "payment_status": "DEPOSITED"
    }
  }
  ```
- **Response Trùng Lịch (409 Conflict)**:
  ```json
  {
    "success": false,
    "message": "Khung giờ này vừa được người khác đặt hoặc đang bảo trì! Vui lòng chọn khung giờ khác."
  }
  ```

### 4.2. Đổi Lịch Thi Đấu
- **Endpoint**: `PUT /api/bookings/<booking_id>/reschedule`
- **Request Body**:
  ```json
  { "new_slot_id": 105 }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Đổi lịch thi đấu thành công!"
  }
  ```

### 4.3. Hủy Lịch Thi Đấu
- **Endpoint**: `PUT /api/bookings/<booking_id>/cancel`
- **Request Body**:
  ```json
  { "reason": "Trời mưa to khách xin hủy" }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "message": "Hủy lịch thành công. Hủy trước 24h -> Hoàn 100% cọc"
  }
  ```

---

## 5. Nhóm API Trí Tuệ Nhân Tạo (AI RAG & Fallback API)

### 5.1. Chatbot Tư Vấn Khung Giờ (RAG)
- **Endpoint**: `POST /api/ai/chat`
- **Request Body**:
  ```json
  {
    "message": "Khách muốn đặt sân bóng 7 người tối thứ Sáu",
    "court_type": "Sân bóng 7 người",
    "date": "2026-09-11"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "reply": "Dạ chào anh/chị! Vào tối thứ Sáu (11/09/2026), bên em hiện còn 2 khung giờ trống cho Sân bóng 7 người:\n• Sân bóng 7 - A: 19:00 - 20:30 (Giá: 500,000 VNĐ)\n• Sân bóng 7 - B: 19:00 - 20:30 (Giá: 500,000 VNĐ)\nAnh/chị muốn đặt khung giờ nào để em hỗ trợ giữ chỗ ngay ạ?"
  }
  ```

### 5.2. AI Sinh Tin Nhắn Xác Nhận / Nhắc Lịch
- **Endpoint**: `POST /api/ai/generate-notification`
- **Request Body**:
  ```json
  {
    "booking_id": 25,
    "type": "confirmation"
  }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "notification_text": "🎉 [XÁC NHẬN ĐẶT SÂN]\nKính chào anh Nguyễn Văn Tuấn,\nSân bóng 7 - A đã ghi nhận lịch đấu của anh vào lúc 19:00 - 20:30 ngày 2026-09-11.\n• Tiền cọc đã nhận: 200,000 VNĐ\n• Còn lại: 300,000 VNĐ.\nAnh nhớ đến trước 15 phút để khởi động nhé!"
  }
  ```

### 5.3. AI Tóm Tắt Công Suất & Đề Xuất Khuyến Mại
- **Endpoint**: `POST /api/ai/occupancy-report`
- **Request Body**:
  ```json
  { "date": "2026-09-11" }
  ```
- **Response (200 OK)**:
  ```json
  {
    "success": true,
    "analysis": "1. Đánh giá: Tỷ lệ lấp đầy toàn cơ sở đạt 48.5%, tập trung cao điểm vào khung giờ 17:30 - 20:30.\n2. Giờ thấp điểm: Khung giờ sáng 06:00 - 09:00 tỷ lệ lấp đầy dưới 20%.\n3. Đề xuất khuyến mại:\n- Giảm 25% giá thuê cho các đội đặt cố định khung giờ 06:00 - 07:30.\n- Tặng miễn phí 1 két nước suối cho trận đấu khung giờ 16:00 - 17:30."
  }
  ```

---

## 6. Nhóm API Báo Cáo Thống Kê (Reports API)

- `GET /api/reports/revenue`: Báo cáo tổng doanh thu, tiền cọc và phân bổ doanh thu theo loại sân.
- `GET /api/reports/occupancy?date=YYYY-MM-DD`: Tỷ lệ lấp đầy toàn sân và chi tiết từng sân.
- `GET /api/reports/peak-hours`: Tần suất đặt và phân loại giờ `CAO ĐIỂM` / `THẤP ĐIỂM`.

