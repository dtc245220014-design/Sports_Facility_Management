from datetime import datetime, date, timedelta
from extensions import db
from models.models import TimeSlot, Booking, Court

def create_booking(customer_info, slot_id, custom_deposit=None, note=""):
    """
    FR-07, NFR-04: Đặt sân với Pessimistic Concurrency Control (SELECT ... FOR UPDATE)
    Bảo vệ 100% chống đặt trùng lịch khi nhiều người cùng bấm đặt 1 slot cùng lúc.
    """
    try:
        # Bắt đầu giao dịch cô lập
        with db.session.begin_nested():
            # Khóa độc quyền dòng TimeSlot (Pessimistic Lock)
            slot = db.session.query(TimeSlot).filter_by(id=slot_id).with_for_update().first()

            if not slot:
                return {"success": False, "message": "Khung giờ không tồn tại!", "status_code": 404}

            if slot.status != 'FREE':
                return {
                    "success": False, 
                    "message": "Khung giờ này vừa được người khác đặt hoặc đang bảo trì! Vui lòng chọn khung giờ khác.", 
                    "status_code": 409
                }

            total_price = float(slot.price)

            # Quy định cọc 30% - 50%, mặc định 40% nếu không nhập
            min_deposit = total_price * 0.3
            max_deposit = total_price * 0.5

            if custom_deposit is not None and float(custom_deposit) > 0:
                deposit_amount = float(custom_deposit)
                if deposit_amount < min_deposit:
                    deposit_amount = min_deposit
                elif deposit_amount > total_price:
                    deposit_amount = total_price
            else:
                deposit_amount = total_price * 0.4  # Mặc định 40%

            # Cập nhật trạng thái slot thành BOOKED
            slot.status = 'BOOKED'

            # Tạo đơn đặt sân
            booking = Booking(
                slot_id=slot.id,
                customer_name=customer_info.get('name', '').strip(),
                customer_phone=customer_info.get('phone', '').strip(),
                deposit_amount=deposit_amount,
                total_price=total_price,
                payment_status='DEPOSITED',
                status='CONFIRMED',
                note=note
            )
            db.session.add(booking)
            db.session.flush() # Lấy booking.id

            booking_dict = booking.to_dict()

        # Commit toàn bộ giao dịch cấp cao
        db.session.commit()
        return {"success": True, "booking": booking_dict, "status_code": 201}

    except Exception as e:
        db.session.rollback()
        raise e

def get_bookings(customer_phone=None, booking_date=None, status=None):
    """Lấy danh sách đơn đặt sân kèm bộ lọc"""
    query = Booking.query.join(TimeSlot)
    if customer_phone:
        query = query.filter(Booking.customer_phone.like(f"%{customer_phone}%"))
    if booking_date:
        query = query.filter(TimeSlot.booking_date == booking_date)
    if status:
        query = query.filter(Booking.status == status)

    bookings = query.order_by(Booking.created_at.desc()).all()
    return [b.to_dict() for b in bookings]

def get_booking_by_id(booking_id):
    """Lấy chi tiết đơn đặt sân theo ID"""
    booking = Booking.query.get(booking_id)
    return booking.to_dict() if booking else None

def reschedule_booking(booking_id, new_slot_id):
    """
    FR-08: Đổi lịch thi đấu. Khóa nguyên tử cả 2 slot và hoán đổi an toàn.
    """
    try:
        with db.session.begin_nested():
            booking = Booking.query.get(booking_id)
            if not booking:
                return {"success": False, "message": "Không tìm thấy đơn đặt sân", "status_code": 404}

            if booking.status != 'CONFIRMED':
                return {"success": False, "message": "Chỉ có thể đổi lịch cho đơn ở trạng thái CONFIRMED", "status_code": 400}

            # Khóa slot mới
            new_slot = db.session.query(TimeSlot).filter_by(id=new_slot_id).with_for_update().first()
            if not new_slot or new_slot.status != 'FREE':
                return {"success": False, "message": "Khung giờ mới đã có người đặt hoặc bảo trì!", "status_code": 409}

            # Khóa slot cũ và giải phóng về FREE
            old_slot = db.session.query(TimeSlot).filter_by(id=booking.slot_id).with_for_update().first()
            if old_slot:
                old_slot.status = 'FREE'

            # Gán slot mới
            new_slot.status = 'BOOKED'
            booking.slot_id = new_slot.id
            booking.total_price = float(new_slot.price)
            booking.note = (booking.note or "") + f" [Đổi lịch sang slot {new_slot_id} vào {datetime.now().strftime('%Y-%m-%d %H:%M')}]"

        db.session.commit()
        return {"success": True, "message": "Đổi lịch thi đấu thành công!", "booking": booking.to_dict(), "status_code": 200}
    except Exception as e:
        db.session.rollback()
        raise e

def cancel_booking(booking_id, reason="Khách yêu cầu hủy"):
    """
    FR-08: Hủy lịch thi đấu kèm chính sách hoàn / phạt cọc:
    - Hủy trước giờ đấu > 24 tiếng: Hoàn 100% tiền cọc.
    - Hủy muộn <= 24 tiếng: Phạt giữ lại tiền cọc.
    """
    try:
        with db.session.begin_nested():
            booking = Booking.query.get(booking_id)
            if not booking:
                return {"success": False, "message": "Không tìm thấy đơn đặt sân", "status_code": 404}

            if booking.status in ('CANCELLED', 'COMPLETED'):
                return {"success": False, "message": f"Đơn đã ở trạng thái {booking.status}, không thể hủy", "status_code": 400}

            slot = db.session.query(TimeSlot).filter_by(id=booking.slot_id).with_for_update().first()
            if slot:
                slot.status = 'FREE'

            # Tính toán chính sách cọc
            match_datetime = datetime.combine(slot.booking_date, slot.start_time)
            now = datetime.now()
            hours_diff = (match_datetime - now).total_seconds() / 3600

            if hours_diff >= 24:
                refund_note = "Hủy trước 24h -> Hoàn 100% cọc"
                booking.payment_status = 'REFUNDED'
            else:
                refund_note = "Hủy muộn (< 24h) -> Không hoàn cọc (Phạt vi phạm lịch)"
                # Giữ nguyên DEPOSITED coi như doanh thu phạt

            booking.status = 'CANCELLED'
            booking.note = (booking.note or "") + f" [Hủy lịch: {reason}. {refund_note}]"

        db.session.commit()
        return {
            "success": True, 
            "message": f"Hủy lịch thành công. {refund_note}", 
            "booking": booking.to_dict(),
            "status_code": 200
        }
    except Exception as e:
        db.session.rollback()
        raise e

def complete_booking(booking_id):
    """
    FR-10: Hoàn tất trận đấu & Quyết toán thanh toán nốt phần còn lại
    """
    booking = Booking.query.get(booking_id)
    if not booking:
        return {"success": False, "message": "Không tìm thấy đơn đặt sân", "status_code": 404}

    booking.payment_status = 'PAID_FULL'
    booking.status = 'COMPLETED'
    db.session.commit()
    return {"success": True, "message": "Đã thanh toán đủ và hoàn tất trận đấu!", "booking": booking.to_dict(), "status_code": 200}

