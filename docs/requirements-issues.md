# Báo Cáo Phân Tích Rủi Ro Nghiệp Vụ & Giải Pháp Kỹ Thuật
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

Tài liệu này tổng hợp các bài toán biên (Edge Cases), xung đột tiềm ẩn trong thực tế vận hành sân thể thao và giải pháp kỹ thuật đã được thiết kế trong hệ thống SportSync AI.

---

## 1. Vấn Đề 1: Khách "Bùng Sân" (No-Show) & Hủy Lịch Đột Ngột

### Bối cảnh Thực tế
Trong kinh doanh sân cỏ nhân tạo và sân tennis, rất nhiều đội bóng đặt sân bằng miệng qua điện thoại rồi đến giờ không đến thi đấu. Điều này gây thiệt hại kép cho chủ sân: vừa mất doanh thu từ khách đặt, vừa từ chối các đội bóng khác muốn thuê cùng khung giờ đó.

### Phân tích Giải pháp Kỹ thuật
1. **Bắt buộc Thu Cọc 30% - 50% (FR-07, AC-DEPOSIT-01)**:
   - Hệ thống không cho phép xác nhận giữ chỗ ở trạng thái `CONFIRMED` nếu tiền cọc bằng 0.
   - Khoản tiền cọc này đóng vai trò là "chi phí cam kết trách nhiệm" của đội bóng.
2. **Quy Chế Hoàn / Phạt Cọc Theo Mốc 24 Giờ (FR-08)**:
   - Nếu khách báo hủy trước giờ thi đấu ≥ 24 giờ: Chủ sân có đủ thời gian để tìm đội khác thay thế -> Hệ thống đánh dấu `payment_status = 'REFUNDED'`, hoàn trả 100% cọc cho khách để giữ quan hệ khách hàng.
   - Nếu khách báo hủy sát giờ (< 24 giờ): Hệ thống giữ nguyên trạng thái `payment_status = 'DEPOSITED'`, không hoàn lại tiền cọc, chuyển slot về `FREE` để đón khách vãng lai. Khoản cọc bị phạt bù đắp chi phí vận hành cho sân.
3. **AI Nhắc Lịch Tự Động (FR-15)**:
   - Tính năng AI tự động soạn tin nhắn nhắc nhở thân thiện trước giờ đấu giúp khách hàng nhớ lịch và chủ động báo sớm nếu có thay đổi.

---

## 2. Vấn Đề 2: Tranh Chấp Đặt Sân Cùng Thời Điểm (Race Condition & Concurrency Collisions)

### Bối cảnh Thực tế
Vào các khung giờ "vàng" (19:00 - 20:30 tối thứ Sáu và cuối tuần), nhu cầu thuê sân rất cao. Rất nhiều nhân viên hoặc người dùng cùng mở giao diện và đồng thời bấm nút xác nhận đặt cho duy nhất 1 sân trống còn lại.

### Đánh giá Lựa chọn Kỹ thuật: Khóa Bi Quan (Pessimistic) vs. Khóa Lạc Quan (Optimistic)
- **Khóa lạc quan (Optimistic Lock bằng Version/Timestamp)**:
  - Phù hợp với hệ thống ít xung đột (Read-heavy).
  - Khi có tranh chấp cao, 9 người dùng sẽ cùng nhập thông tin, chỉ khi bấm lưu thì 9 người bị lỗi version mismatch -> Gây ức chế trải nghiệm người dùng.
- **Khóa bi quan (Pessimistic Lock bằng `SELECT ... FOR UPDATE`) - Giải pháp được lựa chọn**:
  - Khi 1 giao dịch bắt đầu đọc dòng `time_slots`, MySQL InnoDB kích hoạt Row-Level Exclusive Lock (Khóa X).
  - Các giao dịch đến sau 1 phần triệu giây (millisecond) sẽ phải chờ hoặc lập tức bị chặn lại khi slot không còn `FREE`.
  - Kết hợp với ràng buộc toàn vẹn `UNIQUE KEY uq_court_slot (court_id, booking_date, start_time)` ở tầng CSDL để bảo đảm triệt tiêu 100% rủi ro Double Booking.

---

## 3. Vấn Đề 3: Ảo Giác AI (AI Hallucination) & Trả Lời Sai Thông Tin Sân

### Bối cảnh Thực tế
Nếu sử dụng các mô hình ngôn ngữ lớn (LLM) thông thường mà không có Context chính xác, AI có thể tự nghĩ ra các khung giờ trống không có thật (ví dụ: tư vấn sân trống lúc 23:30 đêm hoặc ngày đã kín sân) hoặc tự sáng tạo đơn giá không đúng bảng giá của sân.

### Phân tích Giải pháp Kỹ thuật: Kiến Trúc RAG 4 Pha & Strict Grounding
1. **Tách biệt Truy vấn Dữ liệu (Retriever) và Tạo sinh (Generator)**:
   - Tuyệt đối không để LLM đoán giờ trống. Hệ thống dùng câu lệnh SQL tham số hóa để lọc chính xác các bản ghi có `status = 'FREE'`.
2. **Kỹ thuật Prompt Grounding**:
   - System instruction ép buộc: *"Bạn CHỈ ĐƯỢC PHÉP gợi ý các khung giờ có trong danh sách CSDL được cung cấp. TUYỆT ĐỐI KHÔNG tự sáng tạo thêm khung giờ."*
   - Kiểm tra ngưỡng rỗng: Nếu SQL trả về 0 dòng, hệ thống chủ động trả về thông báo hết sân ngay lập tức mà không cần gọi LLM, vừa tiết kiệm chi phí token vừa loại bỏ triệt để ảo giác.

---

## 4. Vấn Đề 4: Sự Cố Ngắt Kết Nối AI (AI API Downtime / Latency Spikes)

### Bối cảnh Thực tế
Các dịch vụ Cloud AI (như Google Gemini API) có thể gặp sự cố mất kết nối mạng, nghẽn đường truyền quốc tế, vượt hạn mức giới hạn (Rate limit/Quota exceeded) hoặc độ trễ phản hồi tăng cao > 5 giây. Nếu hệ thống phụ thuộc hoàn toàn vào AI, toàn bộ quầy lễ tân sẽ bị tê liệt.

### Phân tích Giải pháp Kỹ thuật: Cơ Chế Dự Phòng Chịu Lỗi (NFR-08 Fallback Architecture)
- Thiết kế hệ thống theo nguyên tắc **Graceful Degradation (Suy giảm Chức năng Dần dần)**:
  - Mọi thao tác gọi AI đều được bọc trong khối `try-except` với cấu hình Timeout nghiêm ngặt.
  - Khi phát hiện lỗi hoặc không tìm thấy `GEMINI_API_KEY`, luồng điều khiển lập tức rẽ nhánh sang `fallback_service.py`.
  - Kết quả trả về cho người dùng bằng văn bản định dạng chuẩn truyền thống (Bullet points) được sinh trực tiếp từ mã nguồn Python nội bộ.
  - Khách hàng và nhân viên vẫn tra cứu được lịch, vẫn sinh được tin nhắn và hoàn toàn không nhận thông báo lỗi hệ thống 500.

---

## 5. Vấn Đề 5: Sân Cần Bảo Trì Đột Xuất Khi Đã Có Khách Đặt

### Bối cảnh Thực tế
Một cơn mưa lớn làm ngập sân, hoặc hệ thống đèn chiếu sáng bị chập điện đột ngột cần bảo trì gấp, trong khi tối hôm đó đã có 2 đội bóng đặt lịch.

### Phân tích Giải pháp Kỹ thuật
- Trong `court_service.py`, cơ chế `toggle_court_maintenance` phân loại rõ:
  - Tự động chuyển toàn bộ các slot `FREE` sang `MAINTENANCE` để ngăn khách mới đặt vào.
  - Đối với các slot đã `BOOKED`, hệ thống giữ nguyên trạng thái đơn để nhân viên dễ dàng lọc ra danh sách các khách hàng bị ảnh hưởng.
  - Nhân viên sử dụng chức năng **Đổi lịch (Reschedule)** để chuyển đội bóng sang sân đối ứng khác (ví dụ từ Sân bóng 7 - A sang Sân bóng 7 - B) hoặc sử dụng chức năng **Hủy lịch kèm hoàn 100% cọc** do lỗi bất khả kháng từ phía sân bóng.

