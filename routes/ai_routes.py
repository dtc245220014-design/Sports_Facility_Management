from flask import Blueprint, request, jsonify
from services.rag_service import (
    process_chat_message, 
    generate_booking_notification, 
    summarize_occupancy_and_promotions
)

ai_bp = Blueprint('ai_bp', __name__, url_prefix='/api/ai')

@ai_bp.route('/chat', methods=['POST'])
def chat():
    """FR-14: AI Gợi ý khung giờ còn trống theo nhu cầu khách"""
    data = request.get_json() or {}
    message = data.get('message', '').strip()
    court_type = data.get('court_type')
    booking_date = data.get('date')

    if not message:
        return jsonify({"success": False, "message": "Nội dung tin nhắn không được để trống"}), 400

    reply = process_chat_message(message, court_type, booking_date)
    return jsonify({
        "success": True,
        "reply": reply
    })

@ai_bp.route('/generate-notification', methods=['POST'])
def generate_notification():
    """FR-15: AI Sinh tin nhắn xác nhận / nhắc lịch thi đấu"""
    data = request.get_json() or {}
    booking_id = data.get('booking_id')
    notification_type = data.get('type', 'confirmation') # 'confirmation' hoặc 'reminder'

    if not booking_id:
        return jsonify({"success": False, "message": "Vui lòng cung cấp booking_id"}), 400

    message = generate_booking_notification(booking_id, notification_type)
    return jsonify({
        "success": True,
        "notification_text": message
    })

@ai_bp.route('/occupancy-report', methods=['POST'])
def occupancy_report():
    """FR-16: AI Tóm tắt công suất và gợi ý khuyến mại giờ thấp điểm"""
    data = request.get_json() or {}
    target_date = data.get('date')

    summary = summarize_occupancy_and_promotions(target_date)
    return jsonify({
        "success": True,
        "analysis": summary
    })

