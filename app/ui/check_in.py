from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDateEdit, QCalendarWidget, QFormLayout, QStackedWidget, QCompleter, QGridLayout, QMessageBox, QFrame, QSpinBox, QTextEdit, QProgressBar, QDialog, QDialogButtonBox, QSizePolicy, QCheckBox
)
from PyQt6.QtCore import Qt, QDate, QSize, pyqtSignal, QMutex
from PyQt6.QtGui import QIcon, QPixmap
from app.core.db import get_all_guests, get_all_rooms, update_room, get_guest_id_by_name, insert_checkin, get_all_checkins, update_checkin, get_booking_services, get_total_booking_charges, get_room_rates, get_tax_rates # Import get_tax_rates
from app.ui.dialogs.add_extra_charge import AddExtraChargeDialog
import uuid
from datetime import datetime
import os
import sys
from fpdf import FPDF
import logging
from decimal import Decimal, InvalidOperation
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
# TAX_RATE = Decimal('0.10') # This constant is no longer directly used for calculation
ROOM_GRID_COLS = 5
MIN_NIGHTS = 1
MAX_NIGHTS = 60
MIN_GUESTS = 1
MAX_GUESTS = 10
RECEIPTS_DIR = os.path.join(os.getcwd(), "receipts")
PDF_ENCODING = 'utf-8'

class DatabaseError(Exception):
    """Custom exception for database operations"""
    pass

class ValidationError(Exception):
    """Custom exception for validation errors"""
    pass

class CheckInWidget(QWidget):
    """Widget for managing check-ins"""
    
    # Signal for guest deletion
    guest_deleted = pyqtSignal()
    # Signal for room status changes (added for consistency with other modules)
    room_status_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transaction_id = str(uuid.uuid4())[:8]  # Initialize transaction ID
        self.checkin_id = str(uuid.uuid4())[:8]  # Initialize check-in ID
        self.checkin_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.selected_room_id = None  # Ensure this is always initialized
        self.current_checkout = None  # Added for checkout functionality
        self.room_mutex = QMutex()  # Mutex for thread-safe room selection
        self.payment_mutex = QMutex()  # Mutex for thread-safe payment processing
        
        # Initialize guests_data to prevent reference errors
        self.guests_data = []
        
        self.setup_ui()
        
        # Initialize guests data after UI setup
        try:
            self.guests_data = self.safe_db_operation(get_all_guests)
        except Exception as e:
            logger.error(f"Failed to initialize guests data: {str(e)}")
            self.guests_data = []
        
        # Connect to the guest deletion signal from the main window
        if parent and hasattr(parent, 'guest_deleted'):
            parent.guest_deleted.connect(self.refresh_guest_lists)
        
        # Connect to room status changes from main window (if available)
        if parent and hasattr(parent, 'room_status_changed'):
            parent.room_status_changed.connect(self.load_room_grid) # Refresh room grid on status change

        # Load check-in list initially (for when the tab is first shown)
        self.load_checkin_list()


    def safe_db_operation(self, operation, *args, **kwargs):
        """Safely execute database operations with error handling"""
        try:
            return operation(*args, **kwargs)
        except Exception as e:
            logger.error(f"Database operation failed: {str(e)}")
            logger.error(traceback.format_exc())
            raise DatabaseError(f"Database operation failed: {str(e)}")

    def validate_numeric_input(self, value, field_name, min_value=None, max_value=None):
        """Validate numeric input with optional min/max constraints"""
        try:
            num_value = Decimal(str(value))
            if min_value is not None and num_value < min_value:
                raise ValidationError(f"{field_name} must be at least {min_value}")
            if max_value is not None and num_value > max_value:
                raise ValidationError(f"{field_name} must be at most {max_value}")
            return num_value
        except (ValueError, InvalidOperation):
            raise ValidationError(f"{field_name} must be a valid number")

    def validate_dates(self, arrival_date, departure_date):
        """Validate date range"""
        if not isinstance(arrival_date, QDate) or not isinstance(departure_date, QDate):
            raise ValidationError("Invalid date format")
        
        if arrival_date > departure_date:
            raise ValidationError("Departure date must be after arrival date")
        
        nights = arrival_date.daysTo(departure_date)
        if nights < MIN_NIGHTS:
            raise ValidationError(f"Minimum stay is {MIN_NIGHTS} night(s)")
        if nights > MAX_NIGHTS:
            raise ValidationError(f"Maximum stay is {MAX_NIGHTS} nights")
        
        return nights

    def validate_payment_input(self, text):
        """Validate payment input to ensure it's a valid number"""
        if not text:
            return True
        
        # Allow only digits and a single decimal point
        if text.count('.') <= 1 and all(c.isdigit() or c == '.' for c in text):
            try:
                float(text)
                return True
            except ValueError:
                return False
        return False
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Check-ins")
        title_label.setObjectName("pageTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        # Connect tab change signal to update relevant lists
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        
        # Check-in list tab
        self.checkin_list_tab = QWidget()
        self.setup_checkin_list_tab()
        checkin_list_icon = QIcon(":/icons/checkins-list.png")
        checkin_list_icon.addPixmap(checkin_list_icon.pixmap(QSize(48, 48)))
        self.tab_widget.addTab(self.checkin_list_tab, checkin_list_icon, "Check-ins")
        
        # New check-in tab
        self.new_checkin_tab = QWidget()
        self.setup_new_checkin_tab()
        new_checkin_icon = QIcon(":/icons/add_checkin.png")
        new_checkin_icon.addPixmap(new_checkin_icon.pixmap(QSize(48, 48)))
        self.tab_widget.addTab(self.new_checkin_tab, new_checkin_icon, "New Check-in")
        
        # Check-out tab
        self.checkout_tab = QWidget()
        self.setup_checkout_tab()
        checkout_icon = QIcon(":/icons/departures.png")
        checkout_icon.addPixmap(checkout_icon.pixmap(QSize(48, 48)))
        self.tab_widget.addTab(self.checkout_tab, checkout_icon, "Check-out")
        
        layout.addWidget(self.tab_widget)

    def on_tab_changed(self, index):
        """Handle tab changes to refresh relevant data."""
        tab_name = self.tab_widget.tabText(index)
        if tab_name == "Check-ins":
            self.load_checkin_list()
        elif tab_name == "New Check-in":
            self.transaction_id = str(uuid.uuid4())[:8]  # reset each time
            self.checkin_id = str(uuid.uuid4())[:8]
            self.selected_room_id = None
            self.reload_guests_for_search()
            self.load_room_grid()
        elif tab_name == "Check-out":
            self.load_checked_in_guests()
            self.populate_tax_options() # Populate tax options when entering checkout tab


    def setup_checkin_list_tab(self):
        layout = QVBoxLayout(self.checkin_list_tab)
        layout.setContentsMargins(20, 20, 20, 20)  # Add consistent margins
        layout.setSpacing(20)  # Add consistent spacing
        
        # Search and filter bar
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 0)  # Add consistent margins
        filter_layout.setSpacing(10)  # Add consistent spacing
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by guest, check-in #, date...")
        self.search_input.textChanged.connect(self.filter_checkin_list)
        filter_layout.addWidget(self.search_input)
        
        self.filter_arrival = QDateEdit()
        self.filter_arrival.setCalendarPopup(True)
        self.filter_arrival.setDisplayFormat("yyyy-MM-dd")
        self.filter_arrival.dateChanged.connect(self.filter_checkin_list)
        filter_layout.addWidget(self.filter_arrival)
        
        self.filter_departure = QDateEdit()
        self.filter_departure.setCalendarPopup(True)
        self.filter_departure.setDisplayFormat("yyyy-MM-dd")
        self.filter_departure.dateChanged.connect(self.filter_checkin_list)
        filter_layout.addWidget(self.filter_departure)
        
        self.filter_room_type = QComboBox()
        self.filter_room_type.addItems(["All Room Types", "Single", "Double", "Suite", "Deluxe"])
        self.filter_room_type.currentTextChanged.connect(self.filter_checkin_list)
        filter_layout.addWidget(self.filter_room_type)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("actionButton")
        refresh_btn.clicked.connect(self.load_checkin_list)
        filter_layout.addWidget(refresh_btn)
        
        layout.addWidget(filter_frame)
        
        # Check-in table
        self.checkin_table = QTableWidget()
        self.checkin_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.checkin_table.setColumnCount(7)
        self.checkin_table.setHorizontalHeaderLabels([
            "Check-In #", "Guest Name", "Arrival", "Departure", "Room", "Status", "Actions"
        ])
        self.checkin_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.checkin_table.setAlternatingRowColors(True)
        self.checkin_table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(self.checkin_table)

    def populate_guest_combo(self):
        self.guest_select_combo.clear()
        guests = get_all_guests()
        self.guest_select_combo.addItem("--Select guest--", None)
        for g in guests:
            name = f"{g['first_name']} {g['last_name']}"
            self.guest_select_combo.addItem(name, g)

    def setup_new_checkin_tab(self):
        layout = QVBoxLayout(self.new_checkin_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Progress indicator
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QHBoxLayout(progress_frame)
        
        steps = ["Guest Details", "Stay Details", "Room Selection", "Payment"]
        self.progress_labels = []
        
        for i, step in enumerate(steps):
            step_widget = QWidget()
            step_layout = QVBoxLayout(step_widget)
            
            # Step number circle
            number_label = QLabel(str(i + 1))
            number_label.setObjectName("stepNumber")
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Step name
            name_label = QLabel(step)
            name_label.setObjectName("stepName")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            step_layout.addWidget(number_label)
            step_layout.addWidget(name_label)
            progress_layout.addWidget(step_widget)
            
            self.progress_labels.append((number_label, name_label))
            
            if i < len(steps) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setObjectName("progressLine")
                progress_layout.addWidget(line)
        
        layout.addWidget(progress_frame)

        # Wizard steps
        self.wizard = QStackedWidget()
        layout.addWidget(self.wizard)

        # Step 1: Guest Selection/Input
        step1 = QWidget()
        s1_layout = QVBoxLayout(step1)
        s1_layout.setContentsMargins(40, 20, 40, 20)
        search_label = QLabel("Select Guest")
        search_label.setObjectName("sectionTitle")
        s1_layout.addWidget(search_label)
        
        # Create a container for the search and dropdown
        search_container = QWidget()
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(0, 0, 0, 0)
        search_container_layout.setSpacing(10)  # Add some spacing between the widgets
        
        # Guest select combo
        self.guest_select_combo = QComboBox()
        self.guest_select_combo.setEditable(True)  # Make combo box editable
        self.guest_select_combo.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)  # Prevent adding new items
        self.guest_select_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.guest_select_combo.currentIndexChanged.connect(self.on_guest_selected)
        self.guest_select_combo.setPlaceholderText("Search and select guest...")  # Add placeholder text
        search_container_layout.addWidget(self.guest_select_combo)
        
        # Create completer for guest search
        self.guest_completer = QCompleter()
        self.guest_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.guest_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.guest_select_combo.setCompleter(self.guest_completer)
        
        s1_layout.addWidget(search_container)
        
        # Guest details form (read-only labels)
        self.guest_first_name_label = QLabel()
        self.guest_last_name_label = QLabel()
        self.guest_id_number_label = QLabel()
        self.guest_nationality_label = QLabel()

        # Create horizontal layouts for each label pair
        first_name_layout = QHBoxLayout()
        first_name_layout.addWidget(QLabel("First Name:"))
        first_name_layout.addWidget(self.guest_first_name_label)
        first_name_layout.addStretch()

        last_name_layout = QHBoxLayout()
        last_name_layout.addWidget(QLabel("Last Name:"))
        last_name_layout.addWidget(self.guest_last_name_label)
        last_name_layout.addStretch()

        id_number_layout = QHBoxLayout()
        id_number_layout.addWidget(QLabel("ID Number:"))
        id_number_layout.addWidget(self.guest_id_number_label)
        id_number_layout.addStretch()

        nationality_layout = QHBoxLayout()
        nationality_layout.addWidget(QLabel("Nationality:"))
        nationality_layout.addWidget(self.guest_nationality_label)
        nationality_layout.addStretch()

        # Add the horizontal layouts to the main layout
        s1_layout.addLayout(first_name_layout)
        s1_layout.addLayout(last_name_layout)
        s1_layout.addLayout(id_number_layout)
        s1_layout.addLayout(nationality_layout)
        
        self.wizard.addWidget(step1)

        # Step 2: Stay Details
        step2 = QWidget()
        s2_layout = QVBoxLayout(step2)
        s2_layout.setContentsMargins(40, 0, 40, 20)
        
        # Date selection with split calendar
        date_frame = QFrame()
        date_frame.setObjectName("dateFrame")
        date_layout = QHBoxLayout(date_frame)
        date_layout.setSpacing(40)
        
        # Arrival date
        arrival_widget = QWidget()
        arrival_layout = QVBoxLayout(arrival_widget)
        arrival_layout.setSpacing(5)
        arrival_label = QLabel("Arrival Date")
        arrival_label.setObjectName("sectionTitle")
        arrival_layout.addWidget(arrival_label)
        
        self.arrival_date = QCalendarWidget()
        # self.arrival_date.setMinimumDate(QDate.currentDate())
        # Removed minimum date restriction to allow past dates
        self.arrival_date.setMinimumWidth(350)
        self.arrival_date.setMinimumHeight(250)
        self.arrival_date.clicked.connect(self.update_payment_amount)
        arrival_layout.addWidget(self.arrival_date)
        
        # Departure date
        departure_widget = QWidget()
        departure_layout = QVBoxLayout(departure_widget)
        departure_layout.setSpacing(5)
        departure_label = QLabel("Departure Date")
        departure_label.setObjectName("sectionTitle")
        departure_layout.addWidget(departure_label)
        
        self.departure_date = QCalendarWidget()
        self.departure_date.setMinimumDate(QDate.currentDate().addDays(1))
        self.departure_date.setMinimumWidth(350)
        self.departure_date.setMinimumHeight(250)
        self.departure_date.clicked.connect(self.update_payment_amount)
        departure_layout.addWidget(self.departure_date)
        
        date_layout.addWidget(arrival_widget, 1)
        date_layout.addWidget(departure_widget, 1)
        s2_layout.addWidget(date_frame)
        
        # Add a stretch here to push content to the top
        s2_layout.addStretch() # <--- ADD THIS LINE HERE

        # Number of guests with stepper
        guests_frame = QFrame()
        guests_frame.setObjectName("guestsFrame")
        guests_layout = QHBoxLayout(guests_frame)
        
        guests_label = QLabel("Number of Guests")
        guests_label.setObjectName("sectionTitle")
        guests_layout.addWidget(guests_label)
        
        self.num_guests = QSpinBox()
        self.num_guests.setMinimum(1)
        self.num_guests.setMaximum(10)
        self.num_guests.setValue(1)
        self.num_guests.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.num_guests.setMinimumWidth(120)
        guests_layout.addWidget(self.num_guests)
        guests_layout.addStretch()
        
        s2_layout.addWidget(guests_frame)
        self.wizard.addWidget(step2)

        # Step 3: Room Selection
        step3 = QWidget()
        s3_layout = QVBoxLayout(step3)
        s3_layout.setContentsMargins(40, 20, 40, 20)
        
        # Room grid with improved styling
        rooms_frame = QFrame()
        rooms_frame.setObjectName("roomsFrame")
        rooms_layout = QVBoxLayout(rooms_frame)
        
        rooms_label = QLabel("Select Room")
        rooms_label.setObjectName("sectionTitle")
        rooms_layout.addWidget(rooms_label)
        
        self.room_grid_widget = QWidget()
        self.room_grid_layout = QGridLayout(self.room_grid_widget)
        self.room_grid_layout.setSpacing(10)
        rooms_layout.addWidget(self.room_grid_widget)
        
        # Legend with improved styling
        legend_frame = QFrame()
        legend_frame.setObjectName("legendFrame")
        legend_layout = QHBoxLayout(legend_frame)
        
        status_colors = {
            "Available": "#27ae60",   # Green
            "Vacant": "#27ae60",  # Added Vacant status with green color
            "Reserved": "#8e44ad",    # Purple
            "Occupied": "#c0392b",    # Red
            "Not Available": "#95a5a6", # Gray
            "Needs Cleaning": "#f1c40f" # Yellow
        }
        
        for status, color in status_colors.items():
            legend_item = QWidget()
            legend_item_layout = QHBoxLayout(legend_item)
            legend_item_layout.setSpacing(5)
            color_box = QLabel()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            status_label = QLabel(status)
            status_label.setStyleSheet("color: #2c3e50;")
            legend_item_layout.addWidget(color_box)
            legend_item_layout.addWidget(status_label)
            legend_layout.addWidget(legend_item)
        
        rooms_layout.addWidget(legend_frame)
        s3_layout.addWidget(rooms_frame)
        self.wizard.addWidget(step3)

        # Step 4: Payment (Final step)
        step4 = QWidget()
        s4_layout = QVBoxLayout(step4)
        s4_layout.setContentsMargins(40, 20, 40, 20)
        
        payment_frame = QFrame()
        payment_frame.setObjectName("paymentFrame")
        payment_layout = QVBoxLayout(payment_frame)
        
        payment_label = QLabel("Payment Details")
        payment_label.setObjectName("sectionTitle")
        payment_layout.addWidget(payment_label)
        
        # Payment method with modern dropdown
        method_widget = QWidget()
        method_layout = QHBoxLayout(method_widget)
        method_label = QLabel("Payment Method:")
        self.payment_method = QComboBox()
        self.payment_method.addItems(["Cash", "Credit Card", "Debit Card", "Mobile Payment"])
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.payment_method)
        payment_layout.addWidget(method_widget)
        
        # Amount details
        amounts_widget = QWidget()
        amounts_layout = QFormLayout(amounts_widget)
        amounts_layout.setSpacing(15)
        
        self.payment_amount = QLineEdit()
        self.payment_amount.setReadOnly(True)
        self.payment_amount.setText("0.00")
        self.payment_amount.setObjectName("readOnlyInput")
        
        self.total_paid = QLineEdit()
        self.total_paid.setPlaceholderText("Enter amount paid")
        self.total_paid.textChanged.connect(self.update_amount_due)
        
        self.amount_due = QLineEdit()
        self.amount_due.setReadOnly(True)
        self.amount_due.setText("0.00")
        self.amount_due.setObjectName("readOnlyInput")
        
        amounts_layout.addRow("Amount Due:", self.payment_amount)
        amounts_layout.addRow("Total Paid:", self.total_paid)
        amounts_layout.addRow("Amount Remaining:", self.amount_due)
        
        payment_layout.addWidget(amounts_widget)
        
        # Payment status with progress indicator
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        
        self.payment_status_label = QLabel("Pending")
        self.payment_status_label.setObjectName("paymentStatus")
        status_layout.addWidget(self.payment_status_label)
        
        self.payment_progress = QProgressBar()
        self.payment_progress.setObjectName("paymentProgress")
        self.payment_progress.setRange(0, 100)
        self.payment_progress.setValue(0)
        status_layout.addWidget(self.payment_progress)
        
        payment_layout.addWidget(status_widget)
        
        s4_layout.addWidget(payment_frame)
        self.wizard.addWidget(step4)

        # Navigation buttons
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_layout = QHBoxLayout(nav_frame)
        
        self.back_btn = QPushButton("Back")
        self.next_btn = QPushButton("Next")
        self.cancel_btn = QPushButton("Cancel")
        self.finish_btn = QPushButton("Finish")
        
        self.back_btn.setObjectName("navButton")
        self.next_btn.setObjectName("navButton")
        self.cancel_btn.setObjectName("navButton")
        self.finish_btn.setObjectName("navButton")
        
        nav_layout.addWidget(self.cancel_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.finish_btn)
        
        layout.addWidget(nav_frame)

        # Connect signals
        self.back_btn.clicked.connect(self.prev_step)
        self.next_btn.clicked.connect(self.next_step)
        self.cancel_btn.clicked.connect(self.cancel_wizard)
        self.finish_btn.clicked.connect(self.finish_wizard)
        self.total_paid.textChanged.connect(self.update_amount_due)
        self.total_paid.textChanged.connect(self.update_payment_status)
        self.payment_amount.textChanged.connect(self.update_payment_status)
        
        self.update_wizard_ui()

    def setup_checkout_tab(self):
        layout = QVBoxLayout(self.checkout_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(0)

        # Progress indicator
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QHBoxLayout(progress_frame)
        
        steps = ["Select Guest", "Review & Charges", "Payment", "Confirmation"]
        self.checkout_progress_labels = []
        
        for i, step in enumerate(steps):
            step_widget = QWidget()
            step_layout = QVBoxLayout(step_widget)
            
            # Step number circle
            number_label = QLabel(str(i + 1))
            number_label.setObjectName("stepNumber")
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            # Step name
            name_label = QLabel(step)
            name_label.setObjectName("stepName")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            step_layout.addWidget(number_label)
            step_layout.addWidget(name_label)
            progress_layout.addWidget(step_widget)
            
            self.checkout_progress_labels.append((number_label, name_label))
            
            if i < len(steps) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setObjectName("progressLine")
                progress_layout.addWidget(line)
        
        layout.addWidget(progress_frame)

        # Wizard steps
        self.checkout_wizard = QStackedWidget()
        layout.addWidget(self.checkout_wizard)

        # Step 1: Guest Selection
        step1 = QWidget()
        s1_layout = QVBoxLayout(step1)
        s1_layout.setContentsMargins(40, 20, 40, 20)
        
        # Search frame
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QVBoxLayout(search_frame)
        
        search_label = QLabel("Select Guest to Check Out")
        search_label.setObjectName("sectionTitle")
        search_layout.addWidget(search_label)
        
        # Search container
        search_container = QWidget()
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        self.checkout_search = QLineEdit()
        self.checkout_search.setPlaceholderText("Search by room number, guest name, or check-in ID...")
        self.checkout_search.textChanged.connect(self.filter_checkout_guests)
        search_container_layout.addWidget(self.checkout_search)
        
        search_layout.addWidget(search_container)
        s1_layout.addWidget(search_frame)
        
        # Checked-in guests table
        self.checkout_table = QTableWidget()
        self.checkout_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.checkout_table.setColumnCount(6)
        self.checkout_table.setHorizontalHeaderLabels([
            "Check-in ID", "Guest Name", "Room", "Arrival", "Departure", "Actions"
        ])
        self.checkout_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.checkout_table.setObjectName("dataTable")
        self.checkout_table.setAlternatingRowColors(True)
        self.checkout_table.verticalHeader().setDefaultSectionSize(50)  # Make rows thick
        s1_layout.addWidget(self.checkout_table)
        
        self.checkout_wizard.addWidget(step1)

        # Step 2: Review & Charges
        step2 = QWidget()
        s2_layout = QVBoxLayout(step2)
        s2_layout.setContentsMargins(40, 20, 40, 20)
        
        # Stay details frame
        stay_frame = QFrame()
        stay_frame.setObjectName("detailsFrame")
        stay_layout = QVBoxLayout(stay_frame)
        
        stay_label = QLabel("Stay Details")
        stay_label.setObjectName("sectionTitle")
        stay_layout.addWidget(stay_label)
        
        # Stay details form
        stay_form = QFormLayout()
        self.checkout_guest_name = QLabel()
        self.checkout_room = QLabel()
        self.checkout_arrival = QLabel()
        self.checkout_departure = QLabel()
        self.checkout_actual_departure = QDateEdit()
        self.checkout_actual_departure.setCalendarPopup(True)
        self.checkout_actual_departure.setDate(QDate.currentDate())
        
        stay_form.addRow("Guest:", self.checkout_guest_name)
        stay_form.addRow("Room:", self.checkout_room)
        stay_form.addRow("Arrival:", self.checkout_arrival)
        stay_form.addRow("Scheduled Departure:", self.checkout_departure)
        stay_form.addRow("Actual Departure:", self.checkout_actual_departure)
        
        stay_layout.addLayout(stay_form)
        s2_layout.addWidget(stay_frame)
        
        # Additional charges frame
        charges_frame = QFrame()
        charges_frame.setObjectName("chargesFrame")
        charges_layout = QVBoxLayout(charges_frame)
        
        charges_label = QLabel("Additional Charges")
        charges_label.setObjectName("sectionTitle")
        charges_layout.addWidget(charges_label)
        
        # Charges table
        self.charges_table = QTableWidget()
        self.charges_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.charges_table.setAlternatingRowColors(True)
        self.charges_table.setColumnCount(4)
        self.charges_table.setHorizontalHeaderLabels([
            "Service", "Quantity", "Unit Price", "Total"
        ])
        self.charges_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.charges_table.setObjectName("dataTable")
        charges_layout.addWidget(self.charges_table)
        
        s2_layout.addWidget(charges_frame)
        self.checkout_wizard.addWidget(step2)

        # Step 3: Payment
        step3 = QWidget()
        s3_layout = QVBoxLayout(step3)
        s3_layout.setContentsMargins(40, 20, 40, 20)
        
        payment_frame = QFrame()
        payment_frame.setObjectName("paymentFrame")
        payment_layout = QVBoxLayout(payment_frame)
        
        payment_label = QLabel("Final Payment")
        payment_label.setObjectName("sectionTitle")
        payment_layout.addWidget(payment_label)
        
        # Payment method with modern dropdown
        method_widget = QWidget()
        method_layout = QHBoxLayout(method_widget)
        method_label = QLabel("Payment Method:")
        self.checkout_payment_method = QComboBox()
        self.checkout_payment_method.addItems(["Cash", "Credit Card", "Debit Card", "Mobile Payment"])
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.checkout_payment_method)
        payment_layout.addWidget(method_widget)
        
        # Tax selection
        tax_select_widget = QWidget()
        tax_select_layout = QHBoxLayout(tax_select_widget)
        tax_select_layout.setContentsMargins(0, 0, 0, 0)
        tax_select_layout.addWidget(QLabel("Select Tax:"))
        self.checkout_tax_select = QComboBox()
        self.populate_tax_options() # Populate tax options
        self.checkout_tax_select.currentIndexChanged.connect(self.update_checkout_total)
        tax_select_layout.addWidget(self.checkout_tax_select)
        tax_select_layout.addStretch()
        payment_layout.addWidget(tax_select_widget)

        self.selected_tax_display = QLabel("No tax selected")
        self.selected_tax_display.setStyleSheet("font-style: italic; color: #555;")
        payment_layout.addWidget(self.selected_tax_display)

        # Amount details
        amounts_widget = QWidget()
        amounts_layout = QFormLayout(amounts_widget)
        amounts_layout.setSpacing(15)
        
        self.checkout_room_charges = QLineEdit()
        self.checkout_room_charges.setReadOnly(True)
        self.checkout_room_charges.setObjectName("readOnlyInput")
        
        self.checkout_additional_charges = QLineEdit()
        self.checkout_additional_charges.setReadOnly(True)
        self.checkout_additional_charges.setObjectName("readOnlyInput")
        
        # Tax amount display (no longer a checkbox)
        self.checkout_tax_amount_display = QLineEdit() # Renamed from checkout_tax_amount
        self.checkout_tax_amount_display.setReadOnly(True)
        self.checkout_tax_amount_display.setObjectName("readOnlyInput")
        self.checkout_tax_amount_display.setText("0.00")
        
        self.checkout_total_amount = QLineEdit()
        self.checkout_total_amount.setReadOnly(True)
        self.checkout_total_amount.setObjectName("readOnlyInput")
        
        self.checkout_amount_paid = QLineEdit()
        self.checkout_amount_paid.setPlaceholderText("Enter amount paid")
        self.checkout_amount_paid.setObjectName("amountInput")
        
        self.checkout_amount_due = QLineEdit()
        self.checkout_amount_due.setReadOnly(True)
        self.checkout_amount_due.setObjectName("readOnlyInput")
        
        amounts_layout.addRow("Room Charges:", self.checkout_room_charges)
        amounts_layout.addRow("Additional Charges:", self.checkout_additional_charges)
        amounts_layout.addRow("Tax Amount:", self.checkout_tax_amount_display) # Updated label
        amounts_layout.addRow("Total Amount:", self.checkout_total_amount)
        amounts_layout.addRow("Amount Paid:", self.checkout_amount_paid)
        amounts_layout.addRow("Amount Due:", self.checkout_amount_due)
        
        payment_layout.addWidget(amounts_widget)
        
        # Payment status with progress indicator
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        
        self.payment_status_label = QLabel("Pending")
        self.payment_status_label.setObjectName("paymentStatus")
        status_layout.addWidget(self.payment_status_label)
        
        self.payment_progress = QProgressBar()
        self.payment_progress.setObjectName("paymentProgress")
        self.payment_progress.setRange(0, 100)
        self.payment_progress.setValue(0)
        status_layout.addWidget(self.payment_progress)
        
        payment_layout.addWidget(status_widget)
        
        s3_layout.addWidget(payment_frame)
        self.checkout_wizard.addWidget(step3)

        # Step 4: Confirmation
        step4 = QWidget()
        s4_layout = QVBoxLayout(step4)
        s4_layout.setContentsMargins(40, 20, 40, 20)
        
        confirmation_frame = QFrame()
        confirmation_frame.setObjectName("confirmationFrame")
        confirmation_layout = QVBoxLayout(confirmation_frame)
        
        # Success message
        success_label = QLabel("Check-out Confirmed!")
        success_label.setObjectName("successTitle")
        success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confirmation_layout.addWidget(success_label)
        
        # Confirmation details
        self.checkout_confirmation_label = QLabel()
        self.checkout_confirmation_label.setObjectName("confirmationDetails")
        self.checkout_confirmation_label.setWordWrap(True)
        confirmation_layout.addWidget(self.checkout_confirmation_label)
        
        # Action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        
        self.checkout_print_receipt_btn = QPushButton("Print Receipt")
        self.checkout_print_receipt_btn.setObjectName("actionButton")
        self.checkout_print_receipt_btn.clicked.connect(self.print_receipt)
        
        actions_layout.addWidget(self.checkout_print_receipt_btn)
        
        confirmation_layout.addWidget(actions_widget)
        
        s4_layout.addWidget(confirmation_frame)
        self.checkout_wizard.addWidget(step4)

        # Navigation buttons
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_layout = QHBoxLayout(nav_frame)
        
        self.checkout_back_btn = QPushButton("Back")
        self.checkout_next_btn = QPushButton("Next")
        self.checkout_cancel_btn = QPushButton("Cancel")
        self.checkout_finish_btn = QPushButton("Finish")
        
        # Set proper object names for styling
        self.checkout_back_btn.setObjectName("navButton")
        self.checkout_next_btn.setObjectName("navButton")
        self.checkout_cancel_btn.setObjectName("navButton")
        self.checkout_finish_btn.setObjectName("navButton")
        
        # Set fixed widths for consistent button sizes
        button_width = 100
        self.checkout_back_btn.setFixedWidth(button_width)
        self.checkout_next_btn.setFixedWidth(button_width)
        self.checkout_cancel_btn.setFixedWidth(button_width)
        self.checkout_finish_btn.setFixedWidth(button_width)
        
        nav_layout.addWidget(self.checkout_cancel_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.checkout_back_btn)
        nav_layout.addWidget(self.checkout_next_btn)
        nav_layout.addWidget(self.checkout_finish_btn)
        
        layout.addWidget(nav_frame)

        # Connect signals
        self.checkout_back_btn.clicked.connect(self.checkout_prev_step)
        self.checkout_next_btn.clicked.connect(self.checkout_next_step)
        self.checkout_cancel_btn.clicked.connect(self.checkout_cancel_wizard)
        self.checkout_finish_btn.clicked.connect(self.checkout_finish_wizard)
        self.checkout_amount_paid.textChanged.connect(self.update_checkout_amount_due)
        
        self.load_checked_in_guests()

    def populate_tax_options(self):
        """Populate the tax selection combobox with available tax rates."""
        self.checkout_tax_select.clear()
        self.checkout_tax_select.addItem("No Tax", None) # Option to select no tax

        tax_rates = self.safe_db_operation(get_tax_rates)
        for tax in tax_rates:
            display_text = tax['name']
            if tax['tax_type'] == 'percentage':
                display_text += f" ({tax['percentage']:.0f}%)"
            elif tax['tax_type'] == 'fixed':
                display_text += f" (MAD {tax['amount']:.2f} Fixed)"
            self.checkout_tax_select.addItem(display_text, tax)
        
        # Only update total if UI elements exist
        if hasattr(self, 'checkout_room_charges') and hasattr(self, 'checkout_total_amount'):
            self.update_checkout_total()

    def load_checked_in_guests(self):
        """Load currently checked-in guests"""
        self.checkout_table.setRowCount(0)
        checkins = get_all_checkins()
        
        for checkin in checkins:
            if checkin['status'] != 'checked_out':
                row = self.checkout_table.rowCount()
                self.checkout_table.insertRow(row)
                
                self.checkout_table.setItem(row, 0, QTableWidgetItem(checkin['checkin_id']))
                self.checkout_table.setItem(row, 1, QTableWidgetItem(f"{checkin['first_name']} {checkin['last_name']}"))
                self.checkout_table.setItem(row, 2, QTableWidgetItem(f"{checkin['room_type']} #{checkin['room_number']}"))
                self.checkout_table.setItem(row, 3, QTableWidgetItem(checkin['arrival_date']))
                self.checkout_table.setItem(row, 4, QTableWidgetItem(checkin['departure_date']))
                
                # Add action button
                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                actions_layout.setSpacing(5)
                actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the buttons
                
                checkout_btn = QPushButton("Check Out")
                checkout_btn.setObjectName("tableActionButton")
                checkout_btn.setProperty("action", "checkout")
                checkout_btn.setFixedWidth(100)
                checkout_btn.clicked.connect(lambda _, c=checkin: self.start_checkout(c))
                
                actions_layout.addWidget(checkout_btn)
                self.checkout_table.setCellWidget(row, 5, actions_widget)

    def filter_checkout_guests(self):
        """Filter checked-in guests based on search text"""
        search_text = self.checkout_search.text().lower()
        for row in range(self.checkout_table.rowCount()):
            show_row = False
            for col in range(self.checkout_table.columnCount() - 1):  # Exclude actions column
                item = self.checkout_table.item(row, col)
                if item and search_text in item.text().lower():
                    show_row = True
                    break
            self.checkout_table.setRowHidden(row, not show_row)

    def start_checkout(self, checkin):
        """Start checkout process for selected guest"""
        self.current_checkout = checkin
        self.checkout_guest_name.setText(f"{checkin['first_name']} {checkin['last_name']}")
        self.checkout_room.setText(f"{checkin['room_type']} #{checkin['room_number']}")
        self.checkout_arrival.setText(checkin['arrival_date'])
        self.checkout_departure.setText(checkin['departure_date'])
        self.checkout_actual_departure.setDate(QDate.currentDate())
        
        # Calculate number of nights
        arrival = QDate.fromString(checkin['arrival_date'], 'yyyy-MM-dd')
        departure = QDate.fromString(checkin['departure_date'], 'yyyy-MM-dd')
        nights = arrival.daysTo(departure)
        if nights <= 0:
            QMessageBox.warning(self, "Error", "Departure date must be after arrival date to calculate nights and rates.")
            return

        # Get room rate from database based on room type
        rates = get_room_rates()
        room_rate_value = next((r['night_rate'] for r in rates if r['room_type'] == checkin['room_type']), None)
        if room_rate_value is None:
            QMessageBox.warning(self, "Error", "Room rate not found for this room type.")
            return
        room_rate = Decimal(str(room_rate_value)) # Convert to Decimal

        room_charges = Decimal(nights) * room_rate # Ensure nights is also Decimal or converted to Decimal for multiplication
        self.checkout_room_charges.setText(f"MAD {room_charges:.2f}")
        
        # Load extra charges
        self.charges_table.setRowCount(0)
        extra_charges = get_booking_services(checkin['id'])
        total_extra_charges = Decimal('0') # Initialize as Decimal
        for charge in extra_charges:
            row = self.charges_table.rowCount()
            self.charges_table.insertRow(row)
            self.charges_table.setItem(row, 0, QTableWidgetItem(charge['service_name']))
            self.charges_table.setItem(row, 1, QTableWidgetItem(str(charge['quantity'])))
            self.charges_table.setItem(row, 2, QTableWidgetItem(f"MAD {Decimal(str(charge['unit_price_at_time_of_charge'])):.2f}"))
            self.charges_table.setItem(row, 3, QTableWidgetItem(f"MAD {Decimal(str(charge['total_charge'])):.2f}"))
            total_extra_charges += Decimal(str(charge['total_charge'])) # Add as Decimal
        
        self.checkout_additional_charges.setText(f"MAD {total_extra_charges:.2f}")
        self.update_checkout_total()
        
        # Move to step 2
        self.checkout_wizard.setCurrentIndex(1)
        self.update_checkout_wizard_ui()

    def update_checkout_total(self):
        """Update the total amount including tax based on selected tax rate."""
        try:
            # Check if required UI elements exist
            if not all(hasattr(self, attr) for attr in ['checkout_room_charges', 'checkout_additional_charges', 
                                                       'checkout_tax_amount_display', 'checkout_total_amount']):
                return

            # Get base amounts as Decimal
            room_charges = Decimal(self.checkout_room_charges.text().replace('MAD ', '').strip() or '0')
            additional_charges = Decimal(self.checkout_additional_charges.text().replace('MAD ', '').strip() or '0')
            
            # Get selected tax data
            selected_tax = self.checkout_tax_select.currentData()
            
            tax_amount = Decimal('0')
            taxable_base = Decimal('0')

            if selected_tax:
                # Determine taxable base
                if selected_tax.get('apply_to_rooms', False):
                    taxable_base += room_charges
                if selected_tax.get('apply_to_services', False):
                    taxable_base += additional_charges

                if selected_tax['tax_type'] == 'percentage':
                    percentage = Decimal(str(selected_tax.get('percentage', 0))) / Decimal('100')
                    tax_amount = taxable_base * percentage
                elif selected_tax['tax_type'] == 'fixed':
                    tax_amount = Decimal(str(selected_tax.get('amount', 0)))
            
            # Update tax display
            self.checkout_tax_amount_display.setText(f"{tax_amount:.2f}")
            self.selected_tax_display.setText(selected_tax['name'] if selected_tax else "No tax selected")

            # Calculate subtotal and total
            subtotal = room_charges + additional_charges
            total = subtotal + tax_amount
            
            self.checkout_total_amount.setText(f"MAD {total:.2f}")
            
            # Update amount due
            self.update_checkout_amount_due()
            
        except Exception as e:
            logger.error(f"Error updating checkout total: {str(e)}")
            logger.error(traceback.format_exc())
            if hasattr(self, 'checkout_total_amount'):
                self.checkout_total_amount.setText("0.00")
            if hasattr(self, 'checkout_tax_amount_display'):
                self.checkout_tax_amount_display.setText("0.00")
            if hasattr(self, 'selected_tax_display'):
                self.selected_tax_display.setText("Error in tax calculation")

    def update_checkout_amount_due(self):
        """Update amount due based on total and amount paid"""
        try:
            total = Decimal(self.checkout_total_amount.text().replace('MAD ', '').strip() or '0')
            paid = Decimal(self.checkout_amount_paid.text().strip() or '0')
            due = max(total - paid, Decimal('0'))
            self.checkout_amount_due.setText(f"MAD {due:.2f}")
        except Exception:
            self.checkout_amount_due.setText(self.checkout_total_amount.text())

    def checkout_prev_step(self):
        """Go to previous step in checkout wizard"""
        if self.checkout_wizard.currentIndex() > 0:
            self.checkout_wizard.setCurrentIndex(self.checkout_wizard.currentIndex() - 1)
            self.update_checkout_wizard_ui()

    def checkout_next_step(self):
        """Go to next step in checkout wizard"""
        if self.checkout_wizard.currentIndex() < self.checkout_wizard.count() - 1:
            self.checkout_wizard.setCurrentIndex(self.checkout_wizard.currentIndex() + 1)
            if self.checkout_wizard.currentIndex() == 3:  # Confirmation step
                self.show_checkout_confirmation()
            self.update_checkout_wizard_ui()

    def checkout_cancel_wizard(self):
        """Cancel checkout process"""
        self.checkout_wizard.setCurrentIndex(0)
        self.update_checkout_wizard_ui()

    def checkout_finish_wizard(self):
        """Complete checkout process"""
        if not self.current_checkout:
            return
            
        try:
            # Update room status
            rooms = get_all_rooms()
            room_info = next((r for r in rooms if r['id'] == self.current_checkout['room_id']), None)
            if room_info:
                room_info = dict(room_info)
                room_info['status'] = 'Needs Cleaning'
                update_room(self.current_checkout['room_id'], room_info)
                self.room_status_changed.emit() # Emit signal for room status change
            
            # Update check-in status
            self.current_checkout['status'] = 'checked_out'
            self.current_checkout['actual_departure'] = self.checkout_actual_departure.date().toString('yyyy-MM-dd')
            self.current_checkout['total_charges'] = float(self.checkout_total_amount.text().replace('MAD ', ''))
            self.current_checkout['final_payment'] = float(self.checkout_amount_paid.text() or 0)
            self.current_checkout['payment_method'] = self.checkout_payment_method.currentText()
            
            update_checkin(self.current_checkout['checkin_id'], self.current_checkout)
            
            # Generate checkout receipt
            pdf_path = self.generate_checkout_receipt()
            if pdf_path and os.path.exists(pdf_path):
                os.startfile(pdf_path)
            
            # Show success message
            QMessageBox.information(self, "Success", "Check-out completed successfully!")
            
            # Reset and return to first step
            self.checkout_wizard.setCurrentIndex(0)
            self.update_checkout_wizard_ui()
            self.load_checked_in_guests()
            
        except Exception as e:
            logger.error(f"Error completing checkout: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to complete checkout: {str(e)}")

    def show_checkout_confirmation(self):
        """Show checkout confirmation details"""
        message = f"""
        <div style='font-size:15px;'>
        <b style='font-size:18px;color:#27ae60;'>Check-out Summary</b><br><br>
        <b>Guest:</b> {self.checkout_guest_name.text()}<br>
        <b>Room:</b> {self.checkout_room.text()}<br>
        <b>Arrival:</b> {self.checkout_arrival.text()}<br>
        <b>Departure:</b> {self.checkout_actual_departure.date().toString('yyyy-MM-dd')}<br><br>
        <b>Charges:</b><br>
        &nbsp;&nbsp;Room Charges: {self.checkout_room_charges.text()}<br>
        &nbsp;&nbsp;Additional Charges: {self.checkout_additional_charges.text()}<br>
        &nbsp;&nbsp;Total Amount: {self.checkout_total_amount.text()}<br>
        &nbsp;&nbsp;Amount Paid: MAD {float(self.checkout_amount_paid.text() or 0):.2f}<br>
        &nbsp;&nbsp;Amount Due: {self.checkout_amount_due.text()}<br>
        &nbsp;&nbsp;Payment Method: {self.checkout_payment_method.currentText()}<br>
        </div>
        """
        self.checkout_confirmation_label.setText(message)

    def print_receipt(self):
        try:
            # Only handle checkout receipt
            if hasattr(self, 'tab_widget') and self.tab_widget.currentIndex() == 2:
                pdf_path = self.generate_checkout_receipt()
                if pdf_path and os.path.exists(pdf_path):
                    os.startfile(pdf_path)
                else:
                    QMessageBox.warning(self, "Error", "Failed to generate receipt PDF")
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to print receipt: {str(e)}")

    def update_checkout_wizard_ui(self):
        """Update checkout wizard UI based on current step"""
        current_step = self.checkout_wizard.currentIndex()
        
        # Update progress indicators
        for i, (number_label, name_label) in enumerate(self.checkout_progress_labels):
            if i < current_step:  # Completed steps
                number_label.setProperty("active", "true")
                number_label.setProperty("completed", "true")
                name_label.setProperty("active", "true")
                name_label.setProperty("completed", "true")
            elif i == current_step:  # Current step
                number_label.setProperty("active", "true")
                number_label.setProperty("completed", "false")
                name_label.setProperty("active", "true")
                name_label.setProperty("completed", "false")
            else:  # Future steps
                number_label.setProperty("active", "false")
                number_label.setProperty("completed", "false")
                name_label.setProperty("active", "false")
                name_label.setProperty("completed", "false")
            
            # Force style update
            number_label.style().unpolish(number_label)
            number_label.style().polish(number_label)
            name_label.style().unpolish(name_label)
            name_label.style().polish(name_label)
        
        # Update navigation buttons
        self.checkout_back_btn.setVisible(current_step > 0)
        self.checkout_next_btn.setVisible(current_step < self.checkout_wizard.count() - 1)
        self.checkout_finish_btn.setVisible(current_step == self.checkout_wizard.count() - 1)
        
        # Update button states
        if current_step == 2:  # Payment step
            try:
                amount_due = float(self.checkout_amount_due.text().replace('MAD ', ''))
                self.checkout_finish_btn.setEnabled(amount_due == 0)
            except:
                self.checkout_finish_btn.setEnabled(False)
        else:
            self.checkout_finish_btn.setEnabled(True)

    def update_wizard_ui(self):
        """Update wizard UI based on current step and validation state"""
        step = self.wizard.currentIndex()
        steps = [
            "Guest Details", "Stay Details", "Room Selection", "Payment"
        ]
        
        # Reset all steps to default style
        for i, (number_label, name_label) in enumerate(self.progress_labels):
            completed = False
            active = False
            
            if i < step:  # Completed steps
                completed = True
                active = True
                
                # Check if step was completed with all requirements
                if i == 0 and not self.guest_select_combo.currentData():
                    completed = False  # Guest not selected
                elif i == 2 and not self.selected_room_id:
                    completed = False  # Room not selected
                elif i == 3:
                    try:
                        if not self.payment_method.currentText():
                            completed = False  # Payment method not selected
                    except:
                        completed = False
            elif i == step:  # Current step
                active = True
                completed = False
            else:  # Future steps
                active = False
                completed = False
                
            # Set properties for styling
            number_label.setProperty("active", "true" if active else "false")
            number_label.setProperty("completed", "true" if completed else "false")
            name_label.setProperty("active", "true" if active else "false")
            name_label.setProperty("completed", "true" if completed else "false")
            
            # Force style update
            number_label.style().unpolish(number_label)
            number_label.style().polish(number_label)
            name_label.style().unpolish(name_label)
            name_label.style().polish(name_label)
        
        # Update button states
        self.back_btn.setEnabled(step > 0)
        self.next_btn.setVisible(step < 3)  # Show next button for first 3 steps
        self.finish_btn.setVisible(step == 3)  # Show finish button on payment step
        
        # Enable next button based on current step validation
        if step == 0:  # Guest Details step
            # Enable next button if a valid guest is selected (not the dummy option)
            current_index = self.guest_select_combo.currentIndex()
            # The button should be enabled if an item other than the "--Select guest--" placeholder is selected.
            self.next_btn.setEnabled(current_index > 0)
        elif step == 1:  # Stay Details step
            # Ensure next button is enabled to proceed to Room Selection
            self.next_btn.setEnabled(True) 
        elif step == 2:  # Room Selection step
            self.next_btn.setEnabled(bool(self.selected_room_id))
        elif step == 3:  # Payment step
            # Enable finish button if payment method is selected
            self.finish_btn.setEnabled(bool(self.payment_method.currentText()))

    def next_step(self):
        current_step = self.wizard.currentIndex()
        
        # Require guest selection/input in step 1
        if current_step == 0:
            if not self.guest_select_combo.currentData():  # Check if a guest is selected from combo
                QMessageBox.warning(self, "Guest Required", "Please select a guest from the dropdown before proceeding.")
                return
        
        # Validate room selection before proceeding to payment step
        if current_step == 2:  # Room Selection step
            if not self.selected_room_id:
                QMessageBox.warning(self, "Room Required", "Please select a room before proceeding.")
                return
        
        # Validate payment information before proceeding to confirmation
        if current_step == 3:  # Payment step
            if not self.payment_method.currentText():
                QMessageBox.warning(self, "Payment Method Required", "Please select a payment method.")
                return
            try:
                # Ensure payment amount is valid
                if not self.payment_amount.text() or Decimal(self.payment_amount.text().replace('MAD ', '').strip() or '0') <= 0:
                    QMessageBox.warning(self, "Invalid Amount", "Payment amount must be greater than zero.")
                    return
                # Check if there's an amount due and confirm partial payment
                amount_due = Decimal(self.amount_due.text().replace('MAD ', '').strip() or '0')
                if amount_due > 0 and self.total_paid.text():
                    result = QMessageBox.question(
                        self, 
                        "Confirm Partial Payment", 
                        "There is still an amount due. Are you sure you want to proceed with partial payment?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if result == QMessageBox.StandardButton.No:
                        return
            except Exception as e:
                logger.error(f"Payment validation error: {str(e)}")
                QMessageBox.warning(self, "Invalid Amount", "Please enter a valid payment amount.")
                return
                
        # Move to next step
        if current_step < self.wizard.count() - 1:
            self.wizard.setCurrentIndex(current_step + 1)
            
            # Handle specific step actions after moving to the next index
            new_current_step = self.wizard.currentIndex() # Get the new index after setCurrentIndex
            
            if new_current_step == 1: # Moved to Stay Details
                # No specific action needed here for button enablement, handled by update_wizard_ui
                pass
            elif new_current_step == 2:  # Moved to Room Selection
                self.load_room_grid() # Load rooms to ensure selection is reflected
                self.update_wizard_ui() # Update UI after loading rooms to check selected_room_id
            elif new_current_step == 3:  # Moved to Payment
                self.update_payment_amount() # Update payment amount based on room/dates
                # The original code had a step 4 (index 4) for confirmation, but the steps list only goes up to 3 (Payment).
                # If you intend to add a confirmation step, ensure the steps list and wizard count are updated accordingly.
                # elif self.wizard.currentIndex() == 4:  # Step 5: Confirmation
                #     self.show_confirmation_details()
                
            # Update UI after step change
            self.update_wizard_ui() # Ensure UI is updated for the new step, crucial for button states

    def show_confirmation_details(self):
        # Generate check-in and transaction IDs if not already generated
        if not hasattr(self, 'checkin_id'):
            self.checkin_id = str(uuid.uuid4())[:8]
            self.transaction_id = str(uuid.uuid4())[:8]
            self.checkin_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Prepare summary
        guest_name = f"{self.guest_first_name_label.text()} {self.guest_last_name_label.text()}"
        guest = self.guest_select_combo.currentData()
        guest_email = guest.get('email', '') if guest else ''
        guest_phone = guest.get('phone', '') if guest else ''
        arrival = self.arrival_date.selectedDate().toString('yyyy-MM-dd')
        departure = self.departure_date.selectedDate().toString('yyyy-MM-dd')
        num_guests = self.num_guests.text()
        room = self.selected_room_id
        rooms = get_all_rooms()
        room_info = next((r for r in rooms if r['id'] == room), {})
        room_number = room_info.get('number', '')
        room_type = room_info.get('type', '')
        total_paid = self.total_paid.text()
        amount_due = self.amount_due.text()
        payment_method = self.payment_method.currentText()
        status = self.payment_status_label.text()
        
        # Detailed confirmation message
        message = f"""
        <div style='font-size:15px;'>
        <b style='font-size:18px;color:#27ae60;'>Check-In Confirmed!</b><br><br>
        <b>Check-In Number:</b> {self.checkin_id}<br>
        <b>Date of Check-In:</b> {self.checkin_date}<br>
        <b>Transaction ID:</b> {self.transaction_id}<br><br>
        <b>Guest Details:</b><br>
        &nbsp;&nbsp;Name: {guest_name}<br>
        &nbsp;&nbsp;Email: {guest_email}<br>
        &nbsp;&nbsp;Phone: {guest_phone}<br><br>
        <b>Stay Details:</b><br>
        &nbsp;&nbsp;Arrival: {arrival}<br>
        &nbsp;&nbsp;Departure: {departure}<br>
        &nbsp;&nbsp;Number of Guests: {num_guests}<br>
        <br><b>Room Details:</b><br>
        &nbsp;&nbsp;Room: {room_type} #{room_number}<br><br>
        <b>Payment Details:</b><br>
        &nbsp;&nbsp;Total Paid: MAD {total_paid}<br>
        &nbsp;&nbsp;Amount Due: MAD {amount_due}<br>
        &nbsp;&nbsp;Payment Method: {payment_method}<br>
        &nbsp;&nbsp;Payment Status: {status}<br>
        </div>
        <br><b style='color:#2980b9;'>Check-in has been successfully completed!</b>
        """
        # Assuming there's a confirmation_label in step 4 or a final confirmation step.
        # If not, you'll need to add one to your UI or adjust where this message is displayed.
        # self.confirmation_label.setText(message) 
        QMessageBox.information(self, "Check-In Confirmation", message) # Using QMessageBox for now if no dedicated label

    def prev_step(self):
        if self.wizard.currentIndex() > 0:
            current_step = self.wizard.currentIndex()
            self.wizard.setCurrentIndex(current_step - 1)
            # If going back to room selection step (step 2), reload the room grid with current selection
            if current_step - 1 == 2:
                self.load_room_grid()
            self.update_wizard_ui()

    def cancel_wizard(self):
        self.wizard.setCurrentIndex(0)
        self.update_wizard_ui()

    def finish_wizard(self):
        """Complete the check-in process"""
        try:
            # Validate all required fields
            if not self.guest_select_combo.currentData():
                QMessageBox.warning(self, "Error", "Please select a guest")
                return
                
            if not self.selected_room_id:
                QMessageBox.warning(self, "Error", "Please select a room")
                return
                
            if not self.payment_method.currentText():
                QMessageBox.warning(self, "Error", "Please select a payment method")
                return

            # Validate payment amount
            try:
                total_amount = Decimal(self.payment_amount.text().replace('MAD ', '').strip() or '0')
                if total_amount <= 0:
                    QMessageBox.warning(self, "Error", "Invalid payment amount")
                    return
            except Exception:
                QMessageBox.warning(self, "Error", "Invalid payment amount")
                return

            # Get guest data
            guest_data = self.guest_select_combo.currentData()
            guest_id = get_guest_id_by_name(
                self.guest_first_name_label.text(),
                self.guest_last_name_label.text()
            )
            if not guest_id and guest_data:
                guest_id = guest_data.get('id')

            # Create check-in record
            checkin_data = {
                'checkin_id': self.checkin_id,
                'transaction_id': self.transaction_id,
                'guest_id': guest_id,
                'room_id': self.selected_room_id,
                'arrival_date': self.arrival_date.selectedDate().toString('yyyy-MM-dd'),
                'departure_date': self.departure_date.selectedDate().toString('yyyy-MM-dd'),
                'num_guests': self.num_guests.value(),
                'payment_method': self.payment_method.currentText(),
                'total_paid': float(self.total_paid.text().replace('MAD ', '') or 0),
                'amount_due': float(self.amount_due.text().replace('MAD ', '') or 0),
                'status': 'checked_in',
                'checkin_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }

            # Save check-in to database
            self.safe_db_operation(insert_checkin, checkin_data)
            
            # --- Update Room Status to 'Occupied' ---
            rooms = get_all_rooms()
            room_to_update = next((r for r in rooms if r['id'] == self.selected_room_id), None)
            if room_to_update:
                updated_room_info = dict(room_to_update) # Create a mutable copy
                updated_room_info['status'] = 'Occupied'
                self.safe_db_operation(update_room, self.selected_room_id, updated_room_info)
                self.room_status_changed.emit() # Emit signal for room status change
            else:
                logger.warning(f"Room with ID {self.selected_room_id} not found for status update.")

            # Show success message with details
            success_msg = f"""
            Check-in completed successfully!
            
            Guest: {self.guest_first_name_label.text()} {self.guest_last_name_label.text()}
            Room: {self.selected_room_id}
            Check-in ID: {self.checkin_id}
            Arrival: {checkin_data['arrival_date']}
            Departure: {checkin_data['departure_date']}
            Payment Status: {self.payment_status_label.text()}
            """
            QMessageBox.information(self, "Success", success_msg)
            
            # Reset wizard and refresh lists
            self.reset_wizard_fields()
            self.wizard.setCurrentIndex(0)
            self.update_wizard_ui()
            self.load_checkin_list()
            self.load_checked_in_guests()

        except Exception as e:
            logger.error(f"Error completing check-in: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to complete check-in: {str(e)}")

    def reset_wizard_fields(self):
        """Reset all fields in the wizard for a new check-in"""
        try:
            # Generate new IDs for the next check-in
            self.checkin_id = str(uuid.uuid4())[:8]
            self.transaction_id = str(uuid.uuid4())[:8]
            # Clear search and guest selection
            self.guest_select_combo.clear()
            self.guest_select_combo.clear()
            self.populate_guest_combo()  # Repopulate the dropdown
            
            # Clear guest details
            self.guest_first_name_label.setText("")
            self.guest_last_name_label.setText("")
            self.guest_id_number_label.setText("")
            self.guest_nationality_label.setText("")
            
            # Reset dates
            self.arrival_date.setSelectedDate(QDate.currentDate())
            self.departure_date.setSelectedDate(QDate.currentDate().addDays(1))
            
            # Reset guest count
            self.num_guests.setValue(MIN_GUESTS)
            
            # Reset room selection
            self.selected_room_id = None
            self.load_room_grid()
            
            # Reset payment fields
            self.payment_method.setCurrentIndex(0)
            self.payment_amount.setText("0.00")
            self.total_paid.clear()
            self.amount_due.setText("0.00")
            self.payment_status_label.setText("Pending")
            self.payment_progress.setValue(0)
            
            # Clear confirmation (if applicable, assuming a confirmation_label exists)
            # if hasattr(self, 'confirmation_label'):
            #     self.confirmation_label.setText("")
            
        except Exception as e:
            logger.error(f"Error resetting wizard fields: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", "Failed to reset form fields")

    def filter_checkin_list(self):
        """Filter check-in list based on search criteria"""
        try:
            search_text = self.search_input.text().lower()
            arrival_date = self.filter_arrival.date()
            departure_date = self.filter_departure.date()
            room_type = self.filter_room_type.currentText()
            
            for row in range(self.checkin_table.rowCount()):
                show_row = True
                
                # Check search text against all columns
                if search_text:
                    text_match = False
                    for col in range(self.checkin_table.columnCount() - 1):  # Exclude actions column
                        item = self.checkin_table.item(row, col)
                        if item and search_text in item.text().lower():
                            text_match = True
                            break
                    show_row = show_row and text_match
                
                # Check date range
                if show_row and (arrival_date.isValid() or departure_date.isValid()):
                    checkin_arrival = QDate.fromString(self.checkin_table.item(row, 2).text(), 'yyyy-MM-dd')
                    checkin_departure = QDate.fromString(self.checkin_table.item(row, 3).text(), 'yyyy-MM-dd')
                    
                    if arrival_date.isValid() and checkin_arrival < arrival_date:
                        show_row = False
                    if departure_date.isValid() and checkin_departure > departure_date:
                        show_row = False
                
                # Check room type
                if show_row and room_type != "All Room Types":
                    room_info = self.checkin_table.item(row, 4).text()
                    if room_type not in room_info:
                        show_row = False
                
                self.checkin_table.setRowHidden(row, not show_row)
                
        except Exception as e:
            logger.error(f"Error filtering check-in list: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", "Failed to filter check-in list")

    def filter_guest_dropdown(self):
        """Filter the guest dropdown based on search text"""
        search_text = self.guest_select_combo.currentText().lower()
        self.guest_select_combo.clear()
        
        # Add the "--Select guest--" option at the beginning
        self.guest_select_combo.addItem("--Select guest--", None)

        # Create a list of matching guests
        matching_guests = []
        for guest in self.guests_data:
            full_name = f"{guest['first_name']} {guest['last_name']}"
            if search_text in full_name.lower():
                matching_guests.append((full_name, guest))
        
        # Sort matching guests by name
        matching_guests.sort(key=lambda x: x[0].lower())
        
        # Add filtered guests to dropdown
        for full_name, guest in matching_guests:
            self.guest_select_combo.addItem(full_name, guest)
        
        # Update completer with current matches
        self.guest_completer.setModel(self.guest_select_combo.model())
        
        # Ensure the UI is updated after filtering
        self.update_wizard_ui()

    def on_guest_selected(self, index):
        """Handle guest selection from dropdown"""
        if index >= 0:
            guest = self.guest_select_combo.currentData()
            if guest:
                self.guest_first_name_label.setText(guest.get('first_name', ''))
                self.guest_last_name_label.setText(guest.get('last_name', ''))
                self.guest_id_number_label.setText(guest.get('id_number', ''))
                self.guest_nationality_label.setText(guest.get('nationality', ''))
            else:
                self.guest_first_name_label.setText("")
                self.guest_last_name_label.setText("")
                self.guest_id_number_label.setText("")
                self.guest_nationality_label.setText("")
        
        # Update the wizard UI to reflect the change in guest selection
        self.update_wizard_ui()

    def reload_guests_for_search(self):
        """Reload guests data and update dropdown"""
        self.guests_data = get_all_guests()
        self.filter_guest_dropdown()  # This will populate the dropdown with all guests initially

    def load_room_grid(self):
        # Remove old buttons
        for i in reversed(range(self.room_grid_layout.count())):
            widget = self.room_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        rooms = get_all_rooms()
        cols = 5
        for idx, room in enumerate(rooms):
            btn = QPushButton(f"{room['number']}\n{room.get('type','')}\n{room.get('status','')}")
            btn.setCheckable(True)
            btn.setMinimumSize(100, 60)
            color = self._room_color(room.get('status',''))
            highlight = (self.selected_room_id == room['id'])
            style = f"background:{color};color:white;font-weight:bold;border-radius:8px;"
            if highlight:
                style += "border: 3px solid #f1c40f;"
                btn.setChecked(True)
            else:
                style += "border: none;"
                btn.setChecked(False)
            btn.setStyleSheet(style)
            if room.get('status') in ["Occupied", "Out of Order"]:
                btn.setEnabled(False)
            btn.clicked.connect(lambda _, rid=room['id']: self.select_room(rid))
            self.room_grid_layout.addWidget(btn, idx // cols, idx % cols)

    def _room_color(self, status):
        return {
            "Available": "#27ae60",
            "Vacant": "#27ae60",  # Added Vacant status with green color
            "Reserved": "#8e44ad",
            "Occupied": "#c0392b",
            "Not Available": "#95a5a6",
            "Needs Cleaning": "#f1c40f"
        }.get(status, "#bdc3c7")

    def select_room(self, room_id):
        """Select a room for check-in with thread safety and validation"""
        try:
            self.room_mutex.lock()
            try:
                # Verify room is still available
                rooms = self.safe_db_operation(get_all_rooms)
                room_info = next((r for r in rooms if r['id'] == room_id), None)
                
                if not room_info:
                    raise ValidationError("Selected room not found")
                
                if room_info.get('status') in ["Occupied", "Out of Order"]:
                    raise ValidationError("Selected room is not available")
                
                self.selected_room_id = room_id
                self.load_room_grid()  # Refresh to update selection
                self.update_payment_amount()  # Update payment amount when room is selected
                
            finally:
                self.room_mutex.unlock()
                # Crucial: Update wizard UI after room selection to enable/disable next button
                self.update_wizard_ui()
                
        except (DatabaseError, ValidationError) as e:
            QMessageBox.warning(self, "Error", str(e))
            self.selected_room_id = None
            self.load_room_grid()
            self.update_wizard_ui() # Also update UI on error to disable button
        except Exception as e:
            logger.error(f"Error selecting room: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", "An unexpected error occurred while selecting the room")
            self.update_wizard_ui() # Also update UI on unexpected error

    def update_payment_amount(self):
        """Calculate payment amount based on room type rate and number of nights"""
        try:
            if not self.selected_room_id:
                self.payment_amount.setText("0.00")
                return

            # Get room information
            rooms = self.safe_db_operation(get_all_rooms)
            room_info = next((r for r in rooms if r['id'] == self.selected_room_id), None)
            if not room_info or not room_info.get('type'):
                raise ValidationError("Invalid room selection")

            # Get room rate for the room type
            rates = self.safe_db_operation(get_room_rates)
            room_rate = next((r['night_rate'] for r in rates if r['room_type'] == room_info['type']), None)
            if not room_rate:
                raise ValidationError("Room rate not found for selected room type")

            # Validate dates and calculate nights
            nights = self.validate_dates(
                self.arrival_date.selectedDate(),
                self.departure_date.selectedDate()
            )

            # Calculate total amount
            total_amount = Decimal(str(room_rate)) * Decimal(str(nights))
            self.payment_amount.setText(f"MAD {total_amount:.2f}")
            self.update_amount_due()

        except (DatabaseError, ValidationError) as e:
            QMessageBox.warning(self, "Error", str(e))
            self.payment_amount.setText("0.00")
        except Exception as e:
            logger.error(f"Error updating payment amount: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", "An unexpected error occurred while calculating payment")
            self.payment_amount.setText("0.00")

    def update_amount_due(self):
        try:
            # Extract numeric values from text fields
            total_str = self.payment_amount.text().replace('MAD ', '').strip() or '0'
            paid_str = self.total_paid.text().strip() or '0'
            
            # Validate input is numeric
            if not self.validate_payment_input(paid_str):
                self.total_paid.setStyleSheet("background-color: #ffcccc;")
                paid_str = '0'
            else:
                self.total_paid.setStyleSheet("")
                
            total = Decimal(total_str)
            paid = Decimal(paid_str)
            due = max(total - paid, Decimal('0'))
            self.amount_due.setText(f"MAD {due:.2f}")
        except Exception as e:
            logger.error(f"Error updating amount due: {str(e)}")
            self.amount_due.setText(self.payment_amount.text())
        self.update_payment_status()

    def update_payment_status(self):
        try:
            total = Decimal(self.payment_amount.text().replace('MAD ', '').strip() or '0')
            paid_text = self.total_paid.text().strip()
            # Validate payment input
            if paid_text and not self.validate_payment_input(paid_text):
                self.total_paid.setStyleSheet("background-color: #ffcccc;")
                status = "Invalid Payment"
                paid = Decimal('0')
            else:
                self.total_paid.setStyleSheet("")
                paid = Decimal(paid_text or '0')
                if paid_text == "":
                    status = "Pending"
                elif paid == total:
                    status = "Completed"
                elif Decimal('0') < paid < total:
                    status = "Partially Paid"
                else:
                    status = "Pending"
        except Exception as e:
            logger.error(f"Error updating payment status: {str(e)}")
            status = "Pending"
            total = Decimal('0')
            paid = Decimal('0')
        self.payment_status_label.setText(status)
        self.payment_progress.setValue(int((paid / total * 100) if total > 0 else 0))

    def _legend_label(self, text, color):
        lbl = QLabel(text)
        lbl.setStyleSheet(f"background:{color};color:white;padding:4px 10px;border-radius:6px;")
        return lbl 

    def load_checkin_list(self):
        """Load and display check-ins in the list"""
        self.checkin_table.setRowCount(0)  # Clear existing rows
        checkins = get_all_checkins()
        
        for checkin in checkins:
            row = self.checkin_table.rowCount()
            self.checkin_table.insertRow(row)
            
            # Add data to columns
            self.checkin_table.setItem(row, 0, QTableWidgetItem(checkin['checkin_id']))
            self.checkin_table.setItem(row, 1, QTableWidgetItem(f"{checkin['first_name']} {checkin['last_name']}"))
            self.checkin_table.setItem(row, 2, QTableWidgetItem(checkin['arrival_date']))
            self.checkin_table.setItem(row, 3, QTableWidgetItem(checkin['departure_date']))
            self.checkin_table.setItem(row, 4, QTableWidgetItem(f"{checkin['room_type']} #{checkin['room_number']}"))
            self.checkin_table.setItem(row, 5, QTableWidgetItem(checkin['status']))
            
            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)
            actions_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the buttons
            
            view_btn = QPushButton("View")
            view_btn.setObjectName("tableActionButton")
            view_btn.setProperty("action", "view")
            view_btn.setFixedWidth(80)
            view_btn.clicked.connect(lambda _, c=checkin: self.view_checkin(c))
            
            extra_btn = QPushButton("Extra")
            extra_btn.setObjectName("tableActionButton")
            extra_btn.setProperty("action", "extra")
            extra_btn.setFixedWidth(80)
            extra_btn.clicked.connect(lambda _, c=checkin: self.add_extra_charge(c))
            
            actions_layout.addWidget(view_btn)
            actions_layout.addWidget(extra_btn)
            self.checkin_table.setCellWidget(row, 6, actions_widget)

    def view_checkin(self, checkin):
        """View details of a specific check-in"""
        # Get extra charges
        extra_charges = get_booking_services(checkin['id'])
        total_extra_charges = get_total_booking_charges(checkin['id'])
        
        # Format extra charges for display
        extra_charges_text = ""
        if extra_charges:
            extra_charges_text = "<br><b>Extra Charges:</b><br>"
            for charge in extra_charges:
                extra_charges_text += f"&nbsp;&nbsp;{charge['service_name']} ({charge['quantity']} {charge['unit']}): MAD {charge['total_charge']:.2f}<br>"
            extra_charges_text += f"<br><b>Total Extra Charges:</b> MAD {total_extra_charges:.2f}<br>"
        
        message = f"""
        <div style='font-size:15px;'>
        <b>Check-In Details</b><br><br>
        <b>Check-In Number:</b> {checkin['checkin_id']}<br>
        <b>Transaction ID:</b> {checkin['transaction_id']}<br>
        <b>Date of Check-In:</b> {checkin['checkin_date']}<br><br>
        <b>Guest:</b> {checkin['first_name']} {checkin['last_name']}<br>
        <b>Room:</b> {checkin['room_type']} #{checkin['room_number']}<br>
        <b>Arrival:</b> {checkin['arrival_date']}<br>
        <b>Departure:</b> {checkin['departure_date']}<br>
        <b>Number of Guests:</b> {checkin['num_guests']}<br><br>
        <b>Payment Details:</b><br>
        &nbsp;&nbsp;Total Paid: MAD {checkin['total_paid']:.2f}<br>
        &nbsp;&nbsp;Amount Due: MAD {checkin['amount_due']:.2f}<br>
        &nbsp;&nbsp;Payment Method: {checkin['payment_method']}<br>
        &nbsp;&nbsp;Payment Status: {checkin['status']}<br>
        {extra_charges_text}
        </div>
        """
        QMessageBox.information(self, "Check-In Details", message)

    def add_extra_charge(self, checkin):
        """Open dialog to add extra charge for a check-in"""
        dialog = AddExtraChargeDialog(
            checkin['id'],
            f"{checkin['first_name']} {checkin['last_name']}",
            f"{checkin['room_type']} #{checkin['room_number']}",
            self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_checkin_list()  # Refresh the list to show updated charges 

    def refresh_guest_lists(self):
        """Refresh all guest dropdowns and lists"""
        # Refresh the guest dropdown in new check-in tab
        if hasattr(self, 'guest_select_combo'):
            self.reload_guests_for_search()
            # If there's search text, reapply the filter
            if hasattr(self, 'guest_search') and self.guest_search.text():
                self.filter_guest_dropdown() 

    def generate_checkout_receipt(self):
        """Generate checkout receipt using FPDF with proper error handling and encoding support"""
        try:
            # Create receipts directory if it doesn't exist
            os.makedirs(RECEIPTS_DIR, exist_ok=True)
            
            # Create a PDF object with UTF-8 support
            # Use 'P' for portrait, 'mm' for millimeters, and 'A5' for page size
            # Create a PDF object with UTF-8 support
            pdf = FPDF()
            pdf.add_page()
            pdf.set_auto_page_break(auto=False, margin=5)
            pdf.set_left_margin(10)
            pdf.set_top_margin(10)
            pdf.set_right_margin(10)
            
            # Set font with UTF-8 support
            # Use DejaVuSans.ttf for regular and DejaVuSans-Bold.ttf for bold
            font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
            font_path_regular = os.path.join(font_dir, 'DejaVuSans.ttf')
            font_path_bold = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
            pdf.add_font('DejaVu', '', font_path_regular, uni=True)
            pdf.add_font('DejaVu', 'B', font_path_bold, uni=True)
            pdf.set_font('DejaVu', '', 10)

            # --- Hotel Information (Header) ---
            # Logo (placeholder - replace with actual image path if available)
            # For now, using a placeholder image URL. In a real application, you'd use a local path.
            # You might need to adjust the x, y, width, height for your logo.
            # Example: pdf.image("path/to/your/logo.png", x=160, y=10, w=40)
            # For now, I'll simulate a logo with text or leave it out if no image is provided.
            # If you have a logo image, ensure it's accessible and replace the placeholder.
            # For this example, I'll just put the logo at the right without an actual image.
            
            page_width = pdf.w - 2 * pdf.l_margin
            # Hotel Name, Address, Phone, Email (Left Aligned)
            pdf.set_font('DejaVu', 'B', 16)
            pdf.cell(page_width * 0.7, 10, "Hotel KISSAN Agdz", 0, 0, "L")
            # Placeholder for logo (right aligned)
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(page_width * 0.3, 10, "LOGO HERE", 0, 1, "R") # Placeholder for logo
            
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 5, "Avenue Mohamed V, Agdz, Province of Zagora, Morocco", 0, 1, "L")
            pdf.cell(0, 5, "Phone: +212 5 44 84 30 44", 0, 1, "L")
            pdf.cell(0, 5, "Fax: +212 5 44 84 32 58", 0, 1, "L")
            pdf.cell(0, 5, "Email: kissane@iam.net.ma", 0, 1, "L")
            pdf.ln(5)

            # --- Title "INVOICE" ---
            pdf.set_font('DejaVu', 'B', 24)
            pdf.cell(0, 15, "INVOICE", 0, 1, "C")
            pdf.ln(5)

            # --- Two Columns: Invoice Details (Left) and Billed To (Right) ---
            col_width = page_width / 2
            pdf.set_font('DejaVu', 'B', 12)
            pdf.cell(col_width, 5, "Invoice Details:", 0, 0, "L")
            pdf.cell(col_width, 5, "Billed To:", 0, 1, "L")
            
            pdf.set_font('DejaVu', '', 10)
            invoice_date = datetime.now().strftime('%d-%m-%Y') # Format as dd-mm-yyyy
            
            # Left Column: Invoice Number, Invoice Date
            pdf.cell(col_width, 4, f"Invoice Number: {self.current_checkout['checkin_id']}", 0, 0, "L")
            # Right Column: Client Name
            pdf.cell(col_width, 4, f"Full Name: {self.checkout_guest_name.text()}", 0, 1, "L")

            pdf.cell(col_width, 4, f"Invoice Date: {invoice_date}", 0, 0, "L")
            # Right Column: Check-in Date
            pdf.cell(col_width, 4, f"Check-in Date: {self.checkout_arrival.text()}", 0, 1, "L")

            pdf.cell(col_width, 4, "", 0, 0, "L") # Empty cell for alignment
            # Right Column: Check-out Date
            pdf.cell(col_width, 4, f"Check-out Date: {self.checkout_actual_departure.date().toString('yyyy-MM-dd')}", 0, 1, "L")
            pdf.ln(3)

            # --- Stay Details Table ---
            pdf.set_font('DejaVu', 'B', 12)
            pdf.cell(0, 10, "Stay Details:", 0, 1, "L")
            pdf.set_fill_color(200, 220, 255)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('DejaVu', 'B', 10)
            
            # Calculate column widths for Stay Details table (occupy 100% width)
            room_type_col_width = page_width * 0.4
            nights_col_width = page_width * 0.2
            rate_col_width = page_width * 0.2
            total_col_width = page_width * 0.2

            pdf.cell(room_type_col_width, 8, "Room Type", 1, 0, "L", 1)
            pdf.cell(nights_col_width, 8, "Nights", 1, 0, "C", 1)
            pdf.cell(rate_col_width, 8, "Rate (MAD)", 1, 0, "R", 1)
            pdf.cell(total_col_width, 8, "Total (MAD)", 1, 1, "R", 1)

            pdf.set_font('DejaVu', '', 10)
            
            # Get room info and calculate nights
            rooms = get_all_rooms()
            room_info = next((r for r in rooms if r['id'] == self.current_checkout['room_id']), None)
            
            room_type_display = room_info.get('type', 'N/A') if room_info else 'N/A'
            
            try:
                arrival_date_dt = datetime.strptime(self.checkout_arrival.text(), '%Y-%m-%d')
                departure_date_dt = datetime.strptime(self.checkout_actual_departure.date().toString('yyyy-MM-dd'), '%Y-%m-%d')
                nights = (departure_date_dt - arrival_date_dt).days
                if nights <= 0:
                    nights = MIN_NIGHTS
            except ValueError as e:
                logger.error(f"Error calculating nights for receipt: {str(e)}")
                nights = MIN_NIGHTS

            # Get room rate
            rates = get_room_rates()
            room_rate = Decimal(str(next((r['night_rate'] for r in rates if r['room_type'] == room_type_display), Decimal('0'))))
            
            room_charges = Decimal(str(nights)) * room_rate

            pdf.cell(room_type_col_width, 8, room_type_display, 1, 0, "L")
            pdf.cell(nights_col_width, 8, str(nights), 1, 0, "C")
            pdf.cell(rate_col_width, 8, f"{float(room_rate):.2f}", 1, 0, "R")
            pdf.cell(total_col_width, 8, f"{float(room_charges):.2f}", 1, 1, "R")
            pdf.ln(2)

            # --- Additional Services Table ---
            extra_services = self.safe_db_operation(get_booking_services, self.current_checkout['id'])
            if extra_services:
                pdf.set_font('DejaVu', 'B', 12)
                pdf.cell(0, 10, "Additional Services:", 0, 1, "L")
                pdf.set_fill_color(200, 220, 255)
                pdf.set_text_color(0, 0, 0)
                pdf.set_font('DejaVu', 'B', 10)

                # Calculate column widths for Additional Services table (occupy 100% width)
                service_col_width = page_width * 0.4
                quantity_col_width = page_width * 0.2
                unit_price_col_width = page_width * 0.2
                total_service_col_width = page_width * 0.2

                pdf.cell(service_col_width, 8, "Service", 1, 0, "L", 1)
                pdf.cell(quantity_col_width, 8, "Quantity", 1, 0, "C", 1)
                pdf.cell(unit_price_col_width, 8, "Unit Price (MAD)", 1, 0, "R", 1)
                pdf.cell(total_service_col_width, 8, "Total (MAD)", 1, 1, "R", 1)

                pdf.set_font('DejaVu', '', 10)
                for service in extra_services:
                    pdf.cell(service_col_width, 8, service['service_name'], 1, 0, "L")
                    pdf.cell(quantity_col_width, 8, str(service['quantity']), 1, 0, "C")
                    pdf.cell(unit_price_col_width, 8, f"{float(Decimal(str(service['unit_price_at_time_of_charge']))):.2f}", 1, 0, "R")
                    pdf.cell(total_service_col_width, 8, f"{float(Decimal(str(service['total_charge']))):.2f}", 1, 1, "R")
                pdf.ln(2)

            # --- Totals (Right Aligned Below Tables) ---
            additional_charges = Decimal(self.checkout_additional_charges.text().replace('MAD ', '').strip() or '0')
            subtotal = room_charges + additional_charges
            
            # Get selected tax details for display and calculation
            selected_tax = self.checkout_tax_select.currentData()
            tax_amount = Decimal('0')
            tax_display_name = "N/A"

            if selected_tax:
                taxable_base = Decimal('0')
                if selected_tax.get('apply_to_rooms', False):
                    taxable_base += room_charges
                if selected_tax.get('apply_to_services', False):
                    taxable_base += additional_charges

                if selected_tax['tax_type'] == 'percentage':
                    percentage = Decimal(str(selected_tax.get('percentage', 0))) / Decimal('100')
                    tax_amount = taxable_base * percentage
                    # tax_display_name = f"{selected_tax['name']} ({float(selected_tax.get('percentage', 0)):.0f}%)"
                elif selected_tax['tax_type'] == 'fixed':
                    tax_amount = Decimal(str(selected_tax.get('amount', 0)))
                    # tax_display_name = f"{selected_tax['name']} (Fixed)"
            
            total_amount = subtotal + tax_amount

            pdf.set_x(pdf.l_margin + page_width * 0.6) # Move to 60% of the page width
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(page_width * 0.2, 8, "Subtotal:", 1, 0, "L")
            pdf.cell(page_width * 0.2, 8, f"{float(subtotal):.2f} MAD", 1, 1, "R")

            pdf.set_x(pdf.l_margin + page_width * 0.6)
            pdf.cell(page_width * 0.2, 8, f"TAX", 1, 0, "L")
            pdf.cell(page_width * 0.2, 8, f"MAD {float(tax_amount):.2f}", 1, 1, "R")
            
            pdf.set_x(pdf.l_margin + page_width * 0.6)
            pdf.set_font('DejaVu', 'B', 12) # Bold font for total due
            pdf.cell(page_width * 0.2, 8, "Total Due:", 1, 0, "L")
            pdf.cell(page_width * 0.2, 8, f"{float(total_amount):.2f} MAD", 1, 1, "R")
            pdf.ln(20)

            # --- Client Signature ---
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 5, "_________________________", 0, 1, "R")
            pdf.cell(0, 5, "Client Signature", 0, 1, "R")
            pdf.ln(20)

            # --- Footer with Divider ---
            # Calculate footer height and position it at the very bottom
            footer_text = "Payment is due upon receipt. We accept cash, credit card, and bank transfers.\nThank you for choosing Grand Oasis Hotel. We hope to see you again soon!"
            
            # Calculate the height of the multi_cell for the footer text
            # This requires setting the font first to get the correct string_width.
            pdf.set_font('DejaVu', '', 10)
            # Use pdf.get_string_width to estimate line breaks for multi_cell
            # A rough estimate of lines for multi_cell (page_width / font_size_factor)
            # For 2 lines, it's roughly 2 * line_height (5mm) = 10mm
            # The actual height can be obtained more accurately, but for a fixed text,
            # a hardcoded estimate is often sufficient.
            
            # Estimated total height of footer content:
            # 1. Horizontal line: negligible height, but takes up current_y.
            # 2. pdf.ln(5): 5mm
            # 3. multi_cell(0, 5, footer_text, 0, "C"): 2 lines * 5mm/line = 10mm (approx)
            # Total estimated footer content height = 5mm (line break) + 10mm (text) = 15mm
            
            # Position Y at the bottom of the page, considering bottom margin
            # pdf.h is total page height (A5 is 210mm)
            # pdf.b_margin is bottom margin (default 10mm, but auto_page_break margin is 30mm)
            # We want to place the footer content to end exactly at pdf.h - pdf.b_margin
            
            # Calculate the y-coordinate where the footer content should *start*
            # This ensures the footer is flush with the bottom margin.
            footer_content_height = 15 # Estimated height of the footer text and line break
            footer_start_y = pdf.h - pdf.b_margin - footer_content_height

            # Set current Y position explicitly to place the footer at the bottom
            pdf.set_y(footer_start_y)

            pdf.set_draw_color(0, 0, 0) # Black line
            # Draw line across the page width
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y()) # Draw a horizontal line
            pdf.ln(5) # Small line break after the divider

            pdf.set_font('DejaVu', '', 10)
            pdf.multi_cell(0, 5, footer_text, 0, "C")
            # Removed final pdf.ln(10) as positioning is now explicit.

            # Define the output PDF file path
            output_pdf_file = os.path.join(RECEIPTS_DIR, f"checkout_receipt_{self.current_checkout['checkin_id']}.pdf")
            
            # Save the PDF
            pdf.output(output_pdf_file)
            
            # Verify the file was created
            if not os.path.exists(output_pdf_file):
                raise IOError("Failed to create PDF file")
                
            return output_pdf_file

        except Exception as e:
            logger.error(f"Error generating PDF: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to generate invoice PDF: {str(e)}")
            return None
