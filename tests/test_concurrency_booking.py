import concurrent.futures
from datetime import date, time
from app import create_app
from extensions import db
from models.models import TimeSlot, Booking, Court

def test_concurrency_prevent_double_booking():
    """
    KỊCH BẢN KIỂM THỬ TRANH CHẤP ĐỒNG THỜI (CONCURRENCY LOCKING TEST)
    FR-07, NFR-04: Đảm bảo khi 10 người dùng cùng gửi yêu cầu đặt 1 slot trong cùng 1 millisecond,
    hệ thống áp dụng Pessimistic Locking (SELECT ... FOR UPDATE)
    -> CHỈ DUY NHẤT 1 Request thành công (HTTP 201)
    -> 9 Request còn lại bị từ chối với mã xung đột (HTTP 409 Conflict)
    """
    app = create_app({'TESTING': True})

    # 1. Chuẩn bị 1 slot kiểm thử riêng biệt
    test_slot_id = None
    with app.app_context():
        # Tìm 1 sân bất kỳ
        court = Court.query.filter_by(status='ACTIVE').first()
        assert court is not None, "Cần ít nhất 1 sân active trong CSDL"

        # Tạo 1 slot test riêng cho ngày 2028-01-01
        test_date = date(2028, 1, 1)
        test_slot = TimeSlot.query.filter_by(court_id=court.id, booking_date=test_date).first()
        if not test_slot:
            test_slot = TimeSlot(
                court_id=court.id,
                booking_date=test_date,
                start_time=time(19, 0, 0),
                end_time=time(20, 30, 0),
                price=500000.0,
                status='FREE'
            )
            db.session.add(test_slot)
            db.session.commit()
        else:
            # Xóa các booking cũ nếu có và reset slot về FREE
            Booking.query.filter_by(slot_id=test_slot.id).delete()
            test_slot.status = 'FREE'
            db.session.commit()

        test_slot_id = test_slot.id

    # 2. Định nghĩa hàm worker đặt sân
    def make_booking_attempt(user_index):
        worker_app = create_app({'TESTING': True})
        with worker_app.test_client() as c:
            payload = {
                "slot_id": test_slot_id,
                "customer_name": f"Khách hàng số {user_index}",
                "customer_phone": f"090000000{user_index}",
                "deposit_amount": 200000
            }
            res = c.post('/api/bookings', json=payload)
            return res.status_code, res.get_json()

    # 3. Kích hoạt 10 luồng đồng thời tranh chấp cùng 1 slot_id
    worker_count = 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=worker_count) as executor:
        futures = [executor.submit(make_booking_attempt, i) for i in range(worker_count)]
        results = [f.result() for f in futures]

    status_codes = [r[0] for r in results]
    print(f"\n[Concurrency Test Result] Status codes: {status_codes}")

    # 4. Kiểm tra kỳ vọng (Asssertions)
    success_count = status_codes.count(201)
    conflict_count = status_codes.count(409)

    assert success_count == 1, f"Kỳ vọng đúng 1 request thành công (201), nhưng có {success_count}"
    assert conflict_count == 9, f"Kỳ vọng 9 request bị từ chối với mã xung đột (409), nhưng có {conflict_count}"

    # 5. Kiểm tra tính toàn vẹn trong CSDL
    with app.app_context():
        slot = TimeSlot.query.get(test_slot_id)
        assert slot.status == 'BOOKED', "Trạng thái slot phải là BOOKED"

        bookings = Booking.query.filter_by(slot_id=test_slot_id).all()
        assert len(bookings) == 1, f"Chỉ được phép có đúng 1 bản ghi Booking trong DB, nhưng có {len(bookings)}"

