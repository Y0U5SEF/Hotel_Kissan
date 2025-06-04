from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QStatusBar, QStackedWidget,
    QFrame, QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QDialogButtonBox, QLineEdit, QDoubleSpinBox, QHeaderView, QComboBox, QMessageBox
)
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt, QSize
from app.core.config_handler import app_config
from app.core.db import (
    get_hotel_settings, update_hotel_settings, get_room_rates, update_room_rate,
    get_services, add_service, update_service, delete_service,
    get_tax_rates, add_tax_rate, update_tax_rate, delete_tax_rate
)
from app.ui.dashboard import DashboardWidget
from app.ui.guests import GuestsWidget
from app.ui.check_in import CheckInWidget
from app.ui.reservations_module import ReservationsWidget
from app.ui.settings import SettingsWidget
from app.ui.room_management import RoomManagementWidget
from app.ui.company_accounts import CompanyAccountsWidget
from app.ui.styles import MAIN_STYLESHEET
from PyQt6.QtCore import pyqtSignal
from app.ui.reports import ReportsWidget
from app.core.auth import UserAuthenticator
from app.core.dev_config import DEV_MODE


class MainWindow(QMainWindow):
    """Main application window"""
    
    # Signal for guest deletion
    guest_deleted = pyqtSignal()
    # Signal for room status changes
    room_status_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.authenticator = UserAuthenticator()
        self.user_name = "Developer" if DEV_MODE else ""  # Initialize user name based on DEV_MODE
        self.setup_ui()
        self.load_styles()
        self.guests_widget.guest_data_changed.connect(self.checkin_widget.reload_guests_for_search)

        
    def setup_ui(self):
        # Set window properties
        self.setWindowTitle("HOTEL KISSAN AGDZ")
        self.setMinimumSize(1200, 800)
        
        # Set the stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)
        
        # Create central widget and main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Create top bar
        self.create_top_bar()
        
        # Create content area with horizontal layout
        content_area = QWidget()
        content_layout = QHBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Create navigation panel
        self.nav_panel = QWidget()
        self.nav_panel.setObjectName("navPanel")
        self.nav_panel.setFixedWidth(240)
        self.nav_layout = QVBoxLayout(self.nav_panel)
        self.nav_layout.setContentsMargins(0, 0, 0, 0)
        self.nav_layout.setSpacing(0)
        
        # Create stacked widget for content
        self.content_stack = QStackedWidget()
        
        # Create navigation buttons and add pages
        self.create_nav_buttons()
        
        # Add widgets to content layout
        content_layout.addWidget(self.nav_panel)
        content_layout.addWidget(self.content_stack)
        
        # Add content area to main layout
        self.main_layout.addWidget(content_area)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Connect guest deletion signal to all relevant widgets
        if hasattr(self, 'guests_widget'):
            self.guests_widget.guest_deleted.connect(self.on_guest_deleted)
        
        # Connect room status changed signal to room management widget
        if hasattr(self.room_management_widget, 'room_status_changed'):
            self.room_management_widget.room_status_changed.connect(self.on_room_status_changed)
        
    def create_top_bar(self):
        top_bar = QFrame()
        top_bar.setObjectName("topBar")
        top_bar.setFixedHeight(60)
        
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(20, 0, 20, 0)
        
        # Hotel name
        hotel_label = QLabel("Hotel Management System")
        hotel_label.setObjectName("hotelName")
        top_layout.addWidget(hotel_label)
        
        # Add stretch to push user info to the right
        top_layout.addStretch()
        
        # User info and logout
        user_widget = QWidget()
        user_layout = QHBoxLayout(user_widget)
        user_layout.setSpacing(15)
        user_layout.setContentsMargins(0, 0, 0, 0)
        
        # Person icon
        person_icon = QLabel()
        person_icon.setPixmap(QIcon("app/resources/icons/person_96px.png").pixmap(QSize(24, 24)))
        user_layout.addWidget(person_icon)
        
        # User name
        self.user_label = QLabel(self.user_name)
        self.user_label.setObjectName("userName")
        self.user_label.setStyleSheet("font-weight: bold;")
        user_layout.addWidget(self.user_label)
        
        # Logout button
        logout_btn = QPushButton()
        logout_btn.setObjectName("logoutButton")
        logout_btn.setIcon(QIcon("app/resources/icons/logout.png"))
        logout_btn.setIconSize(QSize(20, 20))
        logout_btn.setFixedSize(32, 32)
        logout_btn.setToolTip("Logout")
        logout_btn.clicked.connect(self.handle_logout)
        user_layout.addWidget(logout_btn)
        
        top_layout.addWidget(user_widget)
        
        self.main_layout.addWidget(top_bar)
        
    def create_nav_buttons(self):
        # Dashboard
        self.dashboard_widget = DashboardWidget()
        self.dashboard_widget.new_reservation_clicked.connect(self.on_new_reservation)
        self.dashboard_widget.check_in_clicked.connect(self.on_check_in)
        self.dashboard_widget.check_out_clicked.connect(self.on_check_out)
        self.content_stack.addWidget(self.dashboard_widget)
        self.create_nav_button("Dashboard", ":/icons/dashboard.png", 0)
        
        # Check-ins
        self.checkin_widget = CheckInWidget()
        self.content_stack.addWidget(self.checkin_widget)
        self.create_nav_button("Check-ins", ":/icons/checkin.png", 1)
        
        # Reservations
        self.reservations_widget = ReservationsWidget()
        self.content_stack.addWidget(self.reservations_widget)
        self.create_nav_button("Reservations", ":/icons/booking.png", 2)
        
        # Guests
        self.guests_widget = GuestsWidget()
        self.guests_widget.guest_selected.connect(self.on_guest_selected)
        self.guests_widget.check_in_requested.connect(self.on_check_in)
        self.guests_widget.check_out_requested.connect(self.on_check_out)
        self.content_stack.addWidget(self.guests_widget)
        self.create_nav_button("Guests", ":/icons/guests.png", 3)
        
        # Rooms
        self.room_management_widget = RoomManagementWidget()
        self.content_stack.addWidget(self.room_management_widget)
        self.create_nav_button("Rooms", ":/icons/available_rooms.png", 4)
        
        # Company Accounts
        self.company_accounts_widget = CompanyAccountsWidget()
        self.content_stack.addWidget(self.company_accounts_widget)
        self.create_nav_button("Company Accounts", ":/icons/company.png", 5)
        
        # Services
        self.services_widget = QWidget()
        self.setup_services_widget()
        self.content_stack.addWidget(self.services_widget)
        self.create_nav_button("Services", ":/icons/star.png", 6)
        
        # Reports
        reports_widget = ReportsWidget()
        self.content_stack.addWidget(reports_widget)
        self.create_nav_button("Reports", ":/icons/reports.png", 7)
        
        # Add stretch to push settings button to bottom
        self.nav_layout.addStretch()
        
        # Settings (at bottom)
        self.settings_widget = SettingsWidget()
        self.content_stack.addWidget(self.settings_widget)
        self.create_nav_button("Settings", ":/icons/settings.png", 8)
        
    def create_nav_button(self, text, icon_path, index):
        button = QPushButton()
        button.setObjectName("sidebarButton")
        button.setCheckable(True)
        button.setFixedHeight(50)
        
        # Create horizontal layout for icon and text
        layout = QHBoxLayout(button)
        layout.setContentsMargins(15, 5, 15, 5)
        layout.setSpacing(15)
        
        # Add icon
        icon_label = QLabel()
        icon_label.setPixmap(QIcon(icon_path).pixmap(32, 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(icon_label)
        
        # Add text with larger font size
        text_label = QLabel(text)
        font = text_label.font()
        font.setPointSize(14)  # Increase font size to 11pt
        text_label.setFont(font)
        text_label.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        layout.addWidget(text_label)
        
        # Add stretch to push icon and text to the left
        layout.addStretch()
        
        # Connect button click
        button.clicked.connect(lambda: self.on_nav_button_clicked(index))
        
        self.nav_layout.addWidget(button)
        
    def on_nav_button_clicked(self, index):
        # Uncheck all buttons
        for i in range(self.nav_layout.count() - 1):  # -1 to exclude the stretch
            button = self.nav_layout.itemAt(i).widget()
            if isinstance(button, QPushButton):
                button.setChecked(False)
        
        # Check clicked button
        button = self.nav_layout.itemAt(index).widget()
        if isinstance(button, QPushButton):
            button.setChecked(True)
        
        # Switch to corresponding page
        self.content_stack.setCurrentIndex(index)
        
    def on_new_reservation(self):
        """Handle new reservation button click"""
        # Switch to Reservations module and select New Reservation tab
        self.content_stack.setCurrentIndex(2)  # Reservations module index
        if hasattr(self, 'reservations_widget'):
            self.reservations_widget.tab_widget.setCurrentIndex(2)  # New Reservation tab index
        self.status_bar.showMessage("Creating new reservation...")

    def on_check_in(self):
        """Handle check-in button click"""
        # Switch to Check-ins module and select New Check-In tab
        self.content_stack.setCurrentIndex(1)  # Check-ins module index
        if hasattr(self, 'checkin_widget'):
            self.checkin_widget.tab_widget.setCurrentIndex(1)  # New Check-In tab index
        self.status_bar.showMessage("Processing check-in...")

    def on_check_out(self):
        """Handle check-out button click"""
        # Switch to Check-ins module and select Check-Out tab
        self.content_stack.setCurrentIndex(1)  # Check-ins module index
        if hasattr(self, 'checkin_widget'):
            self.checkin_widget.tab_widget.setCurrentIndex(2)  # Check-Out tab index
        self.status_bar.showMessage("Processing check-out...")
        
    def on_guest_selected(self, guest_data):
        """Handle guest selection"""
        self.status_bar.showMessage(f"Selected guest: {guest_data.get('first_name', '')} {guest_data.get('last_name', '')}")
        
    def on_guest_deleted(self):
        """Handle guest deletion"""
        self.guest_deleted.emit()
        
    def on_room_status_changed(self):
        """Handle room status changes"""
        self.room_status_changed.emit()
        
    def load_styles(self):
        """Load the application styles"""
        self.setStyleSheet(MAIN_STYLESHEET)

    def setup_services_widget(self):
        layout = QVBoxLayout(self.services_widget)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Services Table
        self.services_table = QTableWidget()
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels(["Service Name", "Default Price", "Unit", "Actions"])
        self.services_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.services_table.verticalHeader().setDefaultSectionSize(50)  # Make rows thick


        self.services_table.setObjectName("dataTable")
        layout.addWidget(self.services_table)

        # Add Service button
        add_btn = QPushButton("Add Service")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self.add_service)
        layout.addWidget(add_btn)

        # Load existing services
        self.load_services()

    def load_services(self):
        self.services_table.setRowCount(0)
        services = get_services()
        for service in services:
            row = self.services_table.rowCount()
            self.services_table.insertRow(row)
            self.services_table.setItem(row, 0, QTableWidgetItem(service['name']))
            self.services_table.setItem(row, 1, QTableWidgetItem(f"MAD {service['default_price']:.2f}"))
            self.services_table.setItem(row, 2, QTableWidgetItem(service['unit']))
            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("actionButton")
            edit_btn.clicked.connect(lambda _, s=service: self.edit_service(s))
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("actionButton")
            delete_btn.clicked.connect(lambda _, s=service: self.delete_service(s))
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            self.services_table.setCellWidget(row, 3, actions_widget)

    def add_service(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Service")
        dialog.setFixedSize(400, 200)  # Set fixed size for the dialog
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        name = QLineEdit()
        form.addRow("Service Name:", name)
        price = QDoubleSpinBox()
        price.setRange(0, 10000)
        price.setDecimals(2)
        price.setPrefix("MAD ")
        form.addRow("Default Price:", price)
        unit = QComboBox()
        unit.addItems(["per item", "per kg", "per hour", "per day", "per service"])
        unit.setEditable(True)
        form.addRow("Unit:", unit)
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        # Set object names for the buttons
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setObjectName("dialogOkButton")
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setObjectName("dialogCancelButton")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addLayout(form)
        layout.addWidget(buttons)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            service = {
                'name': name.text(),
                'default_price': price.value(),
                'unit': unit.currentText()
            }
            add_service(service)
            self.load_services()

    def edit_service(self, service):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Service")
        dialog.setFixedSize(400, 200)  # Set fixed size for the dialog
        layout = QVBoxLayout(dialog)
        form = QFormLayout()
        name = QLineEdit(service['name'])
        form.addRow("Service Name:", name)
        price = QDoubleSpinBox()
        price.setRange(0, 10000)
        price.setDecimals(2)
        price.setPrefix("MAD ")
        price.setValue(service['default_price'])
        form.addRow("Default Price:", price)
        unit = QComboBox()
        unit.addItems(["per item", "per kg", "per hour", "per day", "per service"])
        unit.setEditable(True)
        unit.setCurrentText(service['unit'])
        form.addRow("Unit:", unit)
        
        # Create button container
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 10, 0, 0)
        
        # Create OK and Cancel buttons
        ok_button = QPushButton("OK")
        ok_button.setObjectName("dialogOkButton")
        ok_button.clicked.connect(dialog.accept)
        
        cancel_button = QPushButton("Cancel")
        cancel_button.setObjectName("dialogCancelButton")
        cancel_button.clicked.connect(dialog.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        
        layout.addLayout(form)
        layout.addWidget(button_container)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_service = {
                'name': name.text(),
                'default_price': price.value(),
                'unit': unit.currentText()
            }
            update_service(service['id'], updated_service)
            self.load_services()

    def delete_service(self, service):
        delete_service(service['id'])
        self.load_services()

    def handle_logout(self):
        """Handle logout button click"""
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            'Confirm Logout',
            'Are you sure you want to logout?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.authenticator.logout()
            self.hide()  # Hide instead of close to keep the window instance alive
            
            # Show login form again
            from app.ui.login_form import LoginForm
            self.login_form = LoginForm()
            self.login_form.login_successful.connect(self.on_login_successful)
            self.login_form.show()
            
    def on_login_successful(self, full_name):
        """Handle successful login"""
        self.user_name = full_name
        self.user_label.setText(full_name.upper())
        self.show()  # Show the main window again
        self.login_form = None  # Clear the reference to the login form
