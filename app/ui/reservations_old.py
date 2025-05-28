from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDateEdit, QCalendarWidget, QFormLayout, QStackedWidget, QCompleter, QGridLayout, QMessageBox, QFrame, QSpinBox, QTextEdit, QProgressBar
)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from app.core.db import get_all_guests, get_all_rooms, update_room, get_guest_id_by_name, insert_checkin, get_all_checkins
from fpdf import FPDF
import uuid
from datetime import datetime
import os

class CheckInWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.transaction_id = str(uuid.uuid4())[:8]  # Initialize transaction ID
        self.checkin_id = str(uuid.uuid4())[:8]  # Initialize check-in ID
        self.checkin_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.selected_room_id = None  # Ensure this is always initialized
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Check-In")
        title_label.setObjectName("pageTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Tabs for different features
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
            }
            QTabBar::tab {
                font-size: 14px;
                padding: 10px 20px;
                margin-right: 5px;
                background-color: #f5f6fa;
                border: none;
                border-radius: 5px;
            }
            QTabBar::tab:selected {
                background-color: #2980b9;
                color: white;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e9ecef;
            }
        """)

        # Check-In List Tab
        self.checkin_list_tab = QWidget()
        self.setup_checkin_list_tab()
        self.tab_widget.addTab(self.checkin_list_tab, QIcon("app/resources/icons/list.png"), "Check-In List")

        # New Check-In Tab
        self.new_checkin_tab = QWidget()
        self.setup_new_checkin_tab()
        self.tab_widget.addTab(self.new_checkin_tab, QIcon("app/resources/icons/add_checkin.png"), "New Check-In")

        main_layout.addWidget(self.tab_widget)

    def setup_checkin_list_tab(self):
        layout = QVBoxLayout(self.checkin_list_tab)
        # Search and filter bar
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by guest, check-in #, date...")
        self.search_input.setObjectName("searchInput")
        filter_layout.addWidget(self.search_input)
        
        self.filter_arrival = QDateEdit()
        self.filter_arrival.setCalendarPopup(True)
        self.filter_arrival.setDisplayFormat("yyyy-MM-dd")
        self.filter_arrival.setObjectName("dateInput")
        filter_layout.addWidget(self.filter_arrival)
        
        self.filter_departure = QDateEdit()
        self.filter_departure.setCalendarPopup(True)
        self.filter_departure.setDisplayFormat("yyyy-MM-dd")
        self.filter_departure.setObjectName("dateInput")
        filter_layout.addWidget(self.filter_departure)
        
        self.filter_room_type = QComboBox()
        self.filter_room_type.addItems(["All Room Types", "Single", "Double", "Suite", "Deluxe"])
        self.filter_room_type.setObjectName("filterCombo")
        filter_layout.addWidget(self.filter_room_type)
        
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("actionButton")
        refresh_btn.clicked.connect(self.load_checkin_list)
        filter_layout.addWidget(refresh_btn)
        
        layout.addWidget(filter_frame)
        
        # Check-in table
        self.checkin_table = QTableWidget()
        self.checkin_table.setAlternatingRowColors(True)
        self.checkin_table.setColumnCount(7)
        self.checkin_table.setHorizontalHeaderLabels([
            "Check-In #", "Guest Name", "Arrival", "Departure", "Room", "Status", "Actions"
        ])
        self.checkin_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.checkin_table.setObjectName("dataTable")
        layout.addWidget(self.checkin_table)

    def setup_new_checkin_tab(self):
        layout = QVBoxLayout(self.new_checkin_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Progress indicator
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QHBoxLayout(progress_frame)
        
        steps = ["Guest Details", "Stay Details", "Room Selection", "Payment", "Confirmation"]
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
        
        # Guest search with modern styling
        search_frame = QFrame()
        search_frame.setObjectName("searchFrame")
        search_layout = QVBoxLayout(search_frame)
        
        search_label = QLabel("Select Guest")
        search_label.setObjectName("sectionTitle")
        search_layout.addWidget(search_label)
        
        # Create a container for the search and dropdown
        search_container = QWidget()
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(0, 0, 0, 0)
        
        # Search input
        self.guest_search = QLineEdit()
        self.guest_search.setPlaceholderText("Search guest...")
        self.guest_search.setObjectName("searchInput")
        self.guest_search.textChanged.connect(self.filter_guest_dropdown)
        search_container_layout.addWidget(self.guest_search)
        
        # Guest dropdown
        self.guest_dropdown = QComboBox()
        self.guest_dropdown.setObjectName("guestDropdown")
        self.guest_dropdown.setMinimumWidth(200)
        self.guest_dropdown.currentIndexChanged.connect(self.on_guest_selected)
        search_container_layout.addWidget(self.guest_dropdown)
        
        search_layout.addWidget(search_container)
        s1_layout.addWidget(search_frame)
        
        # Guest details form
        details_frame = QFrame()
        details_frame.setObjectName("detailsFrame")
        details_layout = QFormLayout(details_frame)
        details_layout.setSpacing(15)
        
        self.guest_first_name = QLineEdit()
        self.guest_first_name.setReadOnly(True)
        self.guest_first_name.setObjectName("readOnlyInput")
        self.guest_last_name = QLineEdit()
        self.guest_last_name.setReadOnly(True)
        self.guest_last_name.setObjectName("readOnlyInput")
        self.guest_email = QLineEdit()
        self.guest_email.setReadOnly(True)
        self.guest_email.setObjectName("readOnlyInput")
        self.guest_phone = QLineEdit()
        self.guest_phone.setReadOnly(True)
        self.guest_phone.setObjectName("readOnlyInput")
        
        details_layout.addRow("First Name:", self.guest_first_name)
        details_layout.addRow("Last Name:", self.guest_last_name)
        details_layout.addRow("Email:", self.guest_email)
        details_layout.addRow("Phone:", self.guest_phone)
        
        s1_layout.addWidget(details_frame)
        self.wizard.addWidget(step1)

        # Step 2: Stay Details
        step2 = QWidget()
        s2_layout = QVBoxLayout(step2)
        s2_layout.setContentsMargins(40, 20, 40, 20)
        
        # Date selection with split calendar
        date_frame = QFrame()
        date_frame.setObjectName("dateFrame")
        date_layout = QHBoxLayout(date_frame)
        date_layout.setSpacing(40)
        
        # Arrival date
        arrival_widget = QWidget()
        arrival_layout = QVBoxLayout(arrival_widget)
        arrival_label = QLabel("Arrival Date")
        arrival_label.setObjectName("sectionTitle")
        arrival_layout.addWidget(arrival_label)
        
        self.arrival_date = QCalendarWidget()
        self.arrival_date.setMinimumDate(QDate.currentDate())
        self.arrival_date.setMinimumWidth(350)
        self.arrival_date.setMinimumHeight(300)
        arrival_layout.addWidget(self.arrival_date)
        
        # Departure date
        departure_widget = QWidget()
        departure_layout = QVBoxLayout(departure_widget)
        departure_label = QLabel("Departure Date")
        departure_label.setObjectName("sectionTitle")
        departure_layout.addWidget(departure_label)
        
        self.departure_date = QCalendarWidget()
        self.departure_date.setMinimumDate(QDate.currentDate().addDays(1))
        self.departure_date.setMinimumWidth(350)
        self.departure_date.setMinimumHeight(300)
        departure_layout.addWidget(self.departure_date)
        
        date_layout.addWidget(arrival_widget, 1)
        date_layout.addWidget(departure_widget, 1)
        s2_layout.addWidget(date_frame)
        
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
            "Vacant": "#27ae60",
            "Occupied": "#c0392b",
            "Dirty": "#e67e22",
            "Clean": "#2980b9",
            "Out of Order": "#7f8c8d",
            "Reserved": "#8e44ad"
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

        # Step 4: Payment
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
        self.payment_method.setObjectName("paymentMethod")
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
        self.payment_amount.setObjectName("amountInput")
        
        self.total_paid = QLineEdit()
        self.total_paid.setPlaceholderText("Enter amount paid")
        self.total_paid.setObjectName("amountInput")
        
        self.amount_due = QLineEdit()
        self.amount_due.setReadOnly(True)
        self.amount_due.setText("0.00")
        self.amount_due.setObjectName("amountInput")
        
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

        # Step 5: Confirmation
        step5 = QWidget()
        s5_layout = QVBoxLayout(step5)
        s5_layout.setContentsMargins(40, 20, 40, 20)
        
        confirmation_frame = QFrame()
        confirmation_frame.setObjectName("confirmationFrame")
        confirmation_layout = QVBoxLayout(confirmation_frame)
        
        # Success message
        success_label = QLabel("Check-In Confirmed!")
        success_label.setObjectName("successTitle")
        success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        confirmation_layout.addWidget(success_label)
        
        # Confirmation details
        self.confirmation_label = QLabel()
        self.confirmation_label.setObjectName("confirmationDetails")
        self.confirmation_label.setWordWrap(True)
        confirmation_layout.addWidget(self.confirmation_label)
        
        # Action buttons
        actions_widget = QWidget()
        actions_layout = QHBoxLayout(actions_widget)
        
        self.print_receipt_btn = QPushButton("Print Receipt")
        self.print_receipt_btn.setObjectName("actionButton")
        self.print_receipt_btn.clicked.connect(self.print_receipt)
        
        self.email_receipt_btn = QPushButton("Email Receipt")
        self.email_receipt_btn.setObjectName("actionButton")
        
        actions_layout.addWidget(self.print_receipt_btn)
        actions_layout.addWidget(self.email_receipt_btn)
        
        confirmation_layout.addWidget(actions_widget)
        
        s5_layout.addWidget(confirmation_frame)
        self.wizard.addWidget(step5)

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

    def update_wizard_ui(self):
        step = self.wizard.currentIndex()
        steps = [
            "Guest Details", "Stay Details", "Room Selection", "Payment", "Confirmation"
        ]
        
        # Reset all steps to default style
        for i, (number_label, name_label) in enumerate(self.progress_labels):
            if i < step:  # Completed steps
                number_label.setStyleSheet("""
                    QLabel {
                        background-color: #27ae60;
                        color: white;
                        border-radius: 15px;
                        padding: 5px;
                        font-weight: bold;
                        font-size: 16px;
                    }
                """)
                name_label.setStyleSheet("color: #27ae60; font-weight: bold;")
            elif i == step:  # Current step
                number_label.setStyleSheet("""
                    QLabel {
                        background-color: #2980b9;
                        color: white;
                        border-radius: 15px;
                        padding: 5px;
                        font-weight: bold;
                        font-size: 16px;
                    }
                """)
                name_label.setStyleSheet("color: #2980b9; font-weight: bold;")
            else:  # Future steps
                number_label.setStyleSheet("""
                    QLabel {
                        background-color: #bdc3c7;
                        color: white;
                        border-radius: 15px;
                        padding: 5px;
                        font-size: 16px;
                    }
                """)
                name_label.setStyleSheet("color: #7f8c8d;")
            
            name_label.setText(f"Step {i+1} of 5: {steps[i]}")
        
        self.back_btn.setEnabled(step > 0)
        self.next_btn.setVisible(step < 4)
        self.finish_btn.setVisible(step == 4)

    def next_step(self):
        # Require guest selection/input in step 1
        if self.wizard.currentIndex() == 0:
            if not self.guest_first_name.text().strip() or not self.guest_last_name.text().strip():
                QMessageBox.warning(self, "Guest Required", "Please select or enter a guest's first and last name before proceeding.")
                return
        if self.wizard.currentIndex() < self.wizard.count() - 1:
            self.wizard.setCurrentIndex(self.wizard.currentIndex() + 1)
            if self.wizard.currentIndex() == 0:
                self.reload_guests_for_search()
            if self.wizard.currentIndex() == 2:  # Step 3: Room Selection
                self.load_room_grid()
            if self.wizard.currentIndex() == 3:  # Step 4: Payment
                self.update_payment_amount()
            if self.wizard.currentIndex() == 4:  # Step 5: Confirmation
                self.show_confirmation_details()
            self.update_wizard_ui()

    def show_confirmation_details(self):
        # Generate check-in and transaction IDs if not already generated
        if not hasattr(self, 'checkin_id'):
            self.checkin_id = str(uuid.uuid4())[:8]
            self.transaction_id = str(uuid.uuid4())[:8]
            self.checkin_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        
        # Prepare summary
        guest_name = f"{self.guest_first_name.text()} {self.guest_last_name.text()}"
        guest_email = self.guest_email.text()
        guest_phone = self.guest_phone.text()
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
        payment_status = self.payment_status_label.text()
        
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
        &nbsp;&nbsp;Payment Status: {payment_status}<br>
        </div>
        <br><b style='color:#2980b9;'>Check-in has been successfully completed!</b>
        """
        self.confirmation_label.setText(message)
        
        # Print Receipt button
        if not hasattr(self, 'print_receipt_btn'):
            self.print_receipt_btn = QPushButton("Print Receipt")
            self.print_receipt_btn.clicked.connect(self.print_receipt)
            self.confirmation_label.parentWidget().layout().addWidget(self.print_receipt_btn)
        self.print_receipt_btn.setVisible(True)

    def prev_step(self):
        if self.wizard.currentIndex() > 0:
            self.wizard.setCurrentIndex(self.wizard.currentIndex() - 1)
            if self.wizard.currentIndex() == 2:  # Step 3: Room Selection
                self.load_room_grid()
            self.update_wizard_ui()

    def cancel_wizard(self):
        self.wizard.setCurrentIndex(0)
        self.update_wizard_ui()

    def finish_wizard(self):
        # Collect all data and process the check-in
        if self.selected_room_id:
            # Fetch current room data and update only the status
            rooms = get_all_rooms()
            room_info = next((r for r in rooms if r['id'] == self.selected_room_id), None)
            if room_info:
                room_info = dict(room_info)  # Make a copy
                room_info['status'] = 'Occupied'
                update_room(self.selected_room_id, room_info)
        
        # Get guest ID
        guest_id = get_guest_id_by_name(self.guest_first_name.text(), self.guest_last_name.text())
        
        # Save check-in to database
        checkin_data = {
            'checkin_id': self.checkin_id,
            'transaction_id': self.transaction_id,
            'guest_id': guest_id,
            'room_id': self.selected_room_id,
            'checkin_date': self.checkin_date,
            'arrival_date': self.arrival_date.selectedDate().toString('yyyy-MM-dd'),
            'departure_date': self.departure_date.selectedDate().toString('yyyy-MM-dd'),
            'num_guests': self.num_guests.value(),
            'total_paid': float(self.total_paid.text() or 0),
            'amount_due': float(self.amount_due.text() or 0),
            'payment_method': self.payment_method.currentText(),
            'payment_status': self.payment_status_label.text()
        }
        insert_checkin(checkin_data)
        
        # Generate receipt
        rooms = get_all_rooms()
        room_info = next((r for r in rooms if r['id'] == self.selected_room_id), {})
        room_type = room_info.get('type', '')
        room_number = room_info.get('number', '')
        guest_name = f"{self.guest_first_name.text()} {self.guest_last_name.text()}"
        self.generate_receipt(
            self.transaction_id,
            self.checkin_id,
            self.checkin_date,
            guest_name,
            self.arrival_date.selectedDate().toString('yyyy-MM-dd'),
            self.departure_date.selectedDate().toString('yyyy-MM-dd'),
            room_type,
            room_number,
            self.total_paid.text(),
            self.amount_due.text(),
            self.payment_method.currentText()
        )
        
        # Reset wizard to step 1 and clear fields for new check-in
        self.reset_wizard_fields()
        self.wizard.setCurrentIndex(0)
        self.update_wizard_ui()
        if hasattr(self, 'print_receipt_btn'):
            self.print_receipt_btn.setVisible(False)
            
        # Refresh check-in list
        self.load_checkin_list()

    def reset_wizard_fields(self):
        # Clear all fields in the wizard for a new check-in
        self.guest_search.clear()
        self.guest_dropdown.clear()
        self.guest_first_name.clear()
        self.guest_last_name.clear()
        self.guest_email.clear()
        self.guest_phone.clear()
        self.arrival_date.setSelectedDate(QDate.currentDate())
        self.departure_date.setSelectedDate(QDate.currentDate().addDays(1))
        self.num_guests.setValue(1)
        self.selected_room_id = None
        self.load_room_grid()
        self.payment_method.setCurrentIndex(0)
        self.payment_amount.setText("0.00")
        self.total_paid.clear()
        self.amount_due.setText("0.00")
        self.payment_status_label.setText("Pending")
        self.payment_progress.setValue(0)
        self.confirmation_label.setText("")

    def generate_receipt(self, transaction_id, checkin_id, checkin_date, guest_name, arrival, departure, room_type, room_number, total_paid, amount_due, payment_method):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Hotel Check-In Receipt", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Check-In Number: {checkin_id}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Transaction ID: {transaction_id}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Date: {checkin_date}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Guest: {guest_name}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Room: {room_type} #{room_number}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Arrival: {arrival}  Departure: {departure}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Total Paid: MAD {total_paid}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Amount Due: MAD {amount_due}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Payment Method: {payment_method}", ln=True, align="C")
        pdf.output("receipt.pdf")

    def print_receipt(self):
        # Open the generated PDF receipt
        os.startfile("receipt.pdf")

    def filter_guest_dropdown(self):
        """Filter the guest dropdown based on search text"""
        search_text = self.guest_search.text().lower()
        self.guest_dropdown.clear()
        
        # Add filtered guests to dropdown
        for guest in self.guests_data:
            full_name = f"{guest['first_name']} {guest['last_name']}"
            if search_text in full_name.lower():
                self.guest_dropdown.addItem(full_name, guest)

    def on_guest_selected(self, index):
        """Handle guest selection from dropdown"""
        if index >= 0:
            guest = self.guest_dropdown.currentData()
            if guest:
                self.guest_first_name.setText(guest['first_name'])
                self.guest_last_name.setText(guest['last_name'])
                self.guest_email.setText(guest.get('email') or "")
                phone = f"{guest.get('phone_code') or ''} {guest.get('phone_number') or ''}".strip()
                self.guest_phone.setText(phone)

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
            "Vacant": "#27ae60",
            "Occupied": "#c0392b",
            "Dirty": "#e67e22",
            "Clean": "#2980b9",
            "Out of Order": "#7f8c8d"
        }.get(status, "#bdc3c7")

    def select_room(self, room_id):
        self.selected_room_id = room_id
        self.load_room_grid()  # Refresh to update selection

    def showEvent(self, event):
        super().showEvent(event)
        self.reload_guests_for_search()
        self.load_checkin_list()  # Load check-ins when widget is shown

    def update_amount_due(self):
        try:
            total = float(self.payment_amount.text())
            paid = float(self.total_paid.text() or 0)
            due = max(total - paid, 0)
            self.amount_due.setText(f"{due:.2f}")
        except Exception:
            self.amount_due.setText(self.payment_amount.text())
        self.update_payment_status()

    def update_payment_status(self):
        try:
            total = float(self.payment_amount.text())
            paid = float(self.total_paid.text() or 0)
            if self.total_paid.text().strip() == "":
                status = "Pending"
            elif paid == total:
                status = "Completed"
            elif 0 < paid < total:
                status = "Partially Paid"
            else:
                status = "Pending"
        except Exception:
            status = "Pending"
        self.payment_status_label.setText(status)
        self.payment_progress.setValue(int(paid / total * 100) if total > 0 else 0)
        if status == "Completed":
            rooms = get_all_rooms()
            room_info = next((r for r in rooms if r['id'] == self.selected_room_id), {})
            room_type = room_info.get('type', '')
            room_number = room_info.get('number', '')
            guest_name = f"{self.guest_first_name.text()} {self.guest_last_name.text()}"
            self.generate_receipt(
                self.transaction_id,
                self.checkin_id,
                self.checkin_date,
                guest_name,
                self.arrival_date.selectedDate().toString('yyyy-MM-dd'),
                self.departure_date.selectedDate().toString('yyyy-MM-dd'),
                room_type,
                room_number,
                self.total_paid.text(),
                self.amount_due.text(),
                self.payment_method.currentText()
            )

    def update_payment_amount(self):
        # Placeholder: set payment amount to a fixed value or calculate from room selection
        self.payment_amount.setText("100.00")
        self.update_amount_due()

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
            self.checkin_table.setItem(row, 5, QTableWidgetItem(checkin['payment_status']))
            
            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)
            
            view_btn = QPushButton("View")
            view_btn.setObjectName("actionButton")
            view_btn.setFixedWidth(80)
            view_btn.clicked.connect(lambda _, c=checkin: self.view_checkin(c))
            
            actions_layout.addWidget(view_btn)
            actions_layout.addStretch()
            self.checkin_table.setCellWidget(row, 6, actions_widget)

    def view_checkin(self, checkin):
        """View details of a specific check-in"""
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
        &nbsp;&nbsp;Payment Status: {checkin['payment_status']}<br>
        </div>
        """
        QMessageBox.information(self, "Check-In Details", message) 