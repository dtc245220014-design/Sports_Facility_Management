import pytest
from app import create_app
from services import rag_service, fallback_service

@pytest.fixture
def app_ctx():
    app = create_app({'TESTING': True})
    with app.app_context():
        yield app

def test_ai_grounding_no_slots(app_ctx):
    """
    AC-AI-01: AI Grounding - Tuyệt đối không ảo giác/bịa khung giờ trống
    Khi ngày yêu cầu không có sân trống nào, AI phải thông báo lịch sự là đã hết sân.
    """
    # Ngày trong quá khứ hoặc ngày không có slot nào được tạo (ví dụ năm 2040)
    empty_date = "2040-01-01"
    response = rag_service.process_chat_message(
        user_query="Còn sân bóng 7 người không?",
        court_type="Sân bóng 7 người",
        booking_date=empty_date
    )
    # Phải thông báo hết sân, không được sinh giờ ảo
    assert "Rất tiếc" in response or "không còn" in response
    assert empty_date in response

def test_ai_fallback_slots():
    """NFR-08: Kiểm thử cơ chế dự phòng hiển thị slot truyền thống"""
    sample_slots = [
        {
            "court_name": "Sân bóng 7 - A",
            "type_name": "Sân bóng 7 người",
            "start_time": "19:00:00",
            "end_time": "20:30:00",
            "price": 500000.0
        }
    ]
    fallback_res = fallback_service.format_traditional_slots(sample_slots, "Sân bóng 7 người", "2026-09-11")
    assert "DANH SÁCH KHUNG GIỜ CÒN TRỐNG" in fallback_res
    assert "Sân bóng 7 - A" in fallback_res
    assert "500,000 VNĐ" in fallback_res

def test_ai_fallback_notification():
    """NFR-08: Kiểm thử sinh tin nhắn dự phòng theo mẫu chuẩn"""
    sample_booking = {
        "customer_name": "Nguyễn Văn Test",
        "deposit_amount": 200000,
        "total_price": 500000,
        "slot_info": {
            "court_name": "Sân Cầu lông 01",
            "court_type": "Sân Cầu lông",
            "date": "2026-09-12",
            "time": "17:30 - 19:00"
        }
    }
    confirm_msg = fallback_service.format_traditional_notification(sample_booking, 'confirmation')
    assert "XÁC NHẬN ĐẶT SÂN THÀNH CÔNG" in confirm_msg
    assert "Nguyễn Văn Test" in confirm_msg
    assert "200,000 VNĐ" in confirm_msg

    reminder_msg = fallback_service.format_traditional_notification(sample_booking, 'reminder')
    assert "NHẮC LỊCH THI ĐẤU HÔM NAY" in reminder_msg
    assert "17:30 - 19:00" in reminder_msg

def test_ai_fallback_occupancy():
    """NFR-08: Kiểm thử báo cáo công suất dự phòng"""
    report_data = {
        "date": "2026-09-11",
        "overall_occupancy_percent": 45.5,
        "total_slots": 30,
        "total_booked": 14
    }
    peak_data = [
        {"time_range": "06:00:00 - 07:30:00", "demand_level": "THẤP ĐIỂM"}
    ]
    res = fallback_service.format_traditional_occupancy_summary(report_data, peak_data)
    assert "BÁO CÁO CÔNG SUẤT VÀ KHUYẾN MẠI" in res
    assert "45.5%" in res
    assert "Giảm 20% giá sân" in res

def test_chat_api_endpoint(app_ctx):
    """Kiểm thử route POST /api/ai/chat phản hồi thành công (HTTP 200)"""
    client = app_ctx.test_client()
    res = client.post('/api/ai/chat', json={
        "message": "Tôi muốn tìm sân bóng 7 người",
        "court_type": "Sân bóng 7 người",
        "date": "2026-09-11"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert len(data['reply']) > 0

