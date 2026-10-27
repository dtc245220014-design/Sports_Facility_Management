# Đặc Tả Kiến Trúc Pipeline AI RAG & Kỹ Thuật Prompt Grounding
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

Tài liệu này chi tiết hóa thiết kế kỹ thuật của Pipeline **AI RAG (Retrieval-Augmented Generation)** 4 giai đoạn, các mẫu System Prompt, kỹ thuật Grounding chống ảo giác và tích hợp 3 tính năng AI cốt lõi theo đề bài.

---

## 1. Quy Trình 4 Pha Của AI RAG Pipeline

```
[Người Dùng Hỏi]
       │
       ▼
┌────────────────────────────────────────┐
│  PHA 1: Intent & Entity Extraction     │  -> Trích xuất: Loại sân, Ngày, Khung giờ
└────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  PHA 2: SQL Context Retriever          │  -> SELECT FROM time_slots WHERE status='FREE'
└────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  PHA 3: Prompt Grounding & Augmentation│  -> Ghép dữ liệu thực tế vào System Instruction
└────────────────────────────────────────┘
       │
       ▼
┌────────────────────────────────────────┐
│  PHA 4: Generation & Fallback Handler  │  -> Gọi Gemini 1.5 Flash (Fallback nếu lỗi)
└────────────────────────────────────────┘
       │
       ▼
[Trả Lời Lịch Sự & Chính Xác]
```

### Pha 1: Trích xuất Ý định & Thực thể (Intent & Entity Extraction)
- Câu hỏi tự nhiên của khách (ví dụ: *"Khách muốn đặt sân bóng 7 người tối thứ Sáu"* hoặc *"Sân cầu lông chiều mai còn giờ nào?"*) được đưa qua bộ trích xuất quy tắc hoặc regex để bóc tách:
  - `court_type`: "Sân bóng 7 người", "Sân bóng 5 người", "Sân Cầu lông", "Sân Tennis".
  - `booking_date`: Ngày cụ thể theo định dạng `YYYY-MM-DD` (Ví dụ: `2026-09-11`).

### Pha 2: Truy Vấn CSDL Thực Tế (SQL Context Retriever)
- Hệ thống thực thi truy vấn tham số hóa an toàn tới MySQL:
  ```sql
  SELECT ts.id, c.name AS court_name, ct.name AS type_name, 
         ts.booking_date, ts.start_time, ts.end_time, ts.price
  FROM time_slots ts
  JOIN courts c ON ts.court_id = c.id
  JOIN court_types ct ON c.court_type_id = ct.id
  WHERE ct.name = :court_type 
    AND ts.booking_date = :booking_date
    AND ts.status = 'FREE'
  ORDER BY ts.start_time ASC;
  ```
- *Quy tắc Chống Bịa Thông Tin (Grounding Cut-off)*: Nếu kết quả truy vấn rỗng (`result == []`), hệ thống lập tức trả về thông báo lịch sự là đã hết sân cho ngày đó mà **không gửi lệnh gọi LLM**.

### Pha 3: Đóng Gói Ngữ Cảnh & Ràng Buộc Grounding (Prompt Augmentation)
- Dữ liệu thô từ SQL được chuyển đổi thành chuỗi ngữ cảnh tường minh (Context String).
- Áp dụng kỹ thuật **System Instruction Grounding** để khóa chặt phạm vi hiểu biết của mô hình: chỉ được phép trả lời dựa trên những slot có trong danh sách được cung cấp.

### Pha 4: Tạo Sinh & Chịu Lỗi (Generation & Fallback Handler)
- Gọi Google Gemini 1.5 Flash với tham số `temperature = 0.2` (giảm thiểu tính ngẫu nhiên, tăng tối đa độ chính xác của thông tin).
- Nếu API gặp sự cố (mất mạng, timeout > 3s, hết quota), `try-except` tự động chuyển tiếp sang `fallback_service.py` trả về danh sách gạch đầu dòng truyền thống.

---

## 2. Các Mẫu Prompt Chuẩn Cho 3 Tính Năng AI

### 2.1. Tính Năng 1: AI Tư Vấn Khung Giờ Còn Trống (FR-14)
- **Prompt Mẫu Theo Yêu Cầu Đề Bài 36**:
  ```text
  System: Bạn là trợ lý ảo chuyên nghiệp của Hệ thống Đặt sân thể thao.
  QUY TẮC CỐT LÕI (GROUNDING): Bạn CHỈ ĐƯỢC PHÉP gợi ý các khung giờ còn trống có trong danh sách CSDL được cung cấp dưới đây.
  TUYỆT ĐỐI KHÔNG tự sáng tạo hoặc bịa thêm bất kỳ khung giờ nào khác.
  Trả lời bằng tiếng Việt lịch sự, thân thiện, súc tích, định dạng gạch đầu dòng rõ ràng và hướng dẫn khách bấm đặt sân.

  User:
  Danh sách khung giờ TRỐNG thực tế từ hệ thống (Ngày {{booking_date}} - {{court_type}}):
  {{available_slots}}

  Yêu cầu/Câu hỏi của khách hàng: "{{user_query}}"

  Hãy tư vấn cho khách hàng những khung giờ trống phù hợp nhất.
  ```

### 2.2. Tính Năng 2: AI Tự Động Sinh Tin Nhắn Xác Nhận / Nhắc Lịch (FR-15)
- **Prompt Sinh Tin Nhắn**:
  ```text
  System: Bạn là trợ lý lễ tân thông minh của sân thể thao, chuyên viết tin nhắn chăm sóc khách hàng chuyên nghiệp, ngắn gọn để gửi qua SMS hoặc Zalo.

  User:
  Dựa vào thông tin đặt sân sau:
  - Khách hàng: {{customer_name}} (SĐT: {{customer_phone}})
  - Sân thi đấu: {{court_name}} ({{court_type}})
  - Thời gian: {{start_time}} - {{end_time}} ngày {{booking_date}}
  - Tiền cọc đã nhận: {{deposit_amount}} VNĐ
  - Tiền còn lại: {{remaining_amount}} VNĐ
  - Loại tin nhắn: {{notification_type}} (Xác nhận đặt sân / Nhắc lịch thi đấu hôm nay)

  Hãy soạn một tin nhắn ngắn gọn, có emoji trực quan, lịch sự và nhắc khách đến trước 15 phút để khởi động và nhận sân.
  ```

### 2.3. Tính Năng 3: AI Tóm Tắt Công Suất & Đề Xuất Khuyến Mại Giờ Thấp Điểm (FR-16)
- **Prompt Phân Tích Công Suất & Khuyến Mại**:
  ```text
  System: Bạn là chuyên gia tư vấn tối ưu doanh thu sân thể thao (Revenue Optimization Specialist).

  User:
  Dữ liệu công suất khai thác (Ngày {{target_date}}):
  - Tỷ lệ lấp đầy tổng thể: {{overall_occupancy_percent}}% ({{total_booked}}/{{total_slots}} slot)
  - Chi tiết từng sân: {{court_details}}
  - Phân tích khung giờ cao/thấp điểm: {{peak_hours_data}}

  Hãy đóng vai chuyên gia vận hành kinh doanh cơ sở thể thao:
  1. Đánh giá tóm tắt ngắn gọn tình hình lấp đầy sân ngày hôm nay.
  2. Chỉ rõ các khung giờ thấp điểm (vắng khách).
  3. Đề xuất 2-3 chương trình khuyến mại cụ thể (giảm giá giờ vàng, combo nước/bóng, ưu đãi học sinh/sinh viên) để kích cầu các khung giờ này.
  ```

---

## 3. Bảng Kiểm Thử Chống Ảo Giác (Grounding Verification Matrix)

| Kịch Bản Đầu Vào | Dữ Liệu SQL Retriever | Phản Hồi AI Kỳ Vọng | Đạt / Không Đạt |
| :--- | :--- | :--- | :---: |
| "Khách muốn đặt sân bóng 7 người tối thứ Sáu" | 2 slot trống: 19:00 - 20:30 & 20:30 - 22:00 | Chỉ liệt kê đúng 2 slot này kèm giá, không đưa thêm slot 17:30 (vì đã bị đặt). | ✅ ĐẠT |
| "Tìm sân cầu lông ngày 2040-01-01" | Rỗng (`[]`) | Báo ngay là không còn sân trống ngày đó, không tự tạo giờ mới. | ✅ ĐẠT |
| Mất kết nối internet / lỗi API Gemini | Không kết nối được | Kích hoạt Fallback trả về mẫu gạch đầu dòng truyền thống trong < 0.5s. | ✅ ĐẠT |

