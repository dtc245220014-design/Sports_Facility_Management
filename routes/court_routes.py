from flask import Blueprint, request, jsonify
from services.court_service import get_court_types, get_courts, get_time_slots, toggle_court_maintenance, get_price_configs

court_bp = Blueprint('court_bp', __name__, url_prefix='/api')

@court_bp.route('/court-types', methods=['GET'])
def list_court_types():
    """FR-03: Lấy danh mục loại sân"""
    types = get_court_types()
    return jsonify({"success": True, "data": types})

@court_bp.route('/courts', methods=['GET'])
def list_courts():
    """FR-03: Lấy danh mục sân thi đấu"""
    type_id = request.args.get('court_type_id', type=int)
    courts = get_courts(court_type_id=type_id)
    return jsonify({"success": True, "data": courts})

@court_bp.route('/slots', methods=['GET'])
def list_slots():
    """FR-04, FR-05: Lấy sơ đồ khung giờ và trạng thái đặt"""
    court_id = request.args.get('court_id', type=int)
    court_type_id = request.args.get('court_type_id', type=int)
    booking_date = request.args.get('date')
    status = request.args.get('status')

    slots = get_time_slots(
        court_id=court_id,
        court_type_id=court_type_id,
        booking_date=booking_date,
        status=status
    )
    return jsonify({"success": True, "data": slots})

@court_bp.route('/courts/<int:court_id>/maintenance', methods=['PUT'])
def update_maintenance(court_id):
    """FR-06: Chuyển trạng thái bảo trì sân và tự động khóa slot"""
    data = request.get_json() or {}
    is_maintenance = data.get('is_maintenance', True)

    success, message = toggle_court_maintenance(court_id, is_maintenance)
    if not success:
        return jsonify({"success": False, "message": message}), 404

    return jsonify({"success": True, "message": message})

@court_bp.route('/price-configs', methods=['GET'])
def list_price_configs():
    """FR-04: Lấy bảng giá theo khung giờ"""
    configs = get_price_configs()
    return jsonify({"success": True, "data": configs})

