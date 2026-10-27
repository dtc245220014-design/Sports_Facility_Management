import pytest
from datetime import date, time, timedelta
from app import create_app
from extensions import db
from models.models import TimeSlot, Booking, Court
from services.booking_service import create_booking, reschedule_booking, cancel_booking
from services.court_service import toggle_court_maintenance

@pytest.fixture
def app_ctx():
    app = create_app({'TESTING': True})
    with app.app_context():
        yield app

def get_or_create_slot(court_id, booking_date, start_time, end_time, price):
    slot = TimeSlot.query.filter_by(
        court_id=court_id, 
        booking_date=booking_date, 
        start_time=start_time
    ).first()
    if not slot:
        slot = TimeSlot(
            court_id=court_id,
            booking_date=booking_date,
            start_time=start_time,
            end_time=end_time,
            price=price,
            status='FREE'
        )
        db.session.add(slot)
        db.session.commit()
    else:
        Booking.query.filter_by(slot_id=slot.id).delete()
        slot.status = 'FREE'
        slot.price = price
        db.session.commit()
    return slot

def test_deposit_calculation_rules(app_ctx):
    """Kiểm tra quy định tính cọc 30% - 50%"""
    court = Court.query.first()
    slot = get_or_create_slot(court.id, date(2028, 2, 1), time(17, 30, 0), time(19, 0, 0), 500000.0)

    # 1. Không truyền custom_deposit -> Mặc định 40% (200.000đ)
    cust_info = {"name": "Test User A", "phone": "0981111111"}
    res = create_booking(cust_info, slot.id)
    assert res['success'] is True
    assert res['booking']['deposit_amount'] == 200000.0
    assert res['booking']['total_price'] == 500000.0
    assert res['booking']['remaining_amount'] == 300000.0

def test_reschedule_booking_logic(app_ctx):
    """Kiểm tra đổi lịch thi đấu sang slot mới"""
    court = Court.query.first()
    slot1 = get_or_create_slot(court.id, date(2028, 3, 1), time(16, 0), time(17, 30), 300000.0)
    slot2 = get_or_create_slot(court.id, date(2028, 3, 1), time(17, 30), time(19, 0), 500000.0)

    # Đặt slot 1
    booking_res = create_booking({"name": "Test User B", "phone": "0982222222"}, slot1.id)
    booking_id = booking_res['booking']['id']

    # Đổi lịch sang slot 2
    resch_res = reschedule_booking(booking_id, slot2.id)
    assert resch_res['success'] is True
    
    # Xác minh slot 1 đã về FREE, slot 2 đã là BOOKED
    assert db.session.get(TimeSlot, slot1.id).status == 'FREE'
    assert db.session.get(TimeSlot, slot2.id).status == 'BOOKED'

def test_cancel_booking_refund_policy(app_ctx):
    """Kiểm tra chính sách hoàn/phạt cọc khi hủy lịch"""
    court = Court.query.first()
    far_date = date(2028, 5, 1)
    slot_far = get_or_create_slot(court.id, far_date, time(19, 0), time(20, 30), 500000.0)

    b_far = create_booking({"name": "Khách hủy sớm", "phone": "0983333333"}, slot_far.id)['booking']
    cancel_res_far = cancel_booking(b_far['id'])
    assert cancel_res_far['success'] is True
    assert cancel_res_far['booking']['payment_status'] == 'REFUNDED'
    assert db.session.get(TimeSlot, slot_far.id).status == 'FREE'

def test_maintenance_auto_lock_slots(app_ctx):
    """FR-06: Chuyển sân sang bảo trì -> Khóa tự động các khung giờ trống"""
    court = Court.query.first()
    future_date = date(2028, 6, 1)
    test_slot = get_or_create_slot(court.id, future_date, time(8, 0), time(9, 30), 100000.0)

    # Chuyển sang MAINTENANCE
    toggle_court_maintenance(court.id, True)
    slot_after = db.session.get(TimeSlot, test_slot.id)
    assert slot_after.status == 'MAINTENANCE'

    # Khôi phục ACTIVE
    toggle_court_maintenance(court.id, False)
    slot_restored = db.session.get(TimeSlot, test_slot.id)
    assert slot_restored.status == 'FREE'

