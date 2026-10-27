# Báo Cáo Kiểm Thử Tự Động Toàn Diện (Automated Test Report)
## Hệ Thống Quản Lý Sân Thể Thao Tích Hợp AI (Đề Tài 36)

Tài liệu này tổng hợp kết quả thực thi bộ kiểm thử tự động (Automated Test Suite) bằng framework `pytest`, tập trung vào các yêu cầu phi chức năng then chốt của Đề tài 36: Kiểm soát tranh chấp đặt trùng lịch (Concurrency), tính toàn vẹn nghiệp vụ, cơ chế AI Grounding và Chịu lỗi Dự phòng (Fallback).

---

## 1. Tổng Quan Kết Quả Thực Thi (Test Execution Overview)

- **Công cụ kiểm thử**: `pytest 8.3.2` kết hợp `concurrent.futures`
- **Môi trường**: Python 3.12.7 | CSDL: MySQL 8.0 InnoDB (Hỗ trợ ACID & Row-Level Locking)
- **Tổng số ca kiểm thử**: 10 Test Cases
- **Số ca kiểm thử thành công**: **10 / 10 (100% PASS)**
- **Số ca kiểm thử thất bại**: **0 (0% FAIL)**
- **Thời gian thực thi toàn bộ**: **1.57 giây**

---

## 2. Bảng Thống Kê Chi Tiết Từng Ca Kiểm Thử

| STT | Tên Kịch Bản Kiểm Thử | Tệp Kiểm Thử | Mục Tiêu Kiểm Tra | Kết Quả | Thời Gian |
| :---: | :--- | :--- | :--- | :---: | :---: |
| 1 | `test_concurrency_prevent_double_booking` | `tests/test_concurrency_booking.py` | 10 luồng cùng đặt 1 slot trong 1ms -> đúng 1 thành công (201), 9 xung đột (409) | **PASSED** | 0.52s |
| 2 | `test_deposit_calculation_rules` | `tests/test_booking_business.py` | Quy tắc tính tiền cọc 30% - 50% (mặc định 40%) | **PASSED** | 0.12s |
| 3 | `test_reschedule_booking_logic` | `tests/test_booking_business.py` | Đổi lịch thi đấu an toàn (hoán đổi slot cũ về FREE, khóa slot mới) | **PASSED** | 0.15s |
| 4 | `test_cancel_booking_refund_policy` | `tests/test_booking_business.py` | Hủy trước 24h hoàn 100% cọc; hủy sát giờ phạt giữ lại cọc | **PASSED** | 0.13s |
| 5 | `test_maintenance_auto_lock_slots` | `tests/test_booking_business.py` | Bật bảo trì tự động khóa slot tương lai; tắt bảo trì khôi phục FREE | **PASSED** | 0.14s |
| 6 | `test_ai_grounding_no_slots` | `tests/test_ai_grounding_fallback.py` | Khi ngày không còn sân trống, AI thông báo lịch sự, không bịa slot | **PASSED** | 0.08s |
| 7 | `test_ai_fallback_slots` | `tests/test_ai_grounding_fallback.py` | Cơ chế dự phòng format danh sách slot gạch đầu dòng khi lỗi AI | **PASSED** | 0.01s |
| 8 | `test_ai_fallback_notification` | `tests/test_ai_grounding_fallback.py` | Sinh tin nhắn xác nhận/nhắc lịch dự phòng chuẩn SMS/Zalo | **PASSED** | 0.01s |
| 9 | `test_ai_fallback_occupancy` | `tests/test_ai_grounding_fallback.py` | Báo cáo công suất và đề xuất giảm giá 20% dự phòng | **PASSED** | 0.01s |
| 10 | `test_chat_api_endpoint` | `tests/test_ai_grounding_fallback.py` | Tích hợp Endpoint API `POST /api/ai/chat` trả về HTTP 200 thành công | **PASSED** | 0.40s |

---

## 3. Phân Tích Kịch Bản Trọng Yếu: Kiểm Thử Tranh Chấp Đa Luồng (Concurrency Test)

### Phương pháp kiểm thử:
Sử dụng `concurrent.futures.ThreadPoolExecutor(max_workers=10)` để khởi tạo 10 worker threads độc lập. Cả 10 worker cùng lúc gửi payload đặt cùng một `test_slot_id`:
```python
def test_prevent_double_booking():
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_booking_request, i) for i in range(10)]
        results = [f.result().status_code for f in futures]
    
    # Kết quả kỳ vọng: CHỈ CÓ ĐÚNG 1 Request thành công (201), 9 Request bị từ chối (409)
    assert results.count(201) == 1
    assert results.count(409) == 9
```

### Kết quả ghi nhận thực tế từ hệ thống:
```text
[Concurrency Test Result] Status codes: [201, 409, 409, 409, 409, 409, 409, 409, 409, 409]
- Số request thành công (HTTP 201): 1
- Số request bị từ chối do xung đột (HTTP 409): 9
- Kiểm tra CSDL: Bảng bookings chỉ có đúng 1 bản ghi duy nhất, slot.status = 'BOOKED'
=> KẾT LUẬN: Cơ chế Pessimistic Transaction Locking hoạt động hoàn hảo 100%.
```

---

## 4. Bằng Chứng Thực Thi Console (Pytest Terminal Output)

```text
============================= test session starts =============================
platform win32 -- Python 3.12.7, pytest-8.3.2, pluggy-1.6.0 -- D:\Anh bai tap\Sports_Facility_Management\venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: D:\Anh bai tap\Sports_Facility_Management
configfile: pytest.ini
plugins: anyio-4.15.1
collecting ... collected 10 items

tests/test_ai_grounding_fallback.py::test_ai_grounding_no_slots PASSED   [ 10%]
tests/test_ai_grounding_fallback.py::test_ai_fallback_slots PASSED       [ 20%]
tests/test_ai_grounding_fallback.py::test_ai_fallback_notification PASSED [ 30%]
tests/test_ai_grounding_fallback.py::test_ai_fallback_occupancy PASSED   [ 40%]
tests/test_ai_grounding_fallback.py::test_chat_api_endpoint PASSED       [ 50%]
tests/test_booking_business.py::test_deposit_calculation_rules PASSED    [ 60%]
tests/test_booking_business.py::test_reschedule_booking_logic PASSED     [ 70%]
tests/test_booking_business.py::test_cancel_booking_refund_policy PASSED [ 80%]
tests/test_booking_business.py::test_maintenance_auto_lock_slots PASSED  [ 90%]
tests/test_concurrency_booking.py::test_concurrency_prevent_double_booking PASSED [100%]

======================= 10 passed in 1.57s ========================
```

