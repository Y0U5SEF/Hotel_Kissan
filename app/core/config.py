import os

# Base directory for the application
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Directory for storing receipts and invoices
RECEIPTS_DIR = os.path.join(BASE_DIR, 'receipts') 