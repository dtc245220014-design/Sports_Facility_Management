from flask import Blueprint, request, jsonify
from services.booking_service import (
    create_booking, 
    get_bookings, 
    get_booking_by_id, 
    reschedule_booking, 
    cancel_booking, 
    complete_booking
)

booking_bp = Blueprint('booking_bp', __name__, url_prefix='/api/bookings')

@booking_bp.route('', methods=['POST'])
def add_booking():
    """
    FR-07, NFR-04: Đặt sân với Pessimistic Concurrency Lock chống trùng lịch
    """
    data = request.get_json() or {}
    slot_id = data.get('slot_id')
    customer_name = data.get('customer_name', '').strip()
    customer_phone = data.get('customer_phone', '').strip()
    custom_deposit = data.get('deposit_amount')
    note = data.get('note', '')

    if not slot_id or not customer_name or not customer_phone:
        return jsonify({
            "success": False, 
            "message": "Thiếu thông tin bắt buộc: slot_id, tên và số điện thoại khách hàng"
        }), 400

    customer_info = {
        "name": customer_name,
        "phone": customer_phone
    }

    try:
        result = create_booking(customer_info, slot_id, custom_deposit, note)
        status_code = result.get('status_code', 200)
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"success": False, "message": f"Lỗi hệ thống: {str(e)}"}), 500

@booking_bp.route('', methods=['GET'])
def list_bookings():
    """FR-05, FR-09: Quản lý khách hàng và danh sách lịch sử đặt"""
    phone = request.args.get('phone')
    booking_date = request.args.get('date')
    status = request.args.get('status')

    bookings = get_bookings(customer_phone=phone, booking_date=booking_date, status=status)
    return jsonify({"success": True, "data": bookings})

@booking_bp.route('/<int:booking_id>', methods=['GET'])
def get_booking(booking_id):
    booking = get_booking_by_id(booking_id)
    if not booking:
        return jsonify({"success": False, "message": "Không tìm thấy đơn đặt sân"}), 404
    return jsonify({"success": True, "data": booking})

@booking_bp.route('/<int:booking_id>/reschedule', methods=['PUT'])
def reschedule(booking_id):
    """FR-08: Đổi lịch thi đấu sang slot mới"""
    data = request.get_json() or {}
    new_slot_id = data.get('new_slot_id')

    if not new_slot_id:
        return jsonify({"success": False, "message": "Vui lòng chọn khung giờ mới (new_slot_id)"}), 400

    result = reschedule_booking(booking_id, new_slot_id)
    status_code = result.get('status_code', 200)
    return jsonify(result), status_code

@booking_bp.route('/<int:booking_id>/cancel', methods=['PUT'])
def cancel(booking_id):
    """FR-08: Hủy lịch thi đấu và xử lý cọc"""
    data = request.get_json() or {}
    reason = data.get('reason', 'Khách báo hủy')

    result = cancel_booking(booking_id, reason)
    status_code = result.get('status_code', 200)
    return jsonify(result), status_code

@booking_bp.route('/<int:booking_id>/complete', methods=['PUT'])
def complete(booking_id):
    """FR-10: Hoàn tất trận đấu và quyết toán thanh toán"""
    result = complete_booking(booking_id)
    status_code = result.get('status_code', 200)
    return jsonify(result), status_code

