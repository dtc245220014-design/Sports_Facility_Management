# Sổ Tay Hướng Dẫn Vận Hành Hệ Thống (User Guide)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

---

## 1. Hướng Dẫn Dành Cho Khách Hàng (Customer)

### 1.1. Xem Sơ Đồ Khung Giờ Trực Quan
1. Truy cập vào trang chủ: `http://localhost:5000`.
2. Mặc định hệ thống mở tab **"Sơ đồ Khung giờ"**.
3. Chọn ngày thi đấu (ô *Chọn ngày*) và lọc theo môn thể thao mong muốn (Bóng đá 7 người, 5 người, Cầu lông, Tennis).
4. Quan sát màu sắc của các khung giờ:
   - 🟢 **Màu xanh lá**: Khung giờ còn trống.
   - 🔴 **Màu đỏ**: Khung giờ đã kín chỗ.
   - ⚪ **Màu xám**: Sân đang tạm dừng phục vụ để bảo dưỡng.

### 1.2. Trò Chuyện Với Trợ Lý AI Tư Vấn (RAG)
1. Bấm vào tab **"Trợ lý AI Tư vấn"** trên thanh điều hướng.
2. Bấm vào các câu hỏi mẫu gợi ý nhanh hoặc gõ câu hỏi tự nhiên vào ô chat. Ví dụ:
   - *"Khách muốn đặt sân bóng 7 người tối thứ Sáu"*
   - *"Chiều mai sân cầu lông còn khung giờ nào trống?"*
3. Bấm nút **"Gửi"** (hoặc nhấn phím `Enter`). Trợ lý AI sẽ tức thì tra cứu CSDL thực tế và gợi ý các khung giờ còn trống chính xác nhất kèm đơn giá.

---

## 2. Hướng Dẫn Dành Cho Nhân Viên Lễ Tân (Staff)

### 2.1. Đăng Nhập Hệ Thống
1. Bấm nút **"Đăng nhập"** ở góc phải trên thanh điều hướng.
2. Nhập tài khoản nhân viên: `staff1` / Mật khẩu: `staff123` (hoặc bấm nút *Staff mẫu* để điền nhanh).
3. Bấm **"Đăng nhập"**. Huy hiệu góc phải sẽ chuyển sang màu xanh lá: `staff1 (STAFF)`.

### 2.2. Đặt Sân Tại Bàn (Khóa Lịch Chống Trùng)
1. Tại tab **"Sơ đồ Khung giờ"**, tìm đến sân và khung giờ màu xanh lá mà khách muốn đặt.
2. Click chuột trực tiếp vào khung giờ đó. Cửa sổ **"Xác Nhận Đặt Sân"** sẽ hiện lên.
3. Nhập thông tin:
   - Họ và tên khách hàng (Ví dụ: `Nguyễn Văn Tuấn`).
   - Số điện thoại liên hệ (Ví dụ: `0988776655`).
   - Tiền đặt cọc: Hệ thống tự động tính sẵn 40% giá sân. Nhân viên có thể điều chỉnh trong khoảng quy định từ 30% đến 50%.
   - Ghi chú thêm (nếu có): Mượn áo bib, yêu cầu bóng mới...
4. Bấm nút **"Khóa lịch & Xác nhận đặt"**.
5. *Kết quả*: Khung giờ ngay lập tức đổi sang màu đỏ (`BOOKED`). Không ai khác có thể đặt đè lên khung giờ này.

### 2.3. Sinh Tin Nhắn Chăm Sóc Khách Hàng Bằng AI
1. Chuyển sang tab **"Quản lý Đặt sân"**.
2. Tìm đơn đặt của khách trong danh sách và bấm nút biểu tượng **Robot AI (màu xanh lá)** ở cột Thao tác.
3. Modal AI sẽ tự động soạn thảo tin nhắn chỉn chu:
   - Chọn tab **"Xác nhận đặt sân"** để gửi ngay sau khi nhận cọc.
   - Chọn tab **"Nhắc lịch thi đấu"** để gửi vào ngày diễn ra trận đấu.
4. Bấm nút **"Sao chép gửi khách"** và dán (Paste) vào cuộc trò chuyện Zalo hoặc SMS của khách hàng.

### 2.4. Đổi Lịch & Hủy Lịch Thi Đấu
- **Đổi lịch**:
  - Tại bảng quản lý, bấm nút Đổi lịch, chọn khung giờ trống mới. Hệ thống sẽ tự động hoán đổi an toàn hai khung giờ.
- **Hủy lịch & Quy định tiền cọc**:
  - Bấm nút **"Hủy lịch"** (biểu tượng dấu X đỏ).
  - Hệ thống tự động kiểm tra thời gian: Nếu khách báo hủy trước 24 giờ, hệ thống ghi nhận hoàn lại 100% tiền cọc cho khách. Nếu hủy muộn dưới 24 giờ, hệ thống phạt giữ lại tiền cọc và giải phóng slot về `FREE`.

### 2.5. Hoàn Tất Trận Đấu & Quyết Toán
1. Sau khi khách đá xong, tại tab **"Quản lý Đặt sân"**, bấm nút **Hoàn tất (biểu tượng tích V xanh dương)**.
2. Nhân viên thu nốt số tiền còn lại (đã hiển thị rõ trên đơn) và bấm xác nhận để hoàn tất đơn đặt.

---

## 3. Hướng Dẫn Dành Cho Quản Lý Cơ Sở (Admin)

### 3.1. Đăng Nhập Tài Khoản Quản Trị
1. Bấm nút Đăng nhập -> Điền `admin` / `admin123` (hoặc bấm nút *Admin mẫu*).
2. Huy hiệu góc phải chuyển thành màu đỏ: `admin (ADMIN)`.

### 3.2. Quản Lý Sân & Bật Chế Độ Bảo Trì
1. Truy cập tab **"Quản lý Sân & Bảo trì"**.
2. Danh sách tất cả các sân sẽ hiện ra kèm trạng thái hoạt động.
3. Khi cần bảo dưỡng mặt cỏ hoặc sửa đèn cho một sân (Ví dụ: Sân bóng 7 - A):
   - Bấm nút **"Chuyển sang bảo trì"**.
   - Toàn bộ các khung giờ trống trong tương lai của sân này sẽ tự động khóa lại (`MAINTENANCE`).
4. Khi bảo trì xong, bấm **"Kết thúc bảo trì"** để tự động khôi phục các khung giờ về `FREE`.

### 3.3. Theo Dõi Báo Cáo Doanh Thu & Tỷ Lệ Lấp Đầy
1. Truy cập tab **"Thống kê & Phân tích AI"**.
2. Xem 4 thẻ chỉ số nhanh: Tổng doanh thu ước tính, Tiền cọc đã thu, Tổng lượt đặt sân, Tỷ lệ lấp đầy hôm nay.
3. Xem bảng **"Phân Tích Khung Giờ Cao Điểm / Thấp Điểm"**: Nhận diện rõ các khung giờ có nhu cầu cao (đỏ) và khung giờ vắng khách (xanh dương).

### 3.4. Kích Hoạt AI Tóm Tắt Vận Hành & Gợi Ý Khuyến Mại
1. Tại tab **"Thống kê & Phân tích AI"**, bấm nút **"Chạy phân tích AI"**.
2. Trợ lý AI sẽ đọc toàn bộ dữ liệu công suất thực tế của cơ sở, đưa ra đánh giá khách quan về hiệu quả khai thác và đề xuất cụ thể 2-3 chính sách giảm giá/khuyến mại (ví dụ: giảm 20% cho khung giờ sáng sớm hoặc tặng nước suối) giúp lấp đầy các khung giờ thấp điểm.

