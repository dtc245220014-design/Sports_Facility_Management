# Các Bản Ghi Quyết Định Kiến Trúc (Architecture Decision Records - ADRs)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

---

## ADR-01: Lựa Chọn Flask Framework Cho Backend
- **Trạng thái**: Đã chấp thuận (Accepted).
- **Bối cảnh**: Hệ thống cần xây dựng các API RESTful phục vụ đặt sân, kiểm soát đồng thời và tích hợp AI RAG với Python. Các ứng viên cân nhắc bao gồm: Flask, Django, FastAPI.
- **Quyết định**: Chọn **Python Flask (phiên bản 3.0.3)** kết hợp với `Flask-SQLAlchemy` và cấu trúc `Blueprint`.
- **Lý do**:
  1. *Độ tinh gọn và linh hoạt*: Flask không bị gò bó bởi cấu trúc monolithic cồng kềnh như Django, cho phép tùy biến luồng xử lý Transaction và tích hợp AI SDK một cách trực tiếp.
  2. *Hệ sinh thái tương thích cao*: Flask hỗ trợ toàn diện các thư viện AI hiện đại của Google (`google-genai`, `google-generativeai`) và PyMySQL.
  3. *Tốc độ triển khai*: Phù hợp hoàn hảo với quy mô của Đề tài 36 trong các kỳ kiểm tra KT1, KT2, KT3 và bảo vệ Cuối kỳ.
- **Hệ quả**: Cần tự tổ chức cấu trúc thư mục theo chuẩn Layered Architecture (Models, Services, Routes) để mã nguồn không bị phân mảnh.

---

## ADR-02: Lựa Chọn MySQL InnoDB & Khóa Bi Quan (Pessimistic Lock)
- **Trạng thái**: Đã chấp thuận (Accepted).
- **Bối cảnh**: Vấn đề trùng lịch (Double Booking) là rủi ro nghiêm trọng nhất trong kinh doanh sân thể thao. Cần lựa chọn CSDL và cơ chế khóa bản ghi thích hợp giữa MySQL, SQLite và PostgreSQL.
- **Quyết định**: Chọn **MySQL 8.0 với Storage Engine InnoDB**, áp dụng câu lệnh khóa dòng **`SELECT ... FOR UPDATE` (Pessimistic Locking)** kết hợp khóa ràng buộc duy nhất **`UNIQUE KEY uq_court_slot (court_id, booking_date, start_time)`**.
- **Lý do**:
  1. *Hỗ trợ giao dịch ACID thực thụ*: InnoDB quản lý khóa ở cấp độ dòng (Row-Level Lock) thay vì khóa toàn bộ bảng (Table Lock) như MyISAM hay SQLite.
  2. *Bảo vệ tuyệt đối khi có tranh chấp đồng thời*: Khóa bi quan chặn ngay lập tức các giao dịch đến sau, bảo đảm trong cùng một khung giờ chỉ có đúng 1 đơn đặt sân được tạo ra.
  3. *Khóa dự phòng cấp CSDL (Database Constraint)*: Ngay cả khi tầng ứng dụng gặp sự cố logic, khóa `UNIQUE KEY` tại MySQL vẫn là "chốt chặn thép" cuối cùng từ chối lệnh insert trùng lặp với lỗi `1062 Duplicate entry`.
- **Hệ quả**: Các phiên giao dịch cần được mở và đóng nhanh chóng (`with_for_update()` kết hợp `db.session.commit()`) để tránh giữ khóa dòng quá lâu gây nghẽn kết nối.

---

## ADR-03: Lựa Chọn Google Gemini 1.5 Flash Cho Pipeline AI RAG
- **Trạng thái**: Đã chấp thuận (Accepted).
- **Bối cảnh**: Hệ thống cần tích hợp trí tuệ nhân tạo để tư vấn khung giờ tự nhiên, sinh tin nhắn xác nhận/nhắc lịch và phân tích báo cáo công suất. Cân nhắc giữa: Google Gemini, OpenAI GPT-4o, Huấn luyện mô hình riêng (Fine-tuning), và Mô hình chạy local (Ollama Llama 3).
- **Quyết định**: Sử dụng **Google Gemini 1.5 Flash** thông qua SDK chính thức `google-genai`.
- **Lý do**:
  1. *Thời gian phản hồi siêu tốc*: Gemini 1.5 Flash có độ trễ cực thấp (thường < 1.5 - 2s), đáp ứng hoàn hảo yêu cầu NFR-01.
  2. *Cửa sổ ngữ cảnh (Context Window) lớn*: Dễ dàng nạp toàn bộ danh sách hàng chục khung giờ trống trong ngày vào Context mà không lo tràn token.
  3. *Hỗ trợ tiếng Việt xuất sắc*: Khả năng hiểu ngôn ngữ tự nhiên đời thường của người Việt (ví dụ: "sân 7", "tối thứ sáu", "chiều mai") rất chính xác.
  4. *Chi phí tối ưu và có gói miễn phí*: Rất thuận tiện cho việc phát triển, kiểm thử đồ án sinh viên và ứng dụng thực tế.
- **Hệ quả**: Phụ thuộc vào kết nối Cloud API và hạn mức giới hạn (Rate limit), do đó bắt buộc phải có cơ chế Dự phòng (ADR-04).

---

## ADR-04: Thiết Kế Mô Hình Dự Phòng Chịu Lỗi (Two-Tier Fallback Mechanism)
- **Trạng thái**: Đã chấp thuận (Accepted).
- **Bối cảnh**: Khi gọi API đám mây (Gemini), hệ thống có thể gặp lỗi mạng quốc tế, hết hạn mức quota hoặc khách chưa nạp API Key. Nếu chỉ áp dụng cơ chế Retry (thử lại vô tận), hệ thống sẽ bị treo và gây trải nghiệm tồi tệ.
- **Quyết định**: Xây dựng module **`FallbackService` (Cơ chế Dự phòng 2 Lớp)**:
  - Lớp 1 (AI Primary): Thử gọi Gemini RAG với timeout 3 giây.
  - Lớp 2 (Rule-based Fallback): Nếu có bất kỳ lỗi nào, ngay lập tức bắt ngoại lệ và kích hoạt hàm sinh kết quả truyền thống từ SQL.
- **Lý do**:
  1. *Độ tin cậy cao (Zero Downtime)*: Đảm bảo giao diện người dùng không bao giờ nhận thông báo lỗi 500.
  2. *Bảo đảm nghiệp vụ cốt lõi*: Khách hàng vẫn tra cứu được khung giờ trống, nhân viên vẫn lấy được tin nhắn mẫu để gửi khách.
- **Hệ quả**: Bổ sung thêm logic định dạng văn bản truyền thống trong backend (`services/fallback_service.py`).

