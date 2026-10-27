# Tiêu Chí Chấp Nhận Kỹ Thuật (Acceptance Criteria)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

Tài liệu này chuẩn hóa các kịch bản kiểm thử nghiệm thu theo định dạng **Given - When - Then (Gherkin format)** nhằm đảm bảo mọi tính năng được phát triển đúng theo yêu cầu thiết kế.

---

## 1. Nghiệp Vụ Đặt Sân & Kiểm Soát Tranh Chấp (Concurrency Control)

### AC-BOOK-01: Chống Trùng Lịch Bằng Pessimistic Transaction Lock (NFR-04, FR-07)
- **Given**: Khung giờ 19:00 - 20:30 Thứ Sáu (slot_id = 101) của Sân bóng 7 - A đang có trạng thái `FREE`.
- **When**: 10 yêu cầu đặt sân từ 10 luồng khác nhau cùng bấm gửi đến API `POST /api/bookings` tại cùng một thời điểm (trong cùng 1 millisecond).
- **Then**:
  1. Hệ thống mở giao dịch CSDL và thực thi câu lệnh khóa dòng `SELECT * FROM time_slots WHERE id = 101 FOR UPDATE`.
  2. Duy nhất 1 yêu cầu tới trước nhận mã trạng thái **HTTP 201 Created** kèm mã đơn `booking_id`. Trạng thái slot chuyển thành `BOOKED`.
  3. 9 yêu cầu còn lại bị phát hiện slot không còn `FREE`, giao dịch rollback và trả về mã lỗi **HTTP 409 Conflict** kèm thông điệp: *"Khung giờ này vừa được người khác đặt hoặc đang bảo trì! Vui lòng chọn khung giờ khác."*
  4. Trong cơ sở dữ liệu, chỉ có duy nhất 1 bản ghi `bookings` được tạo ra cho `slot_id = 101`.

### AC-DEPOSIT-01: Quy Định Tiền Đặt Cọc 30% - 50% (FR-07)
- **Given**: Khung giờ thuê sân có tổng đơn giá là 500.000 VNĐ.
- **When**:
  - *Trường hợp 1*: Nhân viên không nhập tiền cọc tùy chỉnh.
  - *Trường hợp 2*: Nhân viên nhập số tiền cọc là 100.000 VNĐ (dưới mức tối thiểu 30% = 150.000 VNĐ).
  - *Trường hợp 3*: Nhân viên nhập số tiền cọc là 250.000 VNĐ (nằm trong khoảng 30% - 50%).
- **Then**:
  - *Trường hợp 1*: Hệ thống tự động gán tiền cọc mặc định là 40% (200.000 VNĐ).
  - *Trường hợp 2*: Hệ thống tự động nâng mức cọc lên ngưỡng sàn hợp lệ là 30% (150.000 VNĐ).
  - *Trường hợp 3*: Hệ thống ghi nhận chính xác 250.000 VNĐ. Số tiền còn lại phải thanh toán sau trận là `500.000 - 250.000 = 250.000 VNĐ`.

---

## 2. Nghiệp Vụ Đổi Lịch & Hủy Lịch Thi Đấu

### AC-RESCHEDULE-01: Đổi Lịch Thi Đấu An Toàn Nguyên Tử (FR-08)
- **Given**: Đơn đặt sân #12 đang ở slot cũ (16:00 - 17:30) trạng thái `BOOKED`. Slot mới (17:30 - 19:00) đang ở trạng thái `FREE`.
- **When**: Nhân viên gọi API `PUT /api/bookings/12/reschedule` với `new_slot_id`.
- **Then**:
  1. Hệ thống bắt đầu transaction, khóa cả 2 dòng slot bằng `with_for_update()`.
  2. Slot cũ được cập nhật trở lại thành `FREE`.
  3. Slot mới được cập nhật thành `BOOKED`.
  4. Đơn đặt #12 cập nhật `slot_id = new_slot_id` và bổ sung ghi chú lịch sử đổi lịch.
  5. API trả về **HTTP 200 OK**.

### AC-CANCEL-01: Hủy Lịch Trước 24 Giờ - Hoàn Tiền Cọc (FR-08)
- **Given**: Trận đấu diễn ra vào 19:00 ngày 2028-05-01. Thời điểm khách báo hủy là 10:00 ngày 2028-04-20 (cách giờ thi đấu > 24 giờ).
- **When**: Nhân viên gọi API `PUT /api/bookings/<id>/cancel`.
- **Then**:
  1. Slot thi đấu được giải phóng về trạng thái `FREE`.
  2. Đơn đặt chuyển trạng thái thành `CANCELLED`.
  3. Cột `payment_status` chuyển thành `REFUNDED` (Hoàn trả tiền cọc cho khách).
  4. Hệ thống ghi chú: *"Hủy trước 24h -> Hoàn 100% cọc"*.

### AC-CANCEL-02: Hủy Lịch Muộn (<= 24 Giờ) - Phạt Giữ Lại Tiền Cọc (FR-08)
- **Given**: Trận đấu diễn ra vào 19:00 hôm nay. Thời điểm khách báo hủy là 16:00 cùng ngày (cách giờ thi đấu 3 giờ <= 24 giờ).
- **When**: Nhân viên gọi API `PUT /api/bookings/<id>/cancel`.
- **Then**:
  1. Slot thi đấu được giải phóng về `FREE` để có thể nhận khách vãng lai khác.
  2. Đơn đặt chuyển thành `CANCELLED`.
  3. Cột `payment_status` giữ nguyên `DEPOSITED` (sân giữ lại tiền cọc coi như khoản bồi thường thiệt hại).
  4. Hệ thống ghi chú: *"Hủy muộn (< 24h) -> Không hoàn cọc (Phạt vi phạm lịch)"*.

---

## 3. Nghiệp Vụ Bảo Trì Sân (Maintenance)

### AC-MAINT-01: Tự Động Khóa Khung Giờ Khi Sân Vào Bảo Trì (FR-06)
- **Given**: Sân bóng 7 - A có 5 khung giờ còn trống (`FREE`) trong những ngày tới.
- **When**: Quản lý bật công tắc chuyển trạng thái sân sang `MAINTENANCE`.
- **Then**:
  1. Trạng thái của Sân bóng 7 - A trong bảng `courts` chuyển thành `MAINTENANCE`.
  2. Toàn bộ 5 khung giờ `FREE` tương lai của sân này lập tức chuyển thành `MAINTENANCE` trên sơ đồ.
  3. Khách hàng hoặc nhân viên không thể bấm nút đặt vào các khung giờ này.

### AC-MAINT-02: Khôi Phục Khung Giờ Khi Kết Thúc Bảo Trì (FR-06)
- **Given**: Sân bóng 7 - A đang trong trạng thái `MAINTENANCE`.
- **When**: Quản lý bật công tắc chuyển trạng thái sân trở lại `ACTIVE`.
- **Then**:
  1. Toàn bộ các khung giờ đang có trạng thái `MAINTENANCE` của sân này tự động khôi phục về `FREE`.
  2. Sơ đồ hiển thị màu xanh lá và cho phép nhận đặt sân bình thường.

---

## 4. Nghiệp Vụ AI RAG & Dự Phòng Chịu Lỗi (Fault-Tolerance)

### AC-AI-01: Prompt Grounding Chống Bịa Thông Tin (FR-14, NFR-09)
- **Given**: CSDL ngày 2040-01-01 không có bất kỳ sân nào trống (`available_slots = []`).
- **When**: Khách hàng nhắn tin: *"Tôi muốn đặt sân bóng 7 người tối ngày 2040-01-01"*.
- **Then**:
  1. RAG Retriever truy vấn SQL và nhận về tập kết quả rỗng.
  2. Hệ thống phản hồi lịch sự: *"Rất tiếc, vào ngày 2040-01-01 hiện không còn Sân bóng 7 người nào trống. Bạn vui lòng chọn ngày khác hoặc loại sân khác giúp mình nhé!"*
  3. Tuyệt đối **KHÔNG** tự ý bịa ra các khung giờ trống ảo không có thật trong hệ thống.

### AC-AI-02: Sinh Tin Nhắn Chăm Sóc Khách Hàng Chuẩn Zalo/SMS (FR-15)
- **Given**: Đơn đặt sân #1 của khách "Nguyễn Tiến Linh", Sân bóng 7 - A, khung giờ 17:30 - 19:00 ngày 2026-09-11, đã cọc 200.000 VNĐ, còn lại 300.000 VNĐ.
- **When**: Nhân viên chọn đơn #1 và bấm "Sinh tin nhắn AI" với loại "Xác nhận đặt sân".
- **Then**:
  1. AI trả về đoạn văn bản có emoji thân thiện, chứa đầy đủ: Tên khách, tên sân, ngày giờ đá, số tiền đã cọc, số tiền còn thiếu.
  2. Có dòng nhắc nhở: *"Vui lòng có mặt trước 15 phút để khởi động và nhận sân đúng giờ"*.
  3. Nút "Sao chép" đưa toàn bộ nội dung tin nhắn vào Clipboard của máy tính.

### AC-AI-03: Chế Độ Dự Phòng Tự Động Fallback (NFR-08)
- **Given**: Máy chủ mất kết nối Internet hoặc biến `GEMINI_API_KEY` chưa được điền.
- **When**: Khách hàng gửi câu hỏi tìm sân hoặc nhân viên yêu cầu sinh tin nhắn thông báo.
- **Then**:
  1. Hệ thống bắt ngoại lệ trong khối `try-except`, không quăng lỗi HTTP 500 crash ứng dụng.
  2. Tự động chuyển hướng sang `fallback_service.py`.
  3. Trả về kết quả khung giờ dạng danh sách gạch đầu dòng rõ ràng từ dữ liệu SQL.
  4. Người dùng vẫn xem được thông tin và tiếp tục đặt sân bình thường.

