# Tài Liệu Đặc Tả Yêu Cầu Kỹ Thuật (SRS)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

---

## 1. Giới Thiệu & Mô Tả Bài Toán
Các đơn vị kinh doanh cho thuê sân thể thao (sân bóng đá mini 5/7 người, sân cầu lông, sân tennis, pickleball) đang đối mặt với nhiều thách thức lớn khi vận hành theo phương thức truyền thống (qua điện thoại, sổ sách ghi tay, tin nhắn mạng xã hội):
1. **Trùng lịch thi đấu (Double Booking)**: Khi nhiều nhân viên cùng nghe điện thoại hoặc khách đặt cùng lúc, rất dễ gán trùng 1 sân cho 2 đội bóng.
2. **Khó kiểm soát tiền cọc & chính sách hủy lịch**: Khách đặt miệng không cọc dẫn đến tình trạng "bùng sân" vào giờ cao điểm, gây thất thu nghiêm trọng.
3. **Quản lý bảo trì rời rạc**: Khi sân hỏng lưới, đèn hoặc mặt cỏ cần bảo trì, nhân viên quên khóa lịch dẫn đến khách vẫn đặt sân.
4. **Không tối ưu được công suất khai thác**: Khung giờ cao điểm (17:30 - 20:30) luôn quá tải, trong khi các khung giờ thấp điểm (sáng sớm hoặc đầu giờ chiều) sân bị bỏ trống mà không có chiến lược khuyến mại linh hoạt.

**Giải pháp**: Hệ thống Quản lý Sân Thể Thao tích hợp AI (SportSync AI) cung cấp nền tảng quản lý tập trung toàn diện, áp dụng kỹ thuật **Pessimistic Concurrency Lock** để triệt tiêu hoàn toàn nguy cơ trùng lịch, kết hợp cùng **AI RAG (Retrieval-Augmented Generation)** tư vấn khung giờ tự nhiên, tự động sinh tin nhắn xác nhận/nhắc lịch và phân tích công suất đề xuất khuyến mại.

---

## 2. Phân Loại Tác Nhân & Ma Trận Quyền (RBAC)

Hệ thống phân chia 3 đối tượng người dùng:
1. **Quản lý (ADMIN)**: Chủ cơ sở thể thao hoặc quản lý cấp cao. Toàn quyền cấu hình bảng giá, sân, xem báo cáo doanh thu, công suất và đề xuất AI.
2. **Nhân viên (STAFF)**: Nhân viên lễ tân/trực sân. Thực hiện đặt sân tại bàn, thu cọc, đổi lịch, hủy lịch, xem sơ đồ khung giờ và sinh tin nhắn AI gửi khách.
3. **Khách hàng (CUSTOMER / GUEST)**: Người thuê sân. Tra cứu sơ đồ khung giờ trực tuyến, trò chuyện với Chatbot AI để tìm sân trống phù hợp.

### Ma Trận Phân Quyền (RBAC Matrix)

| Chức Năng / Nghiệp Vụ | Admin | Staff | Khách Hàng | Ghi Chú |
| :--- | :---: | :---: | :---: | :--- |
| **Xem sơ đồ khung giờ thời gian thực** | ✅ | ✅ | ✅ | Hiển thị màu sắc trực quan (Trống, Đã đặt, Bảo trì) |
| **Trò chuyện với Trợ lý AI RAG** | ✅ | ✅ | ✅ | AI tư vấn chỉ dựa trên slot trống thực tế |
| **Tạo đơn đặt sân & Khóa lịch** | ✅ | ✅ | ❌ | Nhân viên nhập thông tin khách và thu cọc tại bàn |
| **Đổi lịch thi đấu** | ✅ | ✅ | ❌ | Hoán đổi slot an toàn nguyên tử |
| **Hủy lịch & Áp dụng phạt cọc** | ✅ | ✅ | ❌ | Tự động tính hoàn 100% nếu >24h, phạt nếu <=24h |
| **Hoàn tất trận đấu & Thu đủ tiền** | ✅ | ✅ | ❌ | Quyết toán sau khi trận đấu kết thúc |
| **Chuyển trạng thái Bảo trì sân** | ✅ | ✅ | ❌ | Tự động khóa toàn bộ slot trống của sân |
| **Cấu hình Bảng giá Cao/Thấp điểm** | ✅ | ❌ | ❌ | Quyền riêng của Admin |
| **Xem Báo cáo Doanh thu & Thống kê** | ✅ | ❌ | ❌ | Doanh thu thực tế, tiền cọc, phân bổ theo sân |
| **AI Tóm tắt Công suất & Khuyến mại** | ✅ | ❌ | ❌ | AI đề xuất chiến lược kích cầu giờ thấp điểm |

---

## 3. Danh Sách Yêu Cầu Chức Năng (Functional Requirements - FRs)

### 3.1. Nhóm Chức Năng Quản Lý & Vận Hành
- **FR-01 (Đăng nhập & Phiên làm việc)**: Cho phép Quản lý và Nhân viên đăng nhập vào hệ thống bằng tài khoản và mật khẩu được cấp, lưu phiên làm việc an toàn.
- **FR-02 (Phân quyền Role-Based)**: Kiểm soát quyền truy cập chặt chẽ giữa vai trò ADMIN và STAFF theo ma trận RBAC.
- **FR-03 (Quản lý Danh mục Sân & Loại sân)**: Quản lý các loại sân (Sân bóng mini 5/7 người, Cầu lông, Tennis) và từng sân cụ thể (Sân bóng 7 - A, Sân bóng 7 - B...).
- **FR-04 (Bảng giá Linh hoạt theo Khung giờ)**: Thiết lập đơn giá riêng biệt cho khung giờ thường và khung giờ cao điểm (Peak Hours: 17:30 - 22:00) cho từng loại sân.
- **FR-05 (Sơ đồ Trạng thái Khung giờ)**: Hiển thị ma trận khung giờ theo ngày và loại sân với mã màu thời gian thực:
  - 🟢 **Xanh lá (FREE)**: Khung giờ còn trống, sẵn sàng cho thuê.
  - 🔴 **Đỏ (BOOKED)**: Khung giờ đã được khách đặt và đặt cọc thành công.
  - ⚪ **Xám (MAINTENANCE)**: Khung giờ thuộc sân đang trong giai đoạn bảo dưỡng.
- **FR-06 (Quản lý Lịch Bảo trì Sân)**: Cho phép chuyển trạng thái sân sang `MAINTENANCE`. Khi kích hoạt, hệ thống **tự động khóa tất cả khung giờ FREE trong tương lai** của sân đó. Khi hoàn tất bảo trì, hệ thống tự động mở lại trạng thái `FREE`.
- **FR-07 (Đặt sân & Khóa lịch Nguyên tử)**: Nhập thông tin khách hàng (Tên, SĐT), tự động áp dụng quy định đặt cọc (tối thiểu 30%, mặc định 40%, tối đa 50%), thực thi giao dịch khóa dòng để chống trùng lịch.
- **FR-08 (Đổi lịch & Hủy lịch)**:
  - *Đổi lịch*: Khóa nguyên tử slot cũ và slot mới, đổi sang slot mới nếu còn trống.
  - *Hủy lịch*: Áp dụng quy tắc hoàn tiền cọc (Hủy trước 24 giờ hoàn 100% cọc; hủy muộn <= 24 giờ phạt giữ lại toàn bộ cọc), giải phóng slot về `FREE`.
- **FR-09 (Quản lý Khách hàng & Lịch sử Đặt)**: Lưu trữ lịch sử các trận đấu đã đặt theo số điện thoại khách hàng.
- **FR-10 (Theo dõi Thanh toán & Quyết toán)**: Ghi nhận trạng thái thanh toán (`DEPOSITED`: Đã cọc; `PAID_FULL`: Đã thanh toán 100%; `REFUNDED`: Đã hoàn cọc). Khi trận đấu kết thúc, nhân viên bấm hoàn tất và thu nốt phần còn lại.
- **FR-11 (Thống kê Doanh thu)**: Báo cáo tổng doanh thu dự kiến, tiền cọc đã thu và phân loại tỷ trọng doanh thu theo từng môn thể thao.
- **FR-12 (Thống kê Công suất Lấp đầy)**: Tính toán tỷ lệ % lấp đầy sân (`Occupancy Rate = Slot đã đặt / Tổng slot`) theo ngày và theo từng sân.
- **FR-13 (Phân tích Khung giờ Cao điểm / Thấp điểm)**: Tổng hợp tần suất đặt sân theo từng khung giờ trong ngày, phân loại thành: `CAO ĐIỂM` (≥ 60%), `TRUNG BÌNH` (30% - 59%), `THẤP ĐIỂM` (< 30%).

### 3.2. Nhóm Chức Năng Tích Hợp Trí Tuệ Nhân Tạo (AI Features)
- **FR-14 (AI Tư vấn Khung giờ Còn trống - RAG)**: Khách hàng hỏi bằng ngôn ngữ tự nhiên (Ví dụ: *"Khách muốn đặt sân bóng 7 người tối thứ Sáu"*). Hệ thống tự động bóc tách ý định (Intent Extraction), truy vấn SQL lấy chính xác danh sách các slot `FREE` ngày hôm đó, đóng gói vào Context và đưa vào Gemini LLM với Prompt Grounding nghiêm ngặt để trả lời tự nhiên, lịch sự. Tuyệt đối không bịa khung giờ trống.
- **FR-15 (AI Tự động Sinh Tin nhắn Thông báo)**: Tự động tạo tin nhắn xác nhận đặt sân hoặc nhắc lịch thi đấu trước giờ bóng lăn (đầy đủ tên khách, sân, khung giờ, số tiền cọc, số tiền còn lại và lưu ý đến trước 15 phút), định dạng chuẩn để gửi SMS hoặc Zalo.
- **FR-16 (AI Tóm tắt Công suất & Gợi ý Khuyến mại Giờ Thấp điểm)**: AI tiếp nhận dữ liệu công suất và các khung giờ thấp điểm từ hệ thống thống kê, đóng vai trò chuyên gia tối ưu doanh thu (Revenue Manager) để tóm tắt tình hình vận hành và đề xuất các gói khuyến mại cụ thể (giảm 20% giá sân sáng sớm, tặng kèm nước suối/bóng thi đấu).

---

## 4. Danh Sách Yêu Cầu Phi Chức Năng (Non-Functional Requirements - NFRs)

- **NFR-01 (Thời gian Phản hồi - Response Time)**:
  - Các API nghiệp vụ tra cứu, đặt sân, đổi lịch phản hồi < 1.0 giây.
  - API xử lý AI RAG phản hồi < 3.0 - 5.0 giây.
- **NFR-02 (Khả năng Sẵn sàng - High Availability)**: Hệ thống duy trì tính sẵn sàng 99.5%, cơ sở dữ liệu hoạt động ổn định 24/7.
- **NFR-03 (Khả năng Mở rộng - Scalability)**: Thiết kế phân lớp (Layered Architecture) cho phép mở rộng thêm nhiều cơ sở sân thể thao, nhiều chi nhánh mà không phải đập đi xây lại.
- **NFR-04 (Kiểm soát Đồng thời - Concurrency Control)**: **BẮT BUỘC** áp dụng cơ chế khóa bi quan (Pessimistic Lock `SELECT ... FOR UPDATE`) và khóa ràng buộc `UNIQUE KEY` tại CSDL để loại bỏ 100% lỗi Double Booking khi nhiều người cùng bấm đặt 1 slot.
- **NFR-05 (Bảo mật Mật khẩu)**: Toàn bộ mật khẩu người dùng phải được mã hóa một chiều bằng thuật toán an toàn (BCrypt / PBKDF2 with HMAC-SHA256).
- **NFR-06 (Bảo mật Khóa API AI)**: Khóa `GEMINI_API_KEY` chỉ được lưu trong biến môi trường máy chủ (`.env`), tuyệt đối không gửi hoặc nhúng vào JavaScript Frontend.
- **NFR-07 (Phòng chống Tấn công SQL Injection)**: 100% các câu truy vấn cơ sở dữ liệu phải sử dụng tham số hóa (Parameterized Queries / ORM Statements).
- **NFR-08 (Cơ chế Dự phòng Chịu lỗi AI - Fallback Mechanism)**: Khi dịch vụ Gemini API bị mất mạng, lỗi hạn mức Quota, timeout > 3s hoặc chưa cấu hình API Key, hệ thống tự động chuyển sang chế độ Dự phòng (Fallback Service) sử dụng mẫu tin nhắn chuẩn và dữ liệu SQL truyền thống, đảm bảo không bao giờ trả lỗi 500 cho người dùng.
- **NFR-09 (Tính Chính xác & Chống Ảo giác AI - Grounding)**: AI RAG chỉ được phép đưa ra thông tin có trong Context được truyền vào từ CSDL MySQL. Khi hết sân, AI phải thông báo rõ ràng là hết sân, không được tự bịa ra giờ trống.
- **NFR-10 (Trải nghiệm Người dùng - UX/UI)**: Giao diện trực quan, hỗ trợ tương tác trên cả máy tính và thiết bị di động, mã màu trạng thái khung giờ rõ ràng, thao tác đặt sân tại bàn dưới 3 bước bấm.
- **NFR-11 (Khả năng Kiểm thử - Testability)**: Có bộ test tự động (`pytest`) cho đầy đủ các kịch bản kiểm thử Concurrency đa luồng, kiểm thử cọc/đổi/hủy lịch và kiểm thử AI Fallback.

