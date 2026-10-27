# Danh Sách User Stories (Kèm Giá Trị Nghiệp Vụ)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

Tài liệu này định nghĩa các User Story theo chuẩn Agile Scrum, phân loại theo từng đối tượng sử dụng (Persona) nhằm đảm bảo hệ thống giải quyết đúng nỗi đau của người dùng thực tế.

---

## 1. Danh Sách Personas

- **Persona 1: Anh Hùng (Chủ cơ sở & Quản lý - ADMIN)**
  - *Mục tiêu*: Tối ưu hóa doanh thu, nắm bắt khung giờ cao/thấp điểm, tự động hóa quản lý giá và bảo trì sân mà không bị thất thoát tiền cọc.
- **Persona 2: Chị Mai (Nhân viên lễ tân / trực ca - STAFF)**
  - *Mục tiêu*: Đặt sân nhanh cho khách tại quầy, không bị nhầm lẫn hay trùng sân, dễ dàng gửi tin nhắn xác nhận qua Zalo cho khách và xử lý đổi/hủy lịch minh bạch.
- **Persona 3: Anh Tuấn (Khách hàng quen / Đội trưởng bóng đá - CUSTOMER)**
  - *Mục tiêu*: Tra cứu nhanh sân trống vào các buổi tối cuối tuần, nhận được tư vấn tự nhiên từ chatbot mà không cần chờ lễ tân nghe máy, nhận tin nhắn nhắc lịch rõ ràng.

---

## 2. User Stories Dành Cho Khách Hàng (Customer)

### US-CUST-01: Tra cứu Sơ đồ Khung giờ Trực quan
- **As a** Khách hàng thuê sân,
- **I want** xem trực tiếp sơ đồ trạng thái các sân bóng, cầu lông, tennis theo từng khung giờ trong ngày (Xanh = Trống, Đỏ = Đã đặt, Xám = Bảo trì),
- **So that** tôi có thể chủ động lựa chọn khung giờ phù hợp nhất với đội của mình mà không cần gọi điện hỏi từng sân.
- *Business Value*: Giảm 70% cuộc gọi hỏi giờ trống thông thường cho nhân viên lễ tân.

### US-CUST-02: Nhận Tư vấn Tìm sân Thông minh qua Chatbot AI (RAG)
- **As a** Khách hàng bận rộn,
- **I want** nhắn tin tự nhiên với Trợ lý AI (Ví dụ: *"Khách muốn đặt sân bóng 7 người tối thứ Sáu"* hoặc *"Chiều mai sân cầu lông còn khung giờ nào?"*),
- **So that** AI lập tức lọc dữ liệu thực tế và đưa ra gợi ý khung giờ còn trống kèm giá thuê cụ thể.
- *Business Value*: Tăng tỷ lệ chuyển đổi đặt sân và mang lại trải nghiệm công nghệ hiện đại cho khách hàng.

### US-CUST-03: Nhận Tin nhắn Xác nhận & Nhắc lịch Thi đấu
- **As a** Khách hàng đã đặt cọc sân,
- **I want** nhận được tin nhắn xác nhận chi tiết (sân nào, giờ nào, số tiền đã cọc, số tiền còn lại và lưu ý chuẩn bị) qua tin nhắn,
- **So that** tôi dễ dàng chia sẻ vào nhóm Zalo của đội và không bị quên lịch thi đấu.
- *Business Value*: Hạn chế tối đa tình trạng khách đến muộn hoặc quên lịch, nâng cao tính chuyên nghiệp.

---

## 3. User Stories Dành Cho Nhân Viên Trực Sân (Staff)

### US-STAFF-01: Khóa Lịch Đặt Sân Tức Thì Tại Bàn (Chống Trùng Lịch)
- **As a** Nhân viên trực sân,
- **I want** hệ thống khóa ngay lập tức khung giờ khi tôi bấm xác nhận đặt sân cho khách và yêu cầu cọc 30%-50%,
- **So that** không một nhân viên nào khác hoặc khách hàng nào khác có thể đặt đè lên khung giờ này cùng lúc.
- *Business Value*: Triệt tiêu hoàn toàn 100% sự cố trùng lịch (Double booking) gây tranh cãi và mất uy tín sân.

### US-STAFF-02: Đổi Lịch Thi Đấu Linh Hoạt
- **As a** Nhân viên trực sân,
- **I want** đổi lịch thi đấu sang một khung giờ trống khác khi khách hàng có việc đột xuất và báo trước,
- **So that** hệ thống tự động giải phóng slot cũ về trạng thái `FREE` và khóa slot mới cho khách mà không phải xóa đơn tạo lại từ đầu.
- *Business Value*: Giúp linh hoạt chăm sóc khách hàng thân thiết trong khi vẫn bảo đảm dữ liệu toàn vẹn.

### US-STAFF-03: Hủy Lịch Thi Đấu & Xử Lý Tiền Cọc Tự Động
- **As a** Nhân viên trực sân,
- **I want** khi bấm hủy lịch, hệ thống tự động kiểm tra thời gian báo hủy (trước 24h thì hoàn cọc, dưới 24h thì phạt giữ lại cọc),
- **So that** việc xử lý tiền cọc được thực hiện theo đúng quy chế minh bạch, tránh xung đột quyền lợi.
- *Business Value*: Bảo vệ nguồn thu của sân khi bị hủy lịch sát giờ, giảm thiểu rủi ro bùng sân.

### US-STAFF-04: Sinh Tin Nhắn Chăm Sóc Khách Hàng Bằng 1 Cú Click
- **As a** Nhân viên trực sân,
- **I want** bấm nút "Sinh tin nhắn AI" trên đơn đặt để nhận ngay nội dung tin nhắn xác nhận hoặc nhắc lịch thi đấu được viết chỉn chu, lịch sự,
- **So that** tôi chỉ cần bấm sao chép và gửi nhanh cho khách qua Zalo/SMS trong 3 giây.
- *Business Value*: Tiết kiệm 5-10 phút soạn tin nhắn thủ công cho mỗi lượt đặt sân.

### US-STAFF-05: Quyết Toán & Hoàn Tất Trận Đấu
- **As a** Nhân viên trực sân,
- **I want** bấm hoàn tất trận đấu và xác nhận khách đã thanh toán nốt phần tiền thuê còn lại sau khi trừ tiền cọc,
- **So that** đơn đặt chuyển sang trạng thái `COMPLETED` và doanh thu được ghi nhận chính xác vào ca làm việc.
- *Business Value*: Quản lý tài chính minh bạch, chống thất thoát doanh thu tiền mặt.

---

## 4. User Stories Dành Cho Quản Lý & Chủ Cơ Sở (Admin)

### US-ADMIN-01: Quản Lý Danh Mục Sân & Tự Động Khóa Lịch Bảo Trì
- **As a** Quản lý cơ sở thể thao,
- **I want** chỉ cần 1 nút gạt để chuyển trạng thái một sân sang "Bảo trì" (Ví dụ khi thay cỏ, sửa đèn cao áp, căng lưới),
- **So that** toàn bộ khung giờ còn trống trong tương lai của sân đó tự động khóa lại (`MAINTENANCE`), ngăn chặn bất kỳ ai đặt vào.
- *Business Value*: Đảm bảo an toàn cơ sở vật chất, tránh tình trạng khách đến nơi mới biết sân hỏng.

### US-ADMIN-02: Cấu Hình Bảng Giá Linh Hoạt Khung Giờ Cao / Thấp Điểm
- **As a** Quản lý cơ sở thể thao,
- **I want** cấu hình đơn giá thuê sân khác nhau giữa các khung giờ ngày thường (thấp điểm: 06:00 - 17:30) và giờ vàng buổi tối (cao điểm: 17:30 - 22:00),
- **So that** hệ thống tự động áp giá chính xác theo từng slot được tạo ra.
- *Business Value*: Tối đa hóa lợi nhuận trong giờ cao điểm và tạo điều kiện giảm giá kích cầu giờ thấp điểm.

### US-ADMIN-03: Xem Dashboard Báo Cáo Doanh Thu & Tỷ Lệ Lấp Đầy Công Suất
- **As a** Quản lý cơ sở thể thao,
- **I want** theo dõi biểu đồ doanh thu, số tiền cọc đã thu, tổng số lượt đặt và tỷ lệ lấp đầy (%) của toàn bộ cơ sở trong ngày,
- **So that** tôi nắm bắt tức thì hiệu quả kinh doanh của cụm sân thể thao.
- *Business Value*: Ra quyết định quản trị kinh doanh dựa trên dữ liệu thời gian thực.

### US-ADMIN-04: AI Tóm Tắt Vận Hành & Gợi Ý Khuyến Mại Kích Cầu Giờ Vắng
- **As a** Quản lý cơ sở thể thao,
- **I want** hệ thống AI tự động phân tích các khung giờ vắng khách (thấp điểm < 30%) và đề xuất các chương trình khuyến mại cụ thể (giảm giá 20%, tặng combo nước uống/áo bib),
- **So that** tôi có thể triển khai ngay các chiến dịch marketing lấp đầy sân trống vào buổi sáng và đầu giờ chiều.
- *Business Value*: Tăng công suất khai thác sân trong các khung giờ "chết" lên thêm 25-35%, gia tăng doanh thu ròng.

