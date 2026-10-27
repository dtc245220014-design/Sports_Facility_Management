import os
import sys
import datetime
import pymysql
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')


load_dotenv()

DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'root')
DB_PASSWORD = os.getenv('DB_PASSWORD', '280706')
DB_NAME = os.getenv('DB_NAME', 'sports_facility_db')

def get_connection(use_database=True):
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME if use_database else None,
        charset='utf8mb4',
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=True
    )

def init_database():
    print(f"[*] Đang kết nối tới MySQL ({DB_HOST})...")
    conn = get_connection(use_database=False)
    with conn.cursor() as cursor:
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        print(f"[+] Cơ sở dữ liệu `{DB_NAME}` đã được tạo hoặc đã tồn tại.")
    conn.close()

    # Thực thi schema.sql
    conn = get_connection(use_database=True)
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql_commands = f.read()

    with conn.cursor() as cursor:
        for statement in sql_commands.split(';'):
            # Loại bỏ các dòng comment
            lines = [line for line in statement.splitlines() if not line.strip().startswith('--')]
            cleaned_statement = '\n'.join(lines).strip()
            if cleaned_statement:
                cursor.execute(cleaned_statement)
        print("[+] Các bảng trong schema đã được tạo thành công.")

    conn.close()

def seed_data():
    conn = get_connection(use_database=True)
    with conn.cursor() as cursor:
        # 1. Seed Users (Mã hóa mật khẩu chuẩn bảo mật)
        print("[*] Nạp tài khoản người dùng...")
        users = [
            ('admin', generate_password_hash('admin123'), 'Nguyễn Văn Quản Lý', 'ADMIN'),
            ('staff1', generate_password_hash('staff123'), 'Trần Thị Thu Ngân', 'STAFF'),
            ('staff2', generate_password_hash('staff123'), 'Lê Hoàng Nhân Viên', 'STAFF')
        ]
        for username, pwd_hash, full_name, role in users:
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE full_name=%s, role=%s;
            """, (username, pwd_hash, full_name, role, full_name, role))

        # 2. Seed Court Types
        print("[*] Nạp danh mục loại sân...")
        court_types = [
            (1, 'Sân bóng 7 người', 'Sân cỏ nhân tạo chất lượng cao 7 người tiêu chuẩn mini FIFA'),
            (2, 'Sân bóng 5 người', 'Sân cỏ nhân tạo mini 5 người có mái che'),
            (3, 'Sân Cầu lông', 'Sân thảm chuyên dụng chống trơn trượt đạt chuẩn thi đấu'),
            (4, 'Sân Tennis', 'Sân cứng tiêu chuẩn quốc tế có hệ thống đèn LED cao áp')
        ]
        for c_id, name, desc in court_types:
            cursor.execute("""
                INSERT INTO court_types (id, name, description)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE name=%s, description=%s;
            """, (c_id, name, desc, name, desc))

        # 3. Seed Courts
        print("[*] Nạp danh mục sân thực tế...")
        courts = [
            (1, 1, 'Sân bóng 7 - A', 'ACTIVE'),
            (2, 1, 'Sân bóng 7 - B', 'ACTIVE'),
            (3, 2, 'Sân bóng 5 - A', 'ACTIVE'),
            (4, 3, 'Sân Cầu lông 01', 'ACTIVE'),
            (5, 3, 'Sân Cầu lông 02', 'ACTIVE'),
            (6, 4, 'Sân Tennis 01', 'ACTIVE')
        ]
        for c_id, type_id, name, status in courts:
            cursor.execute("""
                INSERT INTO courts (id, court_type_id, name, status)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE name=%s, status=%s;
            """, (c_id, type_id, name, status, name, status))

        # 4. Seed Price Configs
        print("[*] Nạp bảng giá cao điểm / thấp điểm...")
        prices = [
            # Sân bóng 7 người
            (1, '06:00:00', '17:30:00', 300000.0, 0),
            (1, '17:30:00', '22:30:00', 500000.0, 1),
            # Sân bóng 5 người
            (2, '06:00:00', '17:30:00', 200000.0, 0),
            (2, '17:30:00', '22:30:00', 350000.0, 1),
            # Sân Cầu lông
            (3, '06:00:00', '17:30:00', 80000.0, 0),
            (3, '17:30:00', '22:30:00', 130000.0, 1),
            # Sân Tennis
            (4, '06:00:00', '17:30:00', 150000.0, 0),
            (4, '17:30:00', '22:30:00', 250000.0, 1)
        ]
        cursor.execute("TRUNCATE TABLE price_configs;")
        for type_id, start_h, end_h, price, is_peak in prices:
            cursor.execute("""
                INSERT INTO price_configs (court_type_id, start_hour, end_hour, price, is_peak)
                VALUES (%s, %s, %s, %s, %s);
            """, (type_id, start_h, end_h, price, is_peak))

        # 5. Seed Time Slots cho 7 ngày tới và ngày 2026-09-11 (Thứ sáu trong prompt mẫu)
        print("[*] Khởi tạo khung giờ (Time Slots)...")
        today = datetime.date.today()
        target_dates = [today + datetime.timedelta(days=i) for i in range(7)]
        friday_sample = datetime.date(2026, 9, 11)
        if friday_sample not in target_dates:
            target_dates.append(friday_sample)

        time_definitions = [
            ('06:00:00', '07:30:00', False),
            ('07:30:00', '09:00:00', False),
            ('16:00:00', '17:30:00', False),
            ('17:30:00', '19:00:00', True),
            ('19:00:00', '20:30:00', True),
            ('20:30:00', '22:00:00', True),
        ]

        price_map = {
            1: (300000.0, 500000.0),
            2: (200000.0, 350000.0),
            3: (80000.0, 130000.0),
            4: (150000.0, 250000.0)
        }

        for b_date in target_dates:
            for court_id, type_id, _, _ in courts:
                normal_p, peak_p = price_map[type_id]
                for st, et, is_peak in time_definitions:
                    price = peak_p if is_peak else normal_p
                    cursor.execute("""
                        INSERT INTO time_slots (court_id, booking_date, start_time, end_time, price, status)
                        VALUES (%s, %s, %s, %s, %s, 'FREE')
                        ON DUPLICATE KEY UPDATE price=%s;
                    """, (court_id, b_date, st, et, price, price))

        # Cài đặt một số slot đã đặt trước cho ngày 2026-09-11 và hôm nay để demo
        print("[*] Tạo các đơn đặt sân mẫu...")
        # 1. Đặt slot 17:30 - 19:00 của Sân bóng 7 - A ngày 2026-09-11
        cursor.execute("""
            SELECT id, price FROM time_slots 
            WHERE court_id = 1 AND booking_date = %s AND start_time = '17:30:00'
        """, (friday_sample,))
        slot = cursor.fetchone()
        if slot:
            slot_id = slot['id']
            slot_price = slot['price']
            cursor.execute("UPDATE time_slots SET status = 'BOOKED' WHERE id = %s", (slot_id,))
            deposit = float(slot_price) * 0.4
            cursor.execute("""
                INSERT INTO bookings (slot_id, customer_name, customer_phone, deposit_amount, total_price, payment_status, status, note)
                VALUES (%s, %s, %s, %s, %s, 'DEPOSITED', 'CONFIRMED', %s)
            """, (slot_id, 'Nguyễn Tiến Linh', '0912345678', deposit, slot_price, 'Đã cọc 40% qua chuyển khoản'))


        # 2. Khóa bảo trì sân Tennis buổi sáng
        cursor.execute("""
            UPDATE time_slots SET status = 'MAINTENANCE' 
            WHERE court_id = 6 AND booking_date = %s AND start_time = '06:00:00'
        """, (today,))

        print("[+] Hoàn tất nạp dữ liệu mẫu thành công!")
    conn.close()

if __name__ == '__main__':
    init_database()
    seed_data()
