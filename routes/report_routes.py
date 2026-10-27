from flask import Blueprint, request, jsonify
from services.report_service import get_revenue_summary, get_occupancy_report, get_peak_hours_analysis

report_bp = Blueprint('report_bp', __name__, url_prefix='/api/reports')

@report_bp.route('/revenue', methods=['GET'])
def revenue():
    """FR-11: Thống kê doanh thu"""
    from_date = request.args.get('from_date')
    to_date = request.args.get('to_date')
    data = get_revenue_summary(from_date=from_date, to_date=to_date)
    return jsonify({"success": True, "data": data})

@report_bp.route('/occupancy', methods=['GET'])
def occupancy():
    """FR-12: Báo cáo công suất sân"""
    date_str = request.args.get('date')
    data = get_occupancy_report(target_date=date_str)
    return jsonify({"success": True, "data": data})

@report_bp.route('/peak-hours', methods=['GET'])
def peak_hours():
    """FR-13: Phân tích khung giờ cao điểm và thấp điểm"""
    data = get_peak_hours_analysis()
    return jsonify({"success": True, "data": data})

