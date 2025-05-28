import sqlite3
from app.core.config_handler import app_config
from datetime import datetime

def get_connection():
    db_path = app_config.get_db_path()
    return sqlite3.connect(db_path)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            id_type TEXT,
            id_number TEXT,
            dob TEXT,
            nationality TEXT,
            phone_code TEXT,
            phone_number TEXT,
            email TEXT,
            company TEXT,
            address TEXT,
            vip_status TEXT,
            preferences TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number TEXT NOT NULL UNIQUE,
            type TEXT,
            beds INTEGER,
            floor TEXT,
            location TEXT,
            status TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS check_ins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            checkin_id TEXT NOT NULL UNIQUE,
            transaction_id TEXT NOT NULL,
            guest_id INTEGER,
            room_id INTEGER,
            checkin_date TEXT NOT NULL,
            arrival_date TEXT NOT NULL,
            departure_date TEXT NOT NULL,
            num_guests INTEGER,
            total_paid REAL,
            amount_due REAL,
            payment_method TEXT,
            payment_status TEXT,
            actual_departure TEXT,
            FOREIGN KEY (guest_id) REFERENCES guests (id),
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')
    
    # New tables for settings
    c.execute('''
        CREATE TABLE IF NOT EXISTS hotel_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hotel_name TEXT,
            hotel_address TEXT,
            phone TEXT,
            email TEXT,
            website TEXT
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS room_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_type TEXT NOT NULL UNIQUE,
            night_rate REAL NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            default_price REAL NOT NULL,
            unit TEXT NOT NULL
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS booking_services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            unit_price_at_time_of_charge REAL NOT NULL,
            total_charge REAL NOT NULL,
            charge_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            charged_by_user_id INTEGER,
            notes TEXT,
            FOREIGN KEY (booking_id) REFERENCES check_ins (id),
            FOREIGN KEY (service_id) REFERENCES services (id),
            FOREIGN KEY (charged_by_user_id) REFERENCES users (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS tax_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            tax_type TEXT NOT NULL CHECK(tax_type IN ('percentage', 'fixed')),
            percentage REAL,
            amount REAL,
            apply_to_rooms BOOLEAN NOT NULL DEFAULT 1,
            apply_to_services BOOLEAN NOT NULL DEFAULT 1
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id TEXT NOT NULL UNIQUE,
            guest_first_name TEXT NOT NULL,
            guest_last_name TEXT NOT NULL,
            guest_email TEXT,
            guest_phone TEXT,
            arrival_date TEXT NOT NULL,
            num_guests INTEGER NOT NULL,
            room_id INTEGER,
            room_type TEXT,
            special_requests TEXT,
            payment_method TEXT,
            deposit_amount REAL,
            amount_due REAL,
            status TEXT NOT NULL,
            created_on TEXT NOT NULL,
            FOREIGN KEY (room_id) REFERENCES rooms (id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS reservation_cancellations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reservation_id TEXT NOT NULL,
            cancellation_date TEXT NOT NULL,
            reason TEXT NOT NULL,
            refund_amount REAL,
            notes TEXT,
            cancelled_by TEXT,
            FOREIGN KEY (reservation_id) REFERENCES reservations (reservation_id)
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_guest(guest):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO guests (
            first_name, last_name, id_type, id_number, dob, nationality, phone_code, phone_number, email, company, address, vip_status, preferences
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        guest['first_name'],
        guest['last_name'],
        guest.get('id_type'),
        guest.get('id_number'),
        guest.get('dob'),
        guest.get('nationality'),
        guest.get('phone_code'),
        guest.get('phone_number'),
        guest.get('email'),
        guest.get('company'),
        guest.get('address'),
        guest.get('vip_status'),
        guest.get('preferences')
    ))
    conn.commit()
    conn.close()

def update_guest(guest_id, guest):
    """Update an existing guest record"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE guests SET
            first_name = ?,
            last_name = ?,
            id_type = ?,
            id_number = ?,
            dob = ?,
            nationality = ?,
            phone_code = ?,
            phone_number = ?,
            email = ?,
            company = ?,
            address = ?,
            vip_status = ?,
            preferences = ?
        WHERE id = ?
    ''', (
        guest['first_name'],
        guest['last_name'],
        guest.get('id_type'),
        guest.get('id_number'),
        guest.get('dob'),
        guest.get('nationality'),
        guest.get('phone_code'),
        guest.get('phone_number'),
        guest.get('email'),
        guest.get('company'),
        guest.get('address'),
        guest.get('vip_status'),
        guest.get('preferences'),
        guest_id
    ))
    conn.commit()
    conn.close()

def delete_guest(guest_id):
    """Delete a guest record"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM guests WHERE id = ?', (guest_id,))
    conn.commit()
    conn.close()

def get_all_guests():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM guests')
    columns = [desc[0] for desc in c.description]
    guests = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return guests

# Rooms CRUD

def insert_room(room):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''INSERT INTO rooms (number, type, beds, floor, location, status) VALUES (?, ?, ?, ?, ?, ?)''',
        (room['number'], room.get('type'), room.get('beds'), room.get('floor'), room.get('location'), room.get('status')))
    conn.commit()
    conn.close()

def get_all_rooms():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''SELECT * FROM rooms''')
    columns = [desc[0] for desc in c.description]
    rooms = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return rooms

def update_room(room_id, room):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''UPDATE rooms SET number=?, type=?, beds=?, floor=?, location=?, status=? WHERE id=?''',
        (room['number'], room.get('type'), room.get('beds'), room.get('floor'), room.get('location'), room.get('status'), room_id))
    conn.commit()
    conn.close()

def delete_room(room_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM rooms WHERE id=?', (room_id,))
    conn.commit()
    conn.close()

def insert_checkin(checkin):
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO check_ins (
            checkin_id, transaction_id, guest_id, room_id, checkin_date, 
            arrival_date, departure_date, num_guests, total_paid, 
            amount_due, payment_method, payment_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        checkin['checkin_id'],
        checkin['transaction_id'],
        checkin['guest_id'],
        checkin['room_id'],
        checkin['checkin_date'],
        checkin['arrival_date'],
        checkin['departure_date'],
        checkin['num_guests'],
        checkin['total_paid'],
        checkin['amount_due'],
        checkin['payment_method'],
        checkin['payment_status']
    ))
    conn.commit()
    conn.close()

def get_all_checkins():
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT c.*, g.first_name, g.last_name, r.number as room_number, r.type as room_type
        FROM check_ins c
        LEFT JOIN guests g ON c.guest_id = g.id
        LEFT JOIN rooms r ON c.room_id = r.id
        ORDER BY c.checkin_date DESC
    ''')
    columns = [desc[0] for desc in c.description]
    checkins = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return checkins

def get_guest_id_by_name(first_name, last_name):
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id FROM guests WHERE first_name = ? AND last_name = ?', (first_name, last_name))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def get_available_rooms_count():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM rooms WHERE status = "Vacant"')
    count = c.fetchone()[0]
    conn.close()
    return count

def update_checkin(checkin_id, checkin):
    """Update an existing check-in record"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE check_ins SET
            total_paid = ?,
            amount_due = ?,
            payment_method = ?,
            payment_status = ?,
            actual_departure = ?
        WHERE checkin_id = ?
    ''', (
        checkin['total_paid'],
        checkin['amount_due'],
        checkin['payment_method'],
        checkin['payment_status'],
        checkin.get('actual_departure'),
        checkin_id
    ))
    conn.commit()
    conn.close()

# Hotel Settings CRUD
def get_hotel_settings():
    """Get hotel settings from database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM hotel_settings LIMIT 1')
    settings = c.fetchone()
    conn.close()
    if settings:
        return dict(zip(['id', 'hotel_name', 'hotel_address', 'phone', 'email', 'website'], settings))
    return None

def update_hotel_settings(settings):
    """Update hotel settings in database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO hotel_settings (
            id, hotel_name, hotel_address, phone, email, website
        ) VALUES (
            (SELECT id FROM hotel_settings LIMIT 1),
            ?, ?, ?, ?, ?
        )
    ''', (
        settings['hotel_name'],
        settings['hotel_address'],
        settings['phone'],
        settings['email'],
        settings['website']
    ))
    conn.commit()
    conn.close()

# Room Rates CRUD
def get_room_rates():
    """Get all room rates from database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM room_rates')
    columns = [desc[0] for desc in c.description]
    rates = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return rates

def update_room_rate(room_type, night_rate):
    """Update room rate in database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO room_rates (room_type, night_rate)
        VALUES (?, ?)
    ''', (room_type, night_rate))
    conn.commit()
    conn.close()

# Services CRUD
def get_services():
    """Get all services from database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM services')
    columns = [desc[0] for desc in c.description]
    services = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return services

def add_service(service):
    """Add a new service to database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO services (name, default_price, unit)
        VALUES (?, ?, ?)
    ''', (
        service['name'],
        service['default_price'],
        service['unit']
    ))
    conn.commit()
    conn.close()

def update_service(service_id, service):
    """Update service in database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE services SET name=?, default_price=?, unit=?
        WHERE id=?
    ''', (
        service['name'],
        service['default_price'],
        service['unit'],
        service_id
    ))
    conn.commit()
    conn.close()

def delete_service(service_id):
    """Delete service from database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM services WHERE id=?', (service_id,))
    conn.commit()
    conn.close()

# Tax Rates CRUD
def get_tax_rates():
    """Get all tax rates from database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM tax_rates')
    columns = [desc[0] for desc in c.description]
    rates = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return rates

def add_tax_rate(tax_rate):
    """Add a new tax rate to database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO tax_rates (name, tax_type, percentage, amount, apply_to_rooms, apply_to_services)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (
        tax_rate['name'],
        tax_rate['tax_type'],
        tax_rate['percentage'],
        tax_rate['amount'],
        tax_rate['apply_to_rooms'],
        tax_rate['apply_to_services']
    ))
    conn.commit()
    conn.close()

def update_tax_rate(tax_rate_id, tax_rate):
    """Update tax rate in database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE tax_rates SET name=?, tax_type=?, percentage=?, amount=?, apply_to_rooms=?, apply_to_services=?
        WHERE id=?
    ''', (
        tax_rate['name'],
        tax_rate['tax_type'],
        tax_rate['percentage'],
        tax_rate['amount'],
        tax_rate['apply_to_rooms'],
        tax_rate['apply_to_services'],
        tax_rate_id
    ))
    conn.commit()
    conn.close()

def delete_tax_rate(tax_rate_id):
    """Delete tax rate from database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM tax_rates WHERE id=?', (tax_rate_id,))
    conn.commit()
    conn.close()

# Booking Services CRUD
def add_booking_service(booking_service):
    """Add a new service charge to a booking"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO booking_services (
            booking_id, service_id, quantity, unit_price_at_time_of_charge,
            total_charge, charged_by_user_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        booking_service['booking_id'],
        booking_service['service_id'],
        booking_service['quantity'],
        booking_service['unit_price_at_time_of_charge'],
        booking_service['total_charge'],
        booking_service.get('charged_by_user_id'),
        booking_service.get('notes')
    ))
    conn.commit()
    conn.close()

def get_booking_services(booking_id):
    """Get all service charges for a booking"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT bs.*, s.name as service_name, s.unit
        FROM booking_services bs
        JOIN services s ON bs.service_id = s.id
        WHERE bs.booking_id = ?
        ORDER BY bs.charge_date DESC
    ''', (booking_id,))
    columns = [desc[0] for desc in c.description]
    services = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return services

def delete_booking_service(service_id):
    """Delete a service charge"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM booking_services WHERE id = ?', (service_id,))
    conn.commit()
    conn.close()

def get_total_booking_charges(booking_id):
    """Get the total amount of all service charges for a booking"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT COALESCE(SUM(total_charge), 0) as total
        FROM booking_services
        WHERE booking_id = ?
    ''', (booking_id,))
    total = c.fetchone()[0]
    conn.close()
    return total

def add_reservation(reservation):
    """Add a new reservation to the database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO reservations (
            reservation_id, guest_first_name, guest_last_name, guest_email, guest_phone,
            arrival_date, num_guests, room_id,
            special_requests, payment_method, deposit_amount, amount_due, status, created_on
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        reservation['reservation_id'],
        reservation['guest_first_name'],
        reservation['guest_last_name'],
        reservation.get('guest_email'),
        reservation.get('guest_phone'),
        reservation['arrival_date'],
        int(reservation['num_guests']),
        reservation.get('room_id'),
        reservation.get('special_requests'),
        reservation.get('payment_method'),
        float(reservation.get('deposit_amount', 0)),
        float(reservation.get('amount_due', 0)),
        reservation['status'],
        reservation['created_on']
    ))
    conn.commit()
    conn.close()

def get_reservations():
    """Get all reservations from the database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT r.*, rm.number as room_number 
        FROM reservations r
        LEFT JOIN rooms rm ON r.room_id = rm.id
        ORDER BY r.created_on DESC
    ''')
    columns = [desc[0] for desc in c.description]
    reservations = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return reservations

def update_reservation(reservation):
    """Update an existing reservation"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE reservations SET
            guest_first_name = ?,
            guest_last_name = ?,
            guest_email = ?,
            guest_phone = ?,
            arrival_date = ?,
            num_guests = ?,
            room_id = ?,
            room_type = ?,
            special_requests = ?,
            payment_method = ?,
            deposit_amount = ?,
            amount_due = ?,
            status = ?
        WHERE reservation_id = ?
    ''', (
        reservation['guest_first_name'],
        reservation['guest_last_name'],
        reservation.get('guest_email'),
        reservation.get('guest_phone'),
        reservation['arrival_date'],
        int(reservation['num_guests']),
        reservation.get('room_id'),
        reservation['room_type'],
        reservation.get('special_requests'),
        reservation.get('payment_method'),
        float(reservation.get('deposit_amount', 0)),
        float(reservation.get('amount_due', 0)),
        reservation['status'],
        reservation['reservation_id']
    ))
    conn.commit()
    conn.close()

def delete_reservation(reservation_id):
    """Delete a reservation"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('DELETE FROM reservations WHERE reservation_id = ?', (reservation_id,))
    conn.commit()
    conn.close()

def cancel_reservation(reservation_id, cancellation_data):
    """Cancel a reservation and record the cancellation details"""
    conn = get_connection()
    c = conn.cursor()
    
    try:
        # Start transaction
        c.execute('BEGIN TRANSACTION')
        
        # Update reservation status
        c.execute('''
            UPDATE reservations 
            SET status = 'Cancelled' 
            WHERE reservation_id = ?
        ''', (reservation_id,))
        
        # Insert cancellation record
        c.execute('''
            INSERT INTO reservation_cancellations (
                reservation_id, cancellation_date, reason, 
                refund_amount, notes, cancelled_by
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            reservation_id,
            datetime.now().strftime('%Y-%m-%d %H:%M'),
            cancellation_data['reason'],
            float(cancellation_data.get('refund_amount', 0)),
            cancellation_data.get('notes', ''),
            cancellation_data.get('cancelled_by', 'System')
        ))
        
        # Get the room_id from the reservation
        c.execute('SELECT room_id FROM reservations WHERE reservation_id = ?', (reservation_id,))
        room_id = c.fetchone()[0]
        
        # Update room status to Vacant
        if room_id:
            c.execute('''
                UPDATE rooms 
                SET status = 'Vacant' 
                WHERE id = ?
            ''', (room_id,))
        
        # Commit transaction
        conn.commit()
        return True
        
    except Exception as e:
        # Rollback on error
        conn.rollback()
        print(f"Error cancelling reservation: {e}")
        return False
        
    finally:
        conn.close()

def get_cancellation_details(reservation_id):
    """Get cancellation details for a reservation"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT * FROM reservation_cancellations 
        WHERE reservation_id = ?
    ''', (reservation_id,))
    columns = [desc[0] for desc in c.description]
    cancellation = dict(zip(columns, c.fetchone())) if c.fetchone() else None
    conn.close()
    return cancellation 