import sqlite3
from app.core.config_handler import app_config
from datetime import datetime

def get_connection():
    db_path = app_config.get_db_path()
    return sqlite3.connect(db_path)

def init_db():
    conn = get_connection()
    c = conn.cursor()
    
    # Create users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            role TEXT NOT NULL,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create guests table
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
            address TEXT,
            vip_status TEXT,
            preferences TEXT,
            company_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (company_id) REFERENCES company_accounts(id) ON DELETE SET NULL
        )
    ''')
    
    # Create company_accounts table
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            email TEXT,
            tax_id TEXT,
            billing_terms TEXT,
            credit_limit DECIMAL(10,2),
            payment_due_days INTEGER,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create company_charges table
    c.execute('''
        CREATE TABLE IF NOT EXISTS company_charges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER NOT NULL,
            checkin_id TEXT NOT NULL,
            guest_id INTEGER NOT NULL,
            charge_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            room_charges DECIMAL(10,2) DEFAULT 0,
            service_charges DECIMAL(10,2) DEFAULT 0,
            total_amount DECIMAL(10,2) NOT NULL,
            is_paid BOOLEAN DEFAULT 0,
            payment_date TIMESTAMP,
            notes TEXT,
            FOREIGN KEY (company_id) REFERENCES company_accounts(id),
            FOREIGN KEY (checkin_id) REFERENCES check_ins(checkin_id),
            FOREIGN KEY (guest_id) REFERENCES guests(id)
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
            status TEXT,
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
    try:
        c.execute('''
            INSERT INTO guests (
                first_name, last_name, id_type, id_number, dob,
                nationality, phone_code, phone_number, email,
                address, vip_status, preferences, company_id
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
            guest.get('address'),
            guest.get('vip_status'),
            guest.get('preferences'),
            guest.get('company_id')
        ))
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            raise ValueError("A guest with this ID number already exists")
        raise
    finally:
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
            address = ?,
            vip_status = ?,
            preferences = ?,
            company_id = ?
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
        guest.get('address'),
        guest.get('vip_status'),
        guest.get('preferences'),
        guest.get('company_id'),
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
            amount_due, payment_method, status
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
        checkin['status']
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
            status = ?,
            actual_departure = ?
        WHERE checkin_id = ?
    ''', (
        checkin['total_paid'],
        checkin['amount_due'],
        checkin['payment_method'],
        checkin['status'],
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

def get_filtered_checkins(from_date, to_date, room_type=None, status=None):
    conn = get_connection()
    c = conn.cursor()

    query = '''
        SELECT c.checkin_id, g.first_name || ' ' || g.last_name AS guest_name,
               g.id_number, r.number as room_number, c.arrival_date, c.departure_date, c.status
        FROM check_ins c
        LEFT JOIN guests g ON c.guest_id = g.id
        LEFT JOIN rooms r ON c.room_id = r.id
        WHERE date(c.arrival_date) BETWEEN ? AND ?
    '''
    params = [from_date, to_date]

    if room_type and room_type != "All":
        query += " AND LOWER(r.type) = ?"
        params.append(room_type.lower())

    if status and status != "All":
        query += " AND LOWER(c.status) = ?"
        params.append(status.lower())

    query += " ORDER BY c.arrival_date DESC"

    c.execute(query, params)
    columns = [desc[0] for desc in c.description]
    results = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return results


def get_filtered_reservations(from_date, to_date, room_type="All", status="All"):
    conn = get_connection()
    c = conn.cursor()

    query = """
        SELECT reservation_id, guest_first_name, guest_last_name, room_type,
               arrival_date, num_guests, deposit_amount, status, created_on
        FROM reservations
        WHERE date(arrival_date) BETWEEN ? AND ?
    """
    params = [from_date, to_date]

    if room_type != "All":
        query += " AND room_type = ?"
        params.append(room_type)

    if status != "All":
        query += " AND status = ?"
        params.append(status)

    c.execute(query, params)
    columns = [desc[0] for desc in c.description]
    results = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return results

def get_all_reservations():
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

# User Authentication Functions
def create_user(username, password_hash, first_name, last_name, role):
    """Create a new user in the database"""
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO users (username, password_hash, first_name, last_name, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, first_name, last_name, role))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user_by_username(username):
    """Get user by username"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    columns = [desc[0] for desc in c.description]
    user = c.fetchone()
    conn.close()
    return dict(zip(columns, user)) if user else None

def update_user_password(user_id, new_password_hash):
    """Update user's password"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET password_hash = ? WHERE id = ?', (new_password_hash, user_id))
    conn.commit()
    conn.close()

def deactivate_user(user_id):
    """Deactivate a user account"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('UPDATE users SET is_active = 0 WHERE id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    """Get all users from the database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT id, username, first_name, last_name, role, is_active, created_at FROM users')
    columns = [desc[0] for desc in c.description]
    users = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return users

# Company Accounts CRUD
def add_company_account(company):
    """Add a new company account to database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO company_accounts (
            name, address, phone, email, tax_id, billing_terms,
            credit_limit, payment_due_days, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        company['name'],
        company.get('address'),
        company.get('phone'),
        company.get('email'),
        company.get('tax_id'),
        company.get('billing_terms'),
        company.get('credit_limit', 0),
        company.get('payment_due_days', 30),
        company.get('status', 'active')
    ))
    conn.commit()
    conn.close()

def get_company_accounts():
    """Get all company accounts from database"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM company_accounts ORDER BY name')
    columns = [desc[0] for desc in c.description]
    companies = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return companies

def get_company_account(company_id):
    """Get a specific company account by ID"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM company_accounts WHERE id = ?', (company_id,))
    columns = [desc[0] for desc in c.description]
    company = c.fetchone()
    conn.close()
    return dict(zip(columns, company)) if company else None

def update_company_account(company):
    """Update an existing company account"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        UPDATE company_accounts SET
            name = ?,
            address = ?,
            phone = ?,
            email = ?,
            tax_id = ?,
            billing_terms = ?,
            credit_limit = ?,
            payment_due_days = ?,
            status = ?
        WHERE id = ?
    ''', (
        company['name'],
        company.get('address'),
        company.get('phone'),
        company.get('email'),
        company.get('tax_id'),
        company.get('billing_terms'),
        company.get('credit_limit', 0),
        company.get('payment_due_days', 30),
        company.get('status', 'active'),
        company['id']
    ))
    conn.commit()
    conn.close()

# Company Charges CRUD
def add_company_charge(charge):
    """Add a new company charge"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        INSERT INTO company_charges (
            company_id, checkin_id, guest_id, room_charges,
            service_charges, total_amount, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (
        charge['company_id'],
        charge['checkin_id'],
        charge['guest_id'],
        charge.get('room_charges', 0),
        charge.get('service_charges', 0),
        charge['total_amount'],
        charge.get('notes')
    ))
    conn.commit()
    conn.close()

def get_company_charges(company_id=None, is_paid=None):
    """Get company charges, optionally filtered by company and payment status"""
    conn = get_connection()
    c = conn.cursor()
    
    query = '''
        SELECT cc.*, g.first_name, g.last_name, ci.checkin_id, ci.arrival_date, ci.departure_date,
               r.number as room_number
        FROM company_charges cc
        JOIN guests g ON cc.guest_id = g.id
        JOIN check_ins ci ON cc.checkin_id = ci.checkin_id
        LEFT JOIN rooms r ON ci.room_id = r.id
    '''
    params = []
    
    if company_id is not None:
        query += ' WHERE cc.company_id = ?'
        params.append(company_id)
        if is_paid is not None:
            query += ' AND cc.is_paid = ?'
            params.append(is_paid)
    elif is_paid is not None:
        query += ' WHERE cc.is_paid = ?'
        params.append(is_paid)
    
    query += ' ORDER BY cc.charge_date DESC'
    
    c.execute(query, params)
    columns = [desc[0] for desc in c.description]
    charges = [dict(zip(columns, row)) for row in c.fetchall()]
    conn.close()
    return charges

def mark_company_charge_paid(charge_id, payment_date=None):
    """Mark a company charge as paid"""
    conn = get_connection()
    c = conn.cursor()
    if payment_date is None:
        payment_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    c.execute('''
        UPDATE company_charges SET
            is_paid = 1,
            payment_date = ?
        WHERE id = ?
    ''', (payment_date, charge_id))
    conn.commit()
    conn.close()

def get_company_balance(company_id):
    """Get total unpaid balance for a company"""
    conn = get_connection()
    c = conn.cursor()
    c.execute('''
        SELECT SUM(total_amount) as balance
        FROM company_charges
        WHERE company_id = ? AND is_paid = 0
    ''', (company_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result and result[0] is not None else 0
