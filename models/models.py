from datetime import datetime, date, time
from extensions import db
from werkzeug.security import check_password_hash, generate_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.Enum('ADMIN', 'STAFF', name='user_roles'), nullable=False, default='STAFF')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'full_name': self.full_name,
            'role': self.role,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class CourtType(db.Model):
    __tablename__ = 'court_types'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    courts = db.relationship('Court', backref='court_type', lazy=True, cascade='all, delete-orphan')
    price_configs = db.relationship('PriceConfig', backref='court_type', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'court_count': len(self.courts) if self.courts else 0
        }


class Court(db.Model):
    __tablename__ = 'courts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    court_type_id = db.Column(db.Integer, db.ForeignKey('court_types.id', ondelete='CASCADE'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Enum('ACTIVE', 'MAINTENANCE', name='court_status'), default='ACTIVE')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    time_slots = db.relationship('TimeSlot', backref='court', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'court_type_id': self.court_type_id,
            'court_type_name': self.court_type.name if self.court_type else None,
            'name': self.name,
            'status': self.status
        }


class PriceConfig(db.Model):
    __tablename__ = 'price_configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    court_type_id = db.Column(db.Integer, db.ForeignKey('court_types.id', ondelete='CASCADE'), nullable=False)
    start_hour = db.Column(db.Time, nullable=False)
    end_hour = db.Column(db.Time, nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    is_peak = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'court_type_id': self.court_type_id,
            'court_type_name': self.court_type.name if self.court_type else None,
            'start_hour': str(self.start_hour),
            'end_hour': str(self.end_hour),
            'price': float(self.price),
            'is_peak': bool(self.is_peak)
        }


class TimeSlot(db.Model):
    __tablename__ = 'time_slots'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    court_id = db.Column(db.Integer, db.ForeignKey('courts.id', ondelete='CASCADE'), nullable=False)
    booking_date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    price = db.Column(db.Numeric(12, 2), nullable=False)
    status = db.Column(db.Enum('FREE', 'PENDING', 'BOOKED', 'MAINTENANCE', name='slot_status'), default='FREE')

    __table_args__ = (
        db.UniqueConstraint('court_id', 'booking_date', 'start_time', name='uq_court_slot'),
    )

    bookings = db.relationship('Booking', backref='slot', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        active_booking = next((b for b in self.bookings if b.status in ('CONFIRMED', 'PENDING')), None)
        return {
            'id': self.id,
            'court_id': self.court_id,
            'court_name': self.court.name if self.court else None,
            'court_type_id': self.court.court_type_id if self.court else None,
            'court_type_name': self.court.court_type.name if self.court and self.court.court_type else None,
            'booking_date': self.booking_date.strftime('%Y-%m-%d') if self.booking_date else None,
            'start_time': str(self.start_time),
            'end_time': str(self.end_time),
            'price': float(self.price),
            'status': self.status,
            'booking': active_booking.to_dict() if active_booking else None
        }


class Booking(db.Model):
    __tablename__ = 'bookings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slot_id = db.Column(db.Integer, db.ForeignKey('time_slots.id', ondelete='CASCADE'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20), nullable=False)
    deposit_amount = db.Column(db.Numeric(12, 2), nullable=False)
    total_price = db.Column(db.Numeric(12, 2), nullable=False)
    payment_status = db.Column(db.Enum('DEPOSITED', 'PAID_FULL', 'REFUNDED', name='payment_status'), default='DEPOSITED')
    status = db.Column(db.Enum('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', name='booking_status'), default='CONFIRMED')
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'slot_id': self.slot_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'deposit_amount': float(self.deposit_amount),
            'total_price': float(self.total_price),
            'remaining_amount': float(self.total_price - self.deposit_amount),
            'payment_status': self.payment_status,
            'status': self.status,
            'note': self.note,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'slot_info': {
                'court_name': self.slot.court.name if self.slot and self.slot.court else '',
                'court_type': self.slot.court.court_type.name if self.slot and self.slot.court and self.slot.court.court_type else '',
                'date': self.slot.booking_date.strftime('%Y-%m-%d') if self.slot and self.slot.booking_date else '',
                'time': f"{self.slot.start_time} - {self.slot.end_time}" if self.slot else ''
            } if self.slot else None
        }

