# Tài Liệu Thiết Kế Kiến Trúc Hệ Thống (Architecture Design Document)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

Tài liệu này đặc tả kiến trúc tổng thể, mô hình phân lớp (Layered Architecture), luồng dữ liệu của Pipeline AI RAG và cơ chế kiểm soát đồng thời (Concurrency Control) của hệ thống SportSync AI.

---

## 1. Mô Hình Kiến Trúc Phân Lớp (Layered Architecture)

Hệ thống được thiết kế theo mô hình 4 tầng phân lập rõ ràng (Separation of Concerns), đảm bảo tính module hóa, dễ bảo trì và mở rộng:

```mermaid
graph TD
    subgraph Presentation_Layer["1. Presentation Layer (Giao diện Người dùng)"]
        UI_Web["Single Page Application (HTML5 / Bootstrap 5 / Vanilla JS)"]
        Grid["Sơ đồ Khung giờ Trực quan"]
        ChatUI["Giao diện Trợ lý AI Tư vấn"]
        Dashboard["Bảng điều khiển Doanh thu & Công suất"]
    end

    subgraph API_Layer["2. API & Routing Layer (Flask Blueprints)"]
        AuthBP["Auth Blueprint (/api/auth)"]
        CourtBP["Court Blueprint (/api/courts, /api/slots)"]
        BookingBP["Booking Blueprint (/api/bookings)"]
        AIBP["AI Blueprint (/api/ai)"]
        ReportBP["Report Blueprint (/api/reports)"]
    end

    subgraph Service_Layer["3. Business Service Layer (Nghiệp vụ Hệ thống)"]
        AuthService["AuthService (Xác thực & Mã hóa Mật khẩu)"]
        CourtService["CourtService (Sân, Giá & Khóa Bảo trì)"]
        BookingService["BookingService (Pessimistic Lock, Cọc 30-50%, Đổi/Hủy)"]
        ReportService["ReportService (Doanh thu, Tỷ lệ Lấp đầy, Giờ Cao điểm)"]
        RAGService["RAGService (Intent Parser, Context Retriever, Prompt Grounding)"]
        FallbackService["FallbackService (Cơ chế Dự phòng Khi Lỗi AI)"]
    end

    subgraph Data_Access_Layer["4. Data & External Infrastructure"]
        ORM["SQLAlchemy ORM Models (User, Court, Slot, Booking)"]
        MySQL[("MySQL 8.0 InnoDB (ACID, Row-Level Lock, Unique Key)")]
        Gemini["Google Gemini 1.5 Flash API (LLM Generation)"]
    end

    UI_Web --> AuthBP
    UI_Web --> CourtBP
    UI_Web --> BookingBP
    UI_Web --> AIBP
    UI_Web --> ReportBP

    AuthBP --> AuthService
    CourtBP --> CourtService
    BookingBP --> BookingService
    AIBP --> RAGService
    AIBP --> FallbackService
    ReportBP --> ReportService

    AuthService --> ORM
    CourtService --> ORM
    BookingService --> ORM
    ReportService --> ORM
    RAGService --> ORM
    RAGService --> Gemini
    RAGService -.->|Fallback khi lỗi/timeout| FallbackService

    ORM --> MySQL
```

---

## 2. Luồng Xử Lý Pipeline AI RAG & Dự Phòng (Fallback Sequence)

Mô hình RAG (Retrieval-Augmented Generation) kết hợp cơ chế Chịu lỗi (NFR-08) đảm bảo hệ thống phản hồi thông minh nhưng không bao giờ bị gián đoạn:

```mermaid
sequenceDiagram
    autonumber
    actor Customer as Khách Hàng
    participant UI as Giao diện Web
    participant RAG as RAGService
    participant DB as MySQL Database
    participant Gemini as Gemini 1.5 Flash LLM
    participant Fallback as FallbackService

    Customer->>UI: Nhập: "Khách muốn đặt sân bóng 7 người tối thứ Sáu"
    UI->>RAG: POST /api/ai/chat
    RAG->>RAG: Phân tích Intent (Loại sân: Sân 7, Ngày: 2026-09-11)
    
    RAG->>DB: SQL: SELECT * FROM time_slots WHERE type='Sân 7' AND date='2026-09-11' AND status='FREE'
    DB-->>RAG: Trả về danh sách khung giờ trống thực tế
    
    alt Không còn slot trống nào (result == [])
        RAG-->>UI: Thông báo lịch sự hết sân (Không gọi AI, chống Hallucination)
    else Có slot trống khả dụng
        RAG->>RAG: Đóng gói Context + Strict Grounding Prompt
        
        alt Gọi Gemini API thành công
            RAG->>Gemini: Gửi Prompt + Context (Timeout: 3s)
            Gemini-->>RAG: Trả về lời tư vấn tự nhiên & thân thiện
            RAG-->>UI: Hiển thị phản hồi AI
        else Lỗi kết nối / Quota / Timeout > 3s
            RAG->>Fallback: Kích hoạt format_traditional_slots(result)
            Fallback-->>RAG: Danh sách gạch đầu dòng định dạng chuẩn
            RAG-->>UI: Hiển thị kết quả Fallback truyền thống
        end
    end
    UI-->>Customer: Trình bày câu trả lời và mời bấm Đặt sân
```

---

## 3. Luồng Xử Lý Tranh Chấp Đặt Sân (Concurrency Pessimistic Locking)

Cơ chế khóa bi quan loại bỏ hoàn toàn nguy cơ 2 khách hàng đặt đè lên cùng 1 khung giờ:

```mermaid
sequenceDiagram
    autonumber
    actor UserA as Khách Hàng A
    actor UserB as Khách Hàng B (Trễ 1ms)
    participant API as Booking Controller
    participant Engine as MySQL InnoDB Engine

    UserA->>API: POST /api/bookings (slot_id=101)
    UserB->>API: POST /api/bookings (slot_id=101)

    Note over API,Engine: Bắt đầu giao dịch cô lập (Transaction A & B)

    API->>Engine: [Tx A] SELECT * FROM time_slots WHERE id=101 FOR UPDATE
    activate Engine
    Note over Engine: Đặt khóa độc quyền X-Lock trên dòng slot 101 cho Tx A
    Engine-->>API: Trả về bản ghi slot 101 (status = 'FREE')

    API->>Engine: [Tx B] SELECT * FROM time_slots WHERE id=101 FOR UPDATE
    Note over Engine: Tx B bị Block tạm thời vì dòng đang bị Tx A khóa!

    API->>Engine: [Tx A] UPDATE time_slots SET status='BOOKED' WHERE id=101
    API->>Engine: [Tx A] INSERT INTO bookings (...) VALUES (...)
    API->>Engine: [Tx A] COMMIT
    deactivate Engine
    Note over Engine: Giải phóng X-Lock

    API-->>UserA: HTTP 201 Created (Đặt sân thành công)

    activate Engine
    Note over Engine: Tx B được tiếp tục xử lý
    Engine-->>API: Trả về bản ghi slot 101 (Lúc này status đã là 'BOOKED'!)
    deactivate Engine

    API->>API: Kiểm tra slot.status != 'FREE' -> Rollback Tx B
    API-->>UserB: HTTP 409 Conflict ("Khung giờ này vừa được người khác đặt!")
```

---

## 4. Các Thành Phần Trọng Yếu & Quyết Định Kỹ Thuật

| Thành Phần | Công Nghệ Lựa Chọn | Lý Do & Giá Trị Kỹ Thuật |
| :--- | :--- | :--- |
| **Backend Framework** | Python Flask 3.0 | Nhẹ, linh hoạt, khởi động nhanh, tích hợp mượt mà với thư viện AI `google-genai` và ORM `Flask-SQLAlchemy`. |
| **Database Engine** | MySQL 8.0 (InnoDB) | Đảm bảo tính toàn vẹn ACID, hỗ trợ khóa dòng độc quyền `FOR UPDATE` và kiểm tra khóa ràng buộc `UNIQUE KEY`. |
| **Generative AI** | Google Gemini 1.5 Flash | Tốc độ sinh phản hồi cực nhanh (< 2s), chi phí tối ưu, cửa sổ ngữ cảnh lớn, hỗ trợ tiếng Việt xuất sắc. |
| **Kiến trúc Khả năng Chịu lỗi** | 2-Tier Fallback | Độc lập hoàn toàn với Cloud AI bên ngoài khi gặp sự cố, giữ vững hoạt động kinh doanh của quầy lễ tân. |

