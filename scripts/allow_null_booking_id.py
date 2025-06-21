import sqlite3
import os

# Adjust the path to your database file as needed
DB_PATH = os.path.join(os.environ['APPDATA'], 'KISSAN', 'kissan.db')

def migrate():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # 1. Create new table with booking_id and guest_id nullable
        c.execute('''
            CREATE TABLE IF NOT EXISTS booking_services_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_id INTEGER,
                guest_id INTEGER,
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
        # 2. Copy data (guest_id will be NULL for existing rows)
        c.execute('''
            INSERT INTO booking_services_new
            (id, booking_id, guest_id, service_id, quantity, unit_price_at_time_of_charge, total_charge, charge_date, charged_by_user_id, notes)
            SELECT id, booking_id, NULL, service_id, quantity, unit_price_at_time_of_charge, total_charge, charge_date, charged_by_user_id, notes
            FROM booking_services
        ''')
        # 3. Drop old table
        c.execute('DROP TABLE booking_services')
        # 4. Rename new table
        c.execute('ALTER TABLE booking_services_new RENAME TO booking_services')
        conn.commit()
        print('Migration successful: booking_id and guest_id now allow NULL in booking_services.')
    except Exception as e:
        print(f'Error during migration: {e}')
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate() 