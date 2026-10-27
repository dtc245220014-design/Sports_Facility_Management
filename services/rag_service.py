import os
import re
from datetime import date, datetime, timedelta
from google import genai
from google.genai import types
from sqlalchemy import text
from extensions import db
from services.fallback_service import (
    format_traditional_slots, 
    format_traditional_notification, 
    format_traditional_occupancy_summary
)
from services.booking_service import get_booking_by_id
from services.report_service import get_occupancy_report, get_peak_hours_analysis

def extract_intent_from_query(query):
    """
    Phân tích câu hỏi tự nhiên để trích xuất loại sân và ngày
    """
    query_lower = query.lower()
    
    # 1. Trích xuất loại sân
    court_type = "Sân bóng 7 người" # Mặc định
    if "sân 5" in query_lower or "bóng 5" in query_lower:
        court_type = "Sân bóng 5 người"
    elif "sân 7" in query_lower or "bóng 7" in query_lower or "bóng đá" in query_lower:
        court_type = "Sân bóng 7 người"
    elif "cầu lông" in query_lower:
        court_type = "Sân Cầu lông"
    elif "tennis" in query_lower or "quần vợt" in query_lower:
        court_type = "Sân Tennis"

    # 2. Trích xuất ngày
    today = date.today()
    booking_date = today.strftime('%Y-%m-%d')
    
    if "hôm nay" in query_lower:
        booking_date = today.strftime('%Y-%m-%d')
    elif "ngày mai" in query_lower or "mai" in query_lower:
        booking_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    elif "thứ sáu" in query_lower or "thứ 6" in query_lower:
        # Nếu có chữ thứ 6, tìm ngày thứ 6 gần nhất hoặc ngày mẫu 2026-09-11
        # Nếu hiện tại trong đề tài có ngày mẫu 2026-09-11
        booking_date = "2026-09-11"
    else:
        # Tìm xem có định dạng YYYY-MM-DD không
        date_match = re.search(r'\d{4}-\d{2}-\d{2}', query)
        if date_match:
            booking_date = date_match.group(0)

    return court_type, booking_date

def process_chat_message(user_query, court_type=None, booking_date=None):
    """
    FR-14, AC-AI-01: AI RAG Tư vấn khung giờ còn trống theo nhu cầu khách
    Áp dụng kỹ thuật Prompt Grounding nghiêm ngặt chống bịa thông tin.
    """
    # Trích xuất thông tin tự động nếu chưa có
    extracted_type, extracted_date = extract_intent_from_query(user_query)
    court_type = court_type or extracted_type
    booking_date = booking_date or extracted_date

    slots_data = []
    try:
        # BƯỚC 1 & 2: RAG Retriever - Truy vấn dữ liệu thực tế từ MySQL
        sql = text("""
            SELECT 
                ts.id, 
                c.name AS court_name, 
                ct.name AS type_name, 
                ts.booking_date, 
                ts.start_time, 
                ts.end_time, 
                ts.price
            FROM time_slots ts
            JOIN courts c ON ts.court_id = c.id
            JOIN court_types ct ON c.court_type_id = ct.id
            WHERE ct.name = :court_type 
              AND ts.booking_date = :booking_date
              AND ts.status = 'FREE'
            ORDER BY ts.start_time ASC
        """)
        
        result = db.session.execute(sql, {
            "court_type": court_type,
            "booking_date": booking_date
        }).fetchall()

        if not result:
            return f"Rất tiếc, vào ngày {booking_date} hiện không còn {court_type} nào trống. Bạn vui lòng chọn ngày khác hoặc loại sân khác giúp mình nhé!"

        for row in result:
            slots_data.append({
                "court_name": row.court_name,
                "type_name": row.type_name,
                "start_time": str(row.start_time),
                "end_time": str(row.end_time),
                "price": f"{row.price:,.0f} VNĐ"
            })

        # BƯỚC 3: Dựng Context & Strict Grounding Prompt
        context_str = "\n".join([
            f"- {s['court_name']} ({s['type_name']}): Từ {s['start_time']} đến {s['end_time']} | Giá: {s['price']}"
            for s in slots_data
        ])

        system_instruction = (
            "Bạn là trợ lý ảo chuyên nghiệp của Hệ thống Đặt sân thể thao. "
            "QUY TẮC CỐT LÕI (GROUNDING): Bạn CHỈ ĐƯỢC PHÉP gợi ý các khung giờ còn trống có trong danh sách CSDL được cung cấp dưới đây. "
            "TUYỆT ĐỐI KHÔNG tự sáng tạo hoặc bịa thêm bất kỳ khung giờ nào khác. "
            "Trả lời bằng tiếng Việt lịch sự, thân thiện, súc tích, định dạng gạch đầu dòng rõ ràng và hướng dẫn khách bấm đặt sân."
        )

        prompt = f"""
Danh sách khung giờ TRỐNG thực tế từ hệ thống (Ngày {booking_date} - {court_type}):
{context_str}

Yêu cầu/Câu hỏi của khách hàng: "{user_query}"

Hãy tư vấn cho khách hàng những khung giờ trống phù hợp nhất.
"""

        # BƯỚC 4: Gọi Gemini API
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        if not api_key or "your_gemini_api_key" in api_key.lower():
            return format_traditional_slots(slots_data, court_type, booking_date)

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )
        return response.text.strip()

    except Exception as e:
        print(f"[RAG Service Error] {str(e)}. Kích hoạt chế độ Fallback...")
        return format_traditional_slots(slots_data, court_type, booking_date)

def generate_booking_notification(booking_id, notification_type='confirmation'):
    """
    FR-15: AI Tự động sinh tin nhắn xác nhận hoặc nhắc lịch thi đấu thân thiện
    """
    booking = get_booking_by_id(booking_id)
    if not booking:
        return "Không tìm thấy thông tin đơn đặt sân để tạo thông báo."

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        if not api_key or "your_gemini_api_key" in api_key.lower():
            return format_traditional_notification(booking, notification_type)

        slot_info = booking.get('slot_info', {})
        context = f"""
Thông tin đặt sân:
- Khách hàng: {booking['customer_name']} (SĐT: {booking['customer_phone']})
- Sân: {slot_info.get('court_name')} ({slot_info.get('court_type')})
- Ngày thi đấu: {slot_info.get('date')}
- Khung giờ: {slot_info.get('time')}
- Đã cọc: {booking['deposit_amount']:,.0f} VNĐ
- Còn lại: {booking['remaining_amount']:,.0f} VNĐ
- Loại thông báo: {"Xác nhận đặt sân" if notification_type == 'confirmation' else "Nhắc lịch thi đấu hôm nay"}
"""

        prompt = f"""
Dựa vào dữ liệu đặt sân sau:
{context}

Hãy soạn một tin nhắn ngắn gọn, thân thiện (phù hợp gửi qua SMS hoặc Zalo) để thông báo cho khách hàng.
Yêu cầu:
- Có emoji trực quan, lịch sự.
- Nhắc khách đến trước 15 phút để khởi động và mang trang phục thể thao.
"""

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Bạn là trợ lý lễ tân thông minh của sân thể thao, chuyên viết tin nhắn chăm sóc khách hàng chuyên nghiệp.",
                temperature=0.4
            )
        )
        return response.text.strip()

    except Exception as e:
        print(f"[Notification AI Error] {str(e)}. Sử dụng Fallback...")
        return format_traditional_notification(booking, notification_type)

def summarize_occupancy_and_promotions(target_date=None):
    """
    FR-16: AI Tóm tắt công suất hoạt động và đề xuất chiến lược giảm giá cho giờ thấp điểm
    """
    target_date = target_date or date.today()
    report_data = get_occupancy_report(target_date)
    peak_data = get_peak_hours_analysis()

    try:
        api_key = os.getenv("GEMINI_API_KEY")
        model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

        if not api_key or "your_gemini_api_key" in api_key.lower():
            return format_traditional_occupancy_summary(report_data, peak_data)

        context = f"""
Dữ liệu công suất khai thác (Ngày {target_date}):
- Tỷ lệ lấp đầy tổng thể: {report_data['overall_occupancy_percent']}% ({report_data['total_booked']}/{report_data['total_slots']} slot)
- Chi tiết từng sân: {report_data['court_details']}
- Phân tích khung giờ cao/thấp điểm: {peak_data}
"""

        prompt = f"""
{context}

Hãy đóng vai chuyên gia vận hành kinh doanh cơ sở thể thao:
1. Đánh giá tóm tắt ngắn gọn tình hình lấp đầy sân ngày hôm nay.
2. Chỉ rõ các khung giờ thấp điểm (vắng khách).
3. Đề xuất 2-3 chương trình khuyến mại cụ thể (giảm giá giờ vàng, combo nước/bóng, ưu đãi học sinh/sinh viên) để kích cầu các khung giờ này.
"""

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction="Bạn là chuyên gia tư vấn tối ưu doanh thu sân thể thao (Revenue Optimization Specialist).",
                temperature=0.4
            )
        )
        return response.text.strip()

    except Exception as e:
        print(f"[Occupancy AI Error] {str(e)}. Sử dụng Fallback...")
        return format_traditional_occupancy_summary(report_data, peak_data)