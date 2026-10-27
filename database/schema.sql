-- ====================================================================
-- HỆ THỐNG QUẢN LÝ SÂN THỂ THAO TÍCH HỢP AI - DATABASE SCHEMA (MYSQL 8+)
-- ====================================================================

CREATE DATABASE IF NOT EXISTS sports_facility_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE sports_facility_db;

-- 1. Bảng Người dùng (Phân quyền Admin / Staff)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    role ENUM('ADMIN', 'STAFF') NOT NULL DEFAULT 'STAFF',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 2. Bảng Loại sân thể thao
CREATE TABLE IF NOT EXISTS court_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE, -- Sân bóng 7 người, Sân bóng 5 người, Cầu lông, Tennis
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB;

-- 3. Bảng Danh mục Sân thực tế
CREATE TABLE IF NOT EXISTS courts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    court_type_id INT NOT NULL,
    name VARCHAR(100) NOT NULL, -- Ví dụ: Sân bóng 7 - A, Sân Cầu lông 01
    status ENUM('ACTIVE', 'MAINTENANCE') DEFAULT 'ACTIVE',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (court_type_id) REFERENCES court_types(id) ON DELETE CASCADE,
    INDEX idx_court_status (status)
) ENGINE=InnoDB;

-- 4. Bảng Cấu hình bảng giá theo khung giờ (Giờ cao điểm / Thấp điểm)
CREATE TABLE IF NOT EXISTS price_configs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    court_type_id INT NOT NULL,
    start_hour TIME NOT NULL,
    end_hour TIME NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    is_peak TINYINT(1) DEFAULT 0,
    FOREIGN KEY (court_type_id) REFERENCES court_types(id) ON DELETE CASCADE,
    INDEX idx_price_court_type (court_type_id)
) ENGINE=InnoDB;

-- 5. Bảng Khung giờ / Slot (Cốt lõi xử lý Đặt sân & Lock chống trùng lịch)
CREATE TABLE IF NOT EXISTS time_slots (
    id INT AUTO_INCREMENT PRIMARY KEY,
    court_id INT NOT NULL,
    booking_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    price DECIMAL(12, 2) NOT NULL,
    status ENUM('FREE', 'PENDING', 'BOOKED', 'MAINTENANCE') DEFAULT 'FREE',
    FOREIGN KEY (court_id) REFERENCES courts(id) ON DELETE CASCADE,
    -- RÀNG BUỘC CHỐNG TRÙNG LỊCH Ở CẤP CSDL
    UNIQUE KEY uq_court_slot (court_id, booking_date, start_time),
    -- INDEX TỐI ƯU TRUY VẤN LỊCH VÀ AI RETRIEVER
    INDEX idx_slot_query (booking_date, status),
    INDEX idx_slot_court_date (court_id, booking_date)
) ENGINE=InnoDB;

-- 6. Bảng Đặt sân & Theo dõi Thanh toán đặt cọc
CREATE TABLE IF NOT EXISTS bookings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    slot_id INT NOT NULL,
    customer_name VARCHAR(100) NOT NULL,
    customer_phone VARCHAR(20) NOT NULL,
    deposit_amount DECIMAL(12, 2) NOT NULL, -- Cọc 30% - 50%
    total_price DECIMAL(12, 2) NOT NULL,
    payment_status ENUM('DEPOSITED', 'PAID_FULL', 'REFUNDED') DEFAULT 'DEPOSITED',
    status ENUM('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED') DEFAULT 'CONFIRMED',
    note TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (slot_id) REFERENCES time_slots(id) ON DELETE CASCADE,
    INDEX idx_booking_phone (customer_phone),
    INDEX idx_booking_status (status)
) ENGINE=InnoDB;