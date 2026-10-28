# 🏟️ SportSync AI - Hệ Thống Quản Lý Sân Thể Thao Cho Thuê Tích Hợp AI (Đề Tài 36)

> **Dự án thực hiện theo chuẩn đề tài nghiên cứu & ứng dụng AI trong Vòng đời Phát triển Phần mềm (SDLC).**
> Tích hợp trọn bộ giải pháp quản lý sân thể thao toàn diện: Sơ đồ khung giờ thời gian thực, cơ chế khóa bi quan (Pessimistic Concurrency Lock) chống trùng lịch tuyệt đối, bộ 3 tính năng AI RAG & Dự phòng Fallback, cùng giao diện Web trực quan và bộ kiểm thử tự động `pytest` đạt tỷ lệ thành công 100%.

---

## 🌟 Điểm Nhấn Công Nghệ & Tính Năng Nổi Bật

1. **Kiến Trúc Phân Tầng Chuẩn Mực (Layered Architecture)**:
   - Tách bạch 4 tầng: Giao diện Web (Presentation) -> Bộ điều khiển API (Flask Blueprints) -> Dịch vụ Nghiệp vụ (Services) -> Cơ sở Dữ liệu (SQLAlchemy ORM & MySQL 8.0 InnoDB).
2. **Khóa Bi Quan Chống Trùng Lịch Tuyệt Đối (Pessimistic Locking - NFR-04)**:
   - Áp dụng `SELECT ... FOR UPDATE` và ràng buộc CSDL `UNIQUE KEY uq_court_slot (court_id, booking_date, start_time)`.
   - Đã được kiểm chứng thực tế qua bài test đa luồng (10 luồng cùng tranh chấp 1 slot trong 1ms -> đúng 1 request thành công, 9 request trả lỗi 409 Conflict).
3. **Bộ 3 Tính Năng AI RAG Thông Minh (Google Gemini 1.5 Flash)**:
   - **Tư vấn khung giờ còn trống (FR-14)**: Trích xuất intent từ ngôn ngữ tự nhiên, truy vấn CSDL và trả lời dựa trên 100% dữ liệu thực tế (Strict Grounding, tuyệt đối không bịa giờ trống).
   - **Tự động sinh tin nhắn thông báo (FR-15)**: Soạn thảo tin nhắn xác nhận cọc hoặc nhắc lịch thi đấu thân thiện, chuẩn định dạng gửi SMS/Zalo.
   - **Tóm tắt công suất & Gợi ý khuyến mại (FR-16)**: Phân tích các khung giờ vắng khách (thấp điểm < 30%) và đề xuất chính sách giảm giá kích cầu cụ thể.
4. **Cơ Chế Dự Phòng Chịu Lỗi Toàn Diện (NFR-08 Fallback Architecture)**:
   - Khi mất mạng, timeout > 3s hoặc chưa cấu hình API Key, hệ thống tự động rẽ nhánh sang `fallback_service.py` trả về kết quả truyền thống từ SQL, không bao giờ gây lỗi 500 cho người dùng.
5. **Giao Diện Người Dùng Trực Quan (Interactive Web UI)**:
   - Sơ đồ ma trận khung giờ mã màu thời gian thực (Xanh = Trống, Đỏ = Đã đặt, Xám = Bảo trì).
   - Đặt sân tại bàn, đổi lịch, hủy lịch với chính sách cọc 24 giờ, công tắc bảo trì tự động khóa slot.

---

## 📁 Cấu Trúc Thư Mục Dự Án

```text
Sports_Facility_Management/
├── .agents/skills/              # 9 bộ kỹ năng chuẩn hóa quy trình phát triển
│   ├── requirements-analysis/
│   ├── architecture-design/
│   ├── database-design/
│   ├── implementation/
│   ├── rag-prompt/
│   ├── testing/
│   ├── security-review/
│   ├── code-review/
│   └── documentation/
├── database/                    # Cơ sở dữ liệu
│   ├── schema.sql               # DDL khởi tạo bảng chuẩn 3NF & khóa UNIQUE
│   └── seed_data.py             # Script tự động khởi tạo CSDL & nạp dữ liệu mẫu
├── docs/                        # Trọn bộ 14 tài liệu kỹ thuật hoàn chỉnh
│   ├── requirements.md          # Đặc tả 16 FRs, 11 NFRs và ma trận RBAC
│   ├── user-stories.md          # Danh sách User Stories theo từng Persona
│   ├── acceptance-criteria.md   # Tiêu chí nghiệm thu chuẩn Given-When-Then
│   ├── requirements-issues.md   # Phân tích rủi ro nghiệp vụ & giải pháp
│   ├── architecture.md          # Thiết kế kiến trúc tổng thể & sơ đồ Mermaid
│   ├── architecture-decisions.md# Các bản ghi quyết định kiến trúc ADR 01-04
│   ├── database-design.md       # Thiết kế CSDL 3NF, ERD & Data Dictionary
│   ├── rag-pipeline.md          # Đặc tả Pipeline AI RAG 4 pha & Prompt Grounding
│   ├── security-review.md       # Báo cáo rà soát an ninh thông tin OWASP
│   ├── code-review.md           # Báo cáo rà soát chất lượng mã nguồn
│   ├── test-report.md           # Báo cáo kết quả kiểm thử tự động pytest
│   ├── api.md                   # Đặc tả toàn bộ RESTful API endpoints
│   ├── user-guide.md            # Sổ tay hướng dẫn vận hành chi tiết
│   └── sdlc-ai-report.md        # Báo cáo tổng kết ứng dụng AI qua 4 mốc SDLC
├── models/                      # Tầng truy cập dữ liệu (SQLAlchemy ORM)
│   ├── __init__.py
│   └── models.py                # User, CourtType, Court, PriceConfig, TimeSlot, Booking
├── routes/                      # Tầng điều khiển API (Flask Blueprints)
│   ├── auth_routes.py           # Đăng nhập, đăng xuất, phân quyền RBAC
│   ├── court_routes.py          # Quản lý sân, loại sân, khung giờ, bảo trì
│   ├── booking_routes.py        # Đặt sân, đổi/hủy lịch, quyết toán
│   ├── ai_routes.py             # Chatbot RAG, sinh tin nhắn, báo cáo công suất
│   └── report_routes.py         # Thống kê doanh thu, tỷ lệ lấp đầy, giờ cao điểm
├── services/                    # Tầng nghiệp vụ (Business Logic)
│   ├── auth_service.py          # Xác thực mật khẩu PBKDF2/BCrypt
│   ├── court_service.py         # Quản lý sân và bảo trì tự động khóa slot
│   ├── booking_service.py       # Pessimistic Locking with_for_update(), cọc 30-50%
│   ├── report_service.py        # Thống kê doanh thu và phân tích giờ cao điểm
│   ├── rag_service.py           # Pipeline AI RAG 4 pha kết nối Gemini
│   └── fallback_service.py      # Cơ chế dự phòng chịu lỗi khi ngắt kết nối AI
├── static/                      # Tài nguyên giao diện người dùng
│   ├── css/style.css            # Định kiểu giao diện hiện đại, responsive
│   └── js/app.js                # Xử lý tương tác AJAX, sơ đồ lịch và chatbot
├── templates/
│   └── index.html               # Giao diện Single Page Application
├── tests/                       # Bộ kiểm thử tự động pytest
│   ├── conftest.py              # Cấu hình fixtures kiểm thử
│   ├── test_concurrency_booking.py # Kiểm thử đa luồng tranh chấp đặt sân
│   ├── test_booking_business.py    # Kiểm thử cọc, đổi lịch, hủy lịch, bảo trì
│   └── test_ai_grounding_fallback.py # Kiểm thử AI Grounding & Chế độ Fallback
├── .env                         # Cấu hình biến môi trường và API Key
├── app.py                       # Điểm khởi chạy ứng dụng Flask
├── extensions.py                # Khởi tạo đối tượng SQLAlchemy
├── pytest.ini                   # Cấu hình pytest đường dẫn module
└── requirements.txt             # Danh mục các thư viện phụ thuộc
```


## 🤖 Quy trình phát triển tích hợp AI (AI-Assisted SDLC Workflow)

```mermaid
flowchart TD
    A([📥 1. Phân tích yêu cầu & Khảo sát nghiệp vụ FR/NFR]) --> B[💻 2. Thiết kế hệ thống, ERD CSDL & API SQL & UML]
    
    B --> HG1{👤 Human Gate 1: Duyệt yêu cầu & Bản thiết kế}
    
    HG1 -- Đạt --> C[🤖 3. Tích hợp AI Agent & LLM Engine]
    HG1 -- Chưa đạt --> A
    
    subgraph AI_Skills [Bộ 3 AI Skills & Bảo mật]
        C --> D1[🤖 AI Trợ lý Tư vấn: Khung giờ trống FR-14 & Cơ chế RAG CSDL thực tế RAG Grounding]
        C --> D2[🤖 AI Trợ lý Sinh tin nhắn: Xác nhận đặt sân & Nhắc lịch thi đấu FR-15 - SMS/Zalo]
        C --> D3[🤖 AI Phân tích Kinh doanh: Doanh thu, Công suất & Đề xuất giá FR-16 - Admin Assist]
    end

    D1 & D2 & D3 --> HG2{👤 Human Gate 2: Rà soát & Tối ưu Prompt, Bảo mật dữ liệu Anonymizer Module}
    
    HG2 -- Đạt --> E[🧪 4. Thực nghiệm, 12 Test Cases & Xây dựng Fallback Mechanism Testing]
    HG2 -- Chưa đạt --> C
    
    E --> HG3{👤 Human Gate 3: Thẩm định kiểm thử, Biên & Concurrency}
    
    HG3 -- Đạt --> F[📝 5. Hoàn thiện sản phẩm, Tài liệu kỹ thuật, README & Git]
    HG3 -- Chưa đạt --> E
    
    F --> G[🚀 6. Triển khai hệ thống Web, Docker & Vận hành thực tế]
    
    G --> HG4{👤 Human Gate 4: Nghiệm thu & Hội đồng đánh giá}
    
    HG4 -- Đạt --> H([🎯 Hoàn thành, Vận hành & Phát triển tương lai])
    HG4 -- Chưa đạt --> F
```

---

## 🚀 Hướng Dẫn Cài Đặt & Khởi Chạy

### 1. Môi Trường Yêu Cầu
- **Python**: Phiên bản 3.10, 3.11 hoặc 3.12.
- **MySQL**: Phiên bản 8.0 trở lên đang chạy trên cổng mặc định `3306`.

### 2. Cài Đặt Thư Viện Phụ Thuộc
Mở terminal tại thư mục dự án:
```bash
# Kích hoạt môi trường ảo (nếu đã có venv)
.\venv\Scripts\activate

# Hoặc tạo mới và cài đặt thư viện
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Cấu Hình Biến Môi Trường (`.env`)
Tệp `.env` đã được thiết lập sẵn tại thư mục gốc với thông số:
```ini
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=sports_facility_db
DATABASE_URL=mysql+pymysql://root:your_password@localhost/sports_facility_db

GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=gemini-1.5-flash
```

### 4. Khởi Tạo Cơ Sở Dữ Liệu & Nạp Dữ Liệu Mẫu (Seed Data)
Chạy script tự động khởi tạo database, chạy schema và nạp dữ liệu mẫu ban đầu:
```bash
python database/seed_data.py
```
*Script sẽ tự động tạo bảng, nạp 4 loại sân, 6 sân thực tế, bảng giá cao/thấp điểm, tạo các khung giờ cho các ngày tới (kèm ngày mẫu 2026-09-11) và 2 tài khoản mẫu:*
- **Tài khoản Quản lý (Admin)**: `admin` / `admin123`
- **Tài khoản Nhân viên (Staff)**: `staff1` / `staff123`

### 5. Chạy Bộ Kiểm Thử Tự Động (Automated Testing)
Thực thi toàn bộ 10 bài test tự động bao gồm kiểm thử tranh chấp đa luồng:
```bash
pytest tests/ -v
```
*Kết quả kỳ vọng*: `10 passed in 1.57s` (Tỷ lệ pass 100%).

### 6. Khởi Chạy Ứng Dụng Web
Khởi động máy chủ Flask:
```bash
python app.py
```
Mở trình duyệt web và truy cập địa chỉ:
👉 **`http://localhost:5000`**

---

## 🎬 Kịch Bản Trình Diễn & Chấm Điểm Đồ Án (Demo Walkthrough)

| Bước Demo | Tính Năng Kiểm Chứng | Thao Tác Thực Hiện | Kết Quả Kỳ Vọng |
| :---: | :--- | :--- | :--- |
| **Demo 1** | Sơ đồ khung giờ thời gian thực | Chọn ngày `2026-09-11`, quan sát các sân bóng 7 người, cầu lông, tennis. | Hiển thị ma trận khung giờ với mã màu trực quan (Xanh: Trống, Đỏ: Đã đặt, Xám: Bảo trì). |
| **Demo 2** | Đặt sân tại bàn & Khóa lịch | Bấm vào 1 slot màu xanh, nhập tên `Nguyễn Văn A`, SĐT `0912345678`, tiền cọc 40%, bấm Xác nhận. | Slot lập tức chuyển sang màu đỏ `BOOKED`. Đơn đặt xuất hiện trong tab Quản lý. |
| **Demo 3** | Chống trùng lịch (Concurrency) | Chạy lệnh `pytest tests/test_concurrency_booking.py -v`. | 10 luồng cùng đặt 1 slot -> Đúng 1 request nhận HTTP 201, 9 request nhận HTTP 409 Conflict. |
| **Demo 4** | Trợ lý AI Tư vấn (Prompt mẫu) | Chuyển sang tab "Trợ lý AI", bấm nút gợi ý: *"Khách muốn đặt sân bóng 7 người tối thứ Sáu"*. | AI lọc chính xác các slot còn trống ngày 2026-09-11, trả lời tự nhiên, lịch sự kèm giá thuê. |
| **Demo 5** | AI Sinh Tin Nhắn Zalo/SMS | Tại tab "Quản lý Đặt sân", bấm nút Robot AI trên một đơn đặt bất kỳ. | AI tự động sinh nội dung xác nhận hoặc nhắc lịch thi đấu có emoji, có nút copy 1-click. |
| **Demo 6** | Khóa Lịch Bảo Trì Tự Động | Sang tab "Quản lý Sân & Bảo trì", bấm "Chuyển sang bảo trì" cho Sân bóng 7 - A. | Toàn bộ khung giờ trống của sân đó tự động chuyển sang màu xám `MAINTENANCE`. |
| **Demo 7** | Thống kê Doanh thu & AI Khuyến mại | Sang tab "Thống kê & Phân tích AI", bấm "Chạy phân tích AI". | Hiển thị biểu đồ công suất, giờ cao điểm và AI đề xuất giảm giá 20% cho khung giờ sáng sớm. |

---

## 📚 Danh Mục Tài Liệu Báo Cáo Kỹ Thuật (Docs Index)

Để xem chi tiết tài liệu chuyên sâu của từng bộ kỹ năng, vui lòng xem tại thư mục `docs/`:
- 📋 [Tài liệu Đặc tả Yêu cầu Kỹ thuật (SRS)](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/requirements.md)
- 👤 [Danh sách User Stories theo Personas](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/user-stories.md)
- ✅ [Tiêu chí Chấp nhận Chuẩn Given-When-Then](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/acceptance-criteria.md)
- ⚠️ [Báo cáo Phân tích Rủi ro & Bài toán Biên](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/requirements-issues.md)
- 🏛️ [Tài liệu Thiết kế Kiến trúc Hệ thống Phân tầng](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/architecture.md)
- 📝 [Các Bản ghi Quyết định Kiến trúc (ADR 01-04)](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/architecture-decisions.md)
- 🗄️ [Tài liệu Thiết kế CSDL Chuẩn 3NF & ERD](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/database-design.md)
- 🤖 [Đặc tả Pipeline AI RAG 4 Pha & Prompt Grounding](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/rag-pipeline.md)
- 🔒 [Báo cáo Rà soát An ninh Thông tin OWASP](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/security-review.md)
- 🔍 [Báo cáo Rà soát Chất lượng Mã nguồn (Code Review)](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/code-review.md)
- 🧪 [Báo cáo Kết quả Kiểm thử Tự động pytest](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/test-report.md)
- 🌐 [Đặc tả Toàn bộ RESTful API Endpoints](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/api.md)
- 📖 [Sổ tay Hướng dẫn Vận hành Hệ thống](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/user-guide.md)
- 🎓 [Báo cáo Tổng kết Ứng dụng AI Qua 4 Mốc SDLC](file:///d:/Anh%20bai%20tap/Sports_Facility_Management/docs/sdlc-ai-report.md)

