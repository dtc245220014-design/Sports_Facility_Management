def format_traditional_slots(slots, court_type="sân thể thao", booking_date="ngày đã chọn"):
    """
    NFR-08: Fallback truyền thống hiển thị danh sách khung giờ trống khi AI API gặp sự cố
    """
    if not slots:
        return f"Rất tiếc, vào ngày {booking_date} hiện không còn {court_type} nào trống. Bạn vui lòng chọn ngày khác hoặc liên hệ hotline để được hỗ trợ!"

    response_lines = [
        f"📋 DANH SÁCH KHUNG GIỜ CÒN TRỐNG ({court_type} - {booking_date}):",
        "--------------------------------------------------"
    ]
    for slot in slots:
        c_name = getattr(slot, 'court_name', None) or (slot.get('court_name') if isinstance(slot, dict) else '')
        t_name = getattr(slot, 'type_name', None) or (slot.get('type_name') if isinstance(slot, dict) else '')
        st = getattr(slot, 'start_time', None) or (slot.get('start_time') if isinstance(slot, dict) else '')
        et = getattr(slot, 'end_time', None) or (slot.get('end_time') if isinstance(slot, dict) else '')
        price = getattr(slot, 'price', None) or (slot.get('price') if isinstance(slot, dict) else 0)
        
        try:
            formatted_price = f"{float(price):,.0f} VNĐ"
        except (ValueError, TypeError):
            formatted_price = str(price)

        line = f"• {c_name} ({t_name}): {st} - {et} | Giá: {formatted_price}"
        response_lines.append(line)
        
    response_lines.append("--------------------------------------------------")
    response_lines.append("Quý khách vui lòng bấm nút 'Đặt sân' trên sơ đồ hoặc gọi điện trực tiếp để giữ chỗ!")
    return "\n".join(response_lines)

def format_traditional_notification(booking, notification_type='confirmation'):
    """
    NFR-08: Fallback sinh tin nhắn xác nhận / nhắc lịch theo mẫu chuẩn
    """
    customer_name = booking.get('customer_name', 'Quý khách')
    slot_info = booking.get('slot_info', {})
    court_name = slot_info.get('court_name', 'Sân thể thao')
    date_str = slot_info.get('date', '')
    time_str = slot_info.get('time', '')
    deposit = booking.get('deposit_amount', 0)
    total = booking.get('total_price', 0)
    remaining = total - deposit

    if notification_type == 'confirmation':
        return (
            f"🎉 [XÁC NHẬN ĐẶT SÂN THÀNH CÔNG]\n"
            f"Kính chào {customer_name},\n"
            f"Hệ thống đã ghi nhận lịch đặt của bạn:\n"
            f"🏟️ Sân: {court_name}\n"
            f"📅 Thời gian: {time_str} ngày {date_str}\n"
            f"💵 Tiền cọc đã nhận: {deposit:,.0f} VNĐ\n"
            f"💳 Số tiền còn lại: {remaining:,.0f} VNĐ (thanh toán sau trận đấu)\n\n"
            f"⚠️ Quý khách vui lòng có mặt trước 15 phút để khởi động và nhận sân đúng giờ. Chúc bạn có trận đấu tuyệt vời!"
        )
    else: # reminder
        return (
            f"⏰ [NHẮC LỊCH THI ĐẤU HÔM NAY]\n"
            f"Kính chào {customer_name},\n"
            f"Bạn có lịch thi đấu tại {court_name} vào lúc {time_str} hôm nay ({date_str}).\n"
            f"Vui lòng chuẩn bị trang phục thể thao phù hợp và đến trước 15 phút nhé. Hẹn gặp lại bạn trên sân cỏ!"
        )

def format_traditional_occupancy_summary(report_data, peak_data):
    """
    NFR-08: Fallback tóm tắt báo cáo công suất theo quy tắc thống kê cố định
    """
    overall_rate = report_data.get('overall_occupancy_percent', 0)
    date_str = report_data.get('date', '')
    total_slots = report_data.get('total_slots', 0)
    total_booked = report_data.get('total_booked', 0)

    summary_lines = [
        f"📊 BÁO CÁO CÔNG SUẤT VÀ KHUYẾN MẠI (Ngày {date_str}):",
        f"- Tỷ lệ lấp đầy toàn cụm: {overall_rate}% ({total_booked}/{total_slots} slot đã đặt).",
    ]

    off_peak_slots = [p['time_range'] for p in peak_data if p.get('demand_level') == 'THẤP ĐIỂM']
    if off_peak_slots:
        summary_lines.append(f"- Khung giờ thấp điểm cần kích cầu: {', '.join(off_peak_slots)}.")
        summary_lines.append("- Đề xuất chính sách: Giảm 20% giá sân hoặc tặng kèm nước uống cho các khung giờ thấp điểm trên để nâng cao công suất khai thác.")
    else:
        summary_lines.append("- Các khung giờ đều duy trì lượng khách ổn định.")

    return "\n".join(summary_lines)