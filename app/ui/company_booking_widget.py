from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QDateEdit, QFormLayout, QStackedWidget, QMessageBox, QFrame, QSpinBox,
    QTextEdit, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QIcon
import uuid
from datetime import datetime
import logging
from decimal import Decimal
from app.models.company_booking import CompanyBooking
from app.services.company_booking_service import CompanyBookingService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyBookingWidget(QWidget):
    """Widget for managing company bookings"""
    
    room_status_changed = pyqtSignal()  # Signal when room status changes

    def __init__(self, parent=None):
        super().__init__(parent)
        self.company_booking_service = CompanyBookingService()
        self.setup_ui()

    def setup_ui(self):
        """Set up the user interface"""
        layout = QVBoxLayout(self)

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.new_booking_tab = QWidget()
        self.active_bookings_tab = QWidget()
        self.history_tab = QWidget()
        
        self.tab_widget.addTab(self.new_booking_tab, "New Company Booking")
        self.tab_widget.addTab(self.active_bookings_tab, "Active Bookings")
        self.tab_widget.addTab(self.history_tab, "Booking History")
        
        layout.addWidget(self.tab_widget)
        
        # Setup each tab
        self.setup_new_booking_tab()
        self.setup_active_bookings_tab()
        self.setup_history_tab()

    def setup_new_booking_tab(self):
        """Set up the new company booking tab"""
        layout = QVBoxLayout(self.new_booking_tab)
        
        # Company Information Section
        company_frame = QFrame()
        company_frame.setObjectName("companyFrame")
        company_layout = QFormLayout(company_frame)
        
        self.company_name = QLineEdit()
        self.contact_person = QLineEdit()
        self.contact_email = QLineEdit()
        self.contact_phone = QLineEdit()
        self.billing_address = QTextEdit()
        self.tax_id = QLineEdit()
        self.payment_terms = QComboBox()
        self.payment_terms.addItems(["Net 30", "Net 15", "Due on Receipt", "Custom"])
        self.special_instructions = QTextEdit()
        
        company_layout.addRow("Company Name:", self.company_name)
        company_layout.addRow("Contact Person:", self.contact_person)
        company_layout.addRow("Email:", self.contact_email)
        company_layout.addRow("Phone:", self.contact_phone)
        company_layout.addRow("Billing Address:", self.billing_address)
        company_layout.addRow("Tax ID:", self.tax_id)
        company_layout.addRow("Payment Terms:", self.payment_terms)
        company_layout.addRow("Special Instructions:", self.special_instructions)
        
        layout.addWidget(company_frame)
        
        # Guest Bookings Section
        guests_frame = QFrame()
        guests_frame.setObjectName("guestsFrame")
        guests_layout = QVBoxLayout(guests_frame)
        
        guests_header = QLabel("Guest Bookings")
        guests_header.setObjectName("sectionTitle")
        guests_layout.addWidget(guests_header)
        
        self.guests_table = QTableWidget()
        self.guests_table.setColumnCount(8)
        self.guests_table.setHorizontalHeaderLabels([
            "Guest Name", "Room", "Check-in", "Check-out",
            "Nights", "Rate/Night", "Room Total", "Additional Charges"
        ])
        self.guests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        guests_layout.addWidget(self.guests_table)
        
        add_guest_btn = QPushButton("Add Guest")
        add_guest_btn.clicked.connect(self.add_guest_booking)
        guests_layout.addWidget(add_guest_btn)
        
        layout.addWidget(guests_frame)
        
        # Totals Section
        totals_frame = QFrame()
        totals_frame.setObjectName("totalsFrame")
        totals_layout = QFormLayout(totals_frame)
        
        self.subtotal = QLineEdit()
        self.subtotal.setReadOnly(True)
        self.tax_amount = QLineEdit()
        self.tax_amount.setReadOnly(True)
        self.total_amount = QLineEdit()
        self.total_amount.setReadOnly(True)
        
        totals_layout.addRow("Subtotal:", self.subtotal)
        totals_layout.addRow("Tax:", self.tax_amount)
        totals_layout.addRow("Total Amount:", self.total_amount)
        
        layout.addWidget(totals_frame)
        
        # Action Buttons
        buttons_layout = QHBoxLayout()
        
        save_btn = QPushButton("Save Booking")
        save_btn.clicked.connect(self.save_company_booking)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.clear_form)
        
        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)

    def setup_active_bookings_tab(self):
        """Set up the active bookings tab"""
        layout = QVBoxLayout(self.active_bookings_tab)
        
        # Search and filter section
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search bookings...")
        self.search_input.textChanged.connect(self.filter_bookings)
        
        self.status_filter = QComboBox()
        self.status_filter.addItems(["All", "Pending", "Confirmed", "Checked In", "Checked Out"])
        self.status_filter.currentTextChanged.connect(self.filter_bookings)
        
        filter_layout.addWidget(self.search_input)
        filter_layout.addWidget(self.status_filter)
        
        layout.addLayout(filter_layout)
        
        # Bookings table
        self.bookings_table = QTableWidget()
        self.bookings_table.setColumnCount(7)
        self.bookings_table.setHorizontalHeaderLabels([
            "Company", "Contact", "Check-in", "Check-out",
            "Total Amount", "Status", "Actions"
        ])
        self.bookings_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.bookings_table)

    def setup_history_tab(self):
        """Set up the booking history tab"""
        layout = QVBoxLayout(self.history_tab)
        
        # Similar to active bookings tab but with additional filters for date range
        filter_layout = QHBoxLayout()
        
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("Search history...")
        
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        
        filter_layout.addWidget(self.history_search)
        filter_layout.addWidget(QLabel("From:"))
        filter_layout.addWidget(self.date_from)
        filter_layout.addWidget(QLabel("To:"))
        filter_layout.addWidget(self.date_to)
        
        layout.addLayout(filter_layout)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Company", "Contact", "Check-in", "Check-out",
            "Total Amount", "Status", "Completed Date", "Actions"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.history_table)

    def add_guest_booking(self):
        """Add a new guest booking to the company booking"""
        # This would open a dialog to add a guest booking
        # Similar to the individual booking process but linked to the company
        pass

    def save_company_booking(self):
        """Save the company booking"""
        try:
            # Create company booking object
            company_booking = CompanyBooking(
                company_id=str(uuid.uuid4()),
                company_name=self.company_name.text(),
                contact_person=self.contact_person.text(),
                contact_email=self.contact_email.text(),
                contact_phone=self.contact_phone.text(),
                billing_address=self.billing_address.toPlainText(),
                tax_id=self.tax_id.text(),
                payment_terms=self.payment_terms.currentText(),
                special_instructions=self.special_instructions.toPlainText()
            )
            
            # Validate the booking
            if not self.company_booking_service.validate_company_booking(company_booking):
                QMessageBox.warning(self, "Validation Error", "Please fill in all required fields correctly.")
                return
            
            # Save to database (implement this)
            # self.save_to_database(company_booking)
            
            # Generate invoice
            invoice_path = self.company_booking_service.generate_company_invoice(company_booking)
            
            QMessageBox.information(self, "Success", "Company booking saved successfully!")
            self.clear_form()
            
        except Exception as e:
            logger.error(f"Error saving company booking: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to save company booking: {str(e)}")

    def clear_form(self):
        """Clear all form fields"""
        self.company_name.clear()
        self.contact_person.clear()
        self.contact_email.clear()
        self.contact_phone.clear()
        self.billing_address.clear()
        self.tax_id.clear()
        self.payment_terms.setCurrentIndex(0)
        self.special_instructions.clear()
        self.guests_table.setRowCount(0)
        self.subtotal.clear()
        self.tax_amount.clear()
        self.total_amount.clear()

    def filter_bookings(self):
        """Filter the bookings table based on search and status"""
        # Implement filtering logic
        pass

    def update_totals(self):
        """Update the total amounts based on guest bookings"""
        try:
            subtotal = Decimal('0')
            for row in range(self.guests_table.rowCount()):
                room_total = Decimal(str(self.guests_table.item(row, 6).text() or '0'))
                additional_charges = Decimal(str(self.guests_table.item(row, 7).text() or '0'))
                subtotal += room_total + additional_charges
            
            tax_rate = Decimal('0.10')  # 10% tax rate
            tax_amount = subtotal * tax_rate
            total_amount = subtotal + tax_amount
            
            self.subtotal.setText(f"{float(subtotal):.2f}")
            self.tax_amount.setText(f"{float(tax_amount):.2f}")
            self.total_amount.setText(f"{float(total_amount):.2f}")
            
        except Exception as e:
            logger.error(f"Error updating totals: {str(e)}")
            QMessageBox.warning(self, "Error", "Failed to update totals.") 