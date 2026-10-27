from datetime import date
from extensions import db
from models.models import CourtType, Court, TimeSlot, PriceConfig

def get_court_types():
    """Lấy danh sách các loại sân thể thao"""
    types = CourtType.query.all()
    return [t.to_dict() for t in types]

def get_courts(court_type_id=None):
    """Lấy danh sách sân thi đấu theo loại sân hoặc tất cả"""
    query = Court.query
    if court_type_id:
        query = query.filter_by(court_type_id=court_type_id)
    courts = query.all()
    return [c.to_dict() for c in courts]

def get_time_slots(court_id=None, court_type_id=None, booking_date=None, status=None):
    """
    Truy vấn ma trận khung giờ linh hoạt theo sân, loại sân, ngày và trạng thái
    """
    query = TimeSlot.query.join(Court)
    if court_id:
        query = query.filter(TimeSlot.court_id == court_id)
    if court_type_id:
        query = query.filter(Court.court_type_id == court_type_id)
    if booking_date:
        query = query.filter(TimeSlot.booking_date == booking_date)
    if status:
        query = query.filter(TimeSlot.status == status)
        
    slots = query.order_by(TimeSlot.booking_date, TimeSlot.start_time).all()
    return [s.to_dict() for s in slots]

def toggle_court_maintenance(court_id, is_maintenance):
    """
    FR-06: Quản lý lịch bảo trì.
    Khi chuyển trạng thái sang MAINTENANCE, tự động khóa tất cả khung giờ FREE trong tương lai của sân đó.
    Khi chuyển lại ACTIVE, hoàn lại trạng thái FREE.
    """
    court = Court.query.get(court_id)
    if not court:
        return False, "Không tìm thấy sân thi đấu"

    new_status = 'MAINTENANCE' if is_maintenance else 'ACTIVE'
    court.status = new_status

    today = date.today()
    if is_maintenance:
        # Khóa các slot FREE thành MAINTENANCE
        TimeSlot.query.filter(
            TimeSlot.court_id == court_id,
            TimeSlot.booking_date >= today,
            TimeSlot.status == 'FREE'
        ).update({'status': 'MAINTENANCE'}, synchronize_session=False)
    else:
        # Khôi phục các slot MAINTENANCE về FREE
        TimeSlot.query.filter(
            TimeSlot.court_id == court_id,
            TimeSlot.booking_date >= today,
            TimeSlot.status == 'MAINTENANCE'
        ).update({'status': 'FREE'}, synchronize_session=False)

    db.session.commit()
    return True, f"Cập nhật trạng thái sân thành {new_status} thành công"

def get_price_configs():
    """Lấy danh sách cấu hình giá theo giờ cao điểm/thấp điểm"""
    configs = PriceConfig.query.all()
    return [c.to_dict() for c in configs]

