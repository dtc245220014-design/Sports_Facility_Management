from datetime import date, datetime, timedelta
from sqlalchemy import func
from extensions import db
from models.models import Booking, TimeSlot, Court, CourtType

def get_revenue_summary(from_date=None, to_date=None):
    """
    FR-11: Thống kê tổng doanh thu thực tế và phân loại theo loại sân
    """
    query = db.session.query(
        func.count(Booking.id).label('total_bookings'),
        func.sum(Booking.deposit_amount).label('total_deposits'),
        func.sum(Booking.total_price).label('total_estimated_revenue')
    ).filter(Booking.status.in_(['CONFIRMED', 'COMPLETED']))

    if from_date:
        query = query.join(TimeSlot).filter(TimeSlot.booking_date >= from_date)
    if to_date:
        query = query.join(TimeSlot).filter(TimeSlot.booking_date <= to_date)

    summary = query.first()

    # Thống kê theo từng loại sân
    by_type_query = db.session.query(
        CourtType.name.label('court_type'),
        func.count(Booking.id).label('booking_count'),
        func.sum(Booking.total_price).label('revenue')
    ).join(Court, Court.court_type_id == CourtType.id)\
     .join(TimeSlot, TimeSlot.court_id == Court.id)\
     .join(Booking, Booking.slot_id == TimeSlot.id)\
     .filter(Booking.status.in_(['CONFIRMED', 'COMPLETED']))\
     .group_by(CourtType.name).all()

    by_type = [
        {
            "court_type": row.court_type,
            "booking_count": int(row.booking_count or 0),
            "revenue": float(row.revenue or 0)
        }
        for row in by_type_query
    ]

    return {
        "total_bookings": int(summary.total_bookings or 0) if summary else 0,
        "total_deposits": float(summary.total_deposits or 0) if summary else 0,
        "total_estimated_revenue": float(summary.total_estimated_revenue or 0) if summary else 0,
        "revenue_by_court_type": by_type
    }

def get_occupancy_report(target_date=None):
    """
    FR-12: Thống kê tỷ lệ lấp đầy sân (Occupancy Rate)
    """
    if not target_date:
        target_date = date.today()

    # Tổng số slot và số slot đã BOOKED theo từng sân
    courts = Court.query.all()
    court_stats = []
    total_all_slots = 0
    total_all_booked = 0

    for court in courts:
        slots = TimeSlot.query.filter_by(court_id=court.id, booking_date=target_date).all()
        total_slots = len(slots)
        booked_slots = len([s for s in slots if s.status == 'BOOKED'])
        maintenance_slots = len([s for s in slots if s.status == 'MAINTENANCE'])

        total_all_slots += total_slots
        total_all_booked += booked_slots

        rate = round((booked_slots / total_slots * 100), 1) if total_slots > 0 else 0

        court_stats.append({
            "court_id": court.id,
            "court_name": court.name,
            "court_type": court.court_type.name if court.court_type else "",
            "total_slots": total_slots,
            "booked_slots": booked_slots,
            "maintenance_slots": maintenance_slots,
            "occupancy_rate_percent": rate
        })

    overall_rate = round((total_all_booked / total_all_slots * 100), 1) if total_all_slots > 0 else 0

    return {
        "date": str(target_date),
        "overall_occupancy_percent": overall_rate,
        "total_slots": total_all_slots,
        "total_booked": total_all_booked,
        "court_details": court_stats
    }

def get_peak_hours_analysis():
    """
    FR-13: Phân tích khung giờ cao điểm và thấp điểm
    """
    slots = TimeSlot.query.all()
    time_bins = {}

    for s in slots:
        key = f"{s.start_time} - {s.end_time}"
        if key not in time_bins:
            time_bins[key] = {"total": 0, "booked": 0}
        time_bins[key]["total"] += 1
        if s.status == 'BOOKED':
            time_bins[key]["booked"] += 1

    peak_analysis = []
    for time_range, data in time_bins.items():
        rate = round((data["booked"] / data["total"] * 100), 1) if data["total"] > 0 else 0
        tag = "CAO ĐIỂM" if rate >= 60 else ("TRUNG BÌNH" if rate >= 30 else "THẤP ĐIỂM")
        peak_analysis.append({
            "time_range": time_range,
            "total_slots": data["total"],
            "booked_slots": data["booked"],
            "occupancy_rate_percent": rate,
            "demand_level": tag
        })

    peak_analysis.sort(key=lambda x: x["time_range"])
    return peak_analysis

