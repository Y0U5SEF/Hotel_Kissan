from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QLineEdit, QComboBox,
    QDateEdit, QTextEdit, QTabWidget, QFormLayout, QCheckBox,
    QMessageBox, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QIcon
from app.core.db import insert_guest, get_all_guests, update_guest, delete_guest

class GuestProfileDialog(QDialog):
    """Dialog for adding/editing guest profiles"""
    def __init__(self, parent=None, guest_data=None):
        super().__init__(parent)
        self.guest_data = guest_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Edit Guest" if self.guest_data else "Add New Guest")
        self.setMinimumWidth(800)
        
        layout = QVBoxLayout(self)
        
        # --- Basic Information Section ---
        basic_info_frame = QFrame()
        basic_info_layout = QVBoxLayout(basic_info_frame)
        basic_info_label = QLabel("Basic Information")
        basic_info_label.setStyleSheet("font-weight: bold; margin-bottom: 8px;")
        basic_info_layout.addWidget(basic_info_label)
        
        form_layout = QFormLayout()

        # Last Name
        self.last_name = QLineEdit()
        self.last_name.setObjectName("uppercase")
        self.last_name.setPlaceholderText("Enter last name")
        form_layout.addRow("Last Name *:", self.last_name)
        
        # First Name
        self.first_name = QLineEdit()
        self.first_name.setObjectName("uppercase")
        self.first_name.setPlaceholderText("Enter first name")
        form_layout.addRow("First Name *:", self.first_name)
        
        # ID Type
        self.id_type = QComboBox()
        self.id_type.addItems(["Passport", "National ID", "Driver's License", "Other"])
        form_layout.addRow("ID Type:", self.id_type)
        
        # ID Number
        self.id_number = QLineEdit()
        self.id_number.setPlaceholderText("Enter ID number")
        form_layout.addRow("ID Number:", self.id_number)
        
        # Date of Birth
        self.dob = QDateEdit()
        self.dob.setCalendarPopup(True)
        self.dob.setDate(QDate.currentDate().addYears(-18))
        form_layout.addRow("Date of Birth:", self.dob)
        
        # Nationality
        self.nationality = QComboBox()
        self.nationality.setEditable(True)
        self.nationality.addItems([
            "Afghanistan", "Albania", "Algeria", "Andorra", "Angola", "Antigua and Barbuda", "Argentina",
            "Armenia", "Australia", "Austria", "Azerbaijan", "Bahamas", "Bahrain", "Bangladesh", "Barbados",
            "Belarus", "Belgium", "Belize", "Benin", "Bhutan", "Bolivia", "Bosnia and Herzegovina",
            "Botswana", "Brazil", "Brunei", "Bulgaria", "Burkina Faso", "Burundi", "Cabo Verde",
            "Cambodia", "Cameroon", "Canada", "Central African Republic", "Chad", "Chile", "China",
            "Colombia", "Comoros", "Congo", "Costa Rica", "Croatia", "Cuba", "Cyprus", "Czech Republic",
            "Denmark", "Djibouti", "Dominica", "Dominican Republic", "Ecuador", "Egypt", "El Salvador",
            "Equatorial Guinea", "Eritrea", "Estonia", "Eswatini", "Ethiopia", "Fiji", "Finland",
            "France", "Gabon", "Gambia", "Georgia", "Germany", "Ghana", "Greece", "Grenada", "Guatemala",
            "Guinea", "Guinea-Bissau", "Guyana", "Haiti", "Honduras", "Hungary", "Iceland", "India",
            "Indonesia", "Iran", "Iraq", "Ireland", "Israel", "Italy", "Jamaica", "Japan", "Jordan",
            "Kazakhstan", "Kenya", "Kiribati", "Korea, North", "Korea, South", "Kosovo", "Kuwait",
            "Kyrgyzstan", "Laos", "Latvia", "Lebanon", "Lesotho", "Liberia", "Libya", "Liechtenstein",
            "Lithuania", "Luxembourg", "Madagascar", "Malawi", "Malaysia", "Maldives", "Mali", "Malta",
            "Marshall Islands", "Mauritania", "Mauritius", "Mexico", "Micronesia", "Moldova", "Monaco",
            "Mongolia", "Montenegro", "Morocco", "Mozambique", "Myanmar", "Namibia", "Nauru", "Nepal",
            "Netherlands", "New Zealand", "Nicaragua", "Niger", "Nigeria", "North Macedonia", "Norway",
            "Oman", "Pakistan", "Palau", "Palestine", "Panama", "Papua New Guinea", "Paraguay", "Peru",
            "Philippines", "Poland", "Portugal", "Qatar", "Romania", "Russia", "Rwanda", "Saint Kitts and Nevis",
            "Saint Lucia", "Saint Vincent and the Grenadines", "Samoa", "San Marino", "Sao Tome and Principe",
            "Saudi Arabia", "Senegal", "Serbia", "Seychelles", "Sierra Leone", "Singapore", "Slovakia",
            "Slovenia", "Solomon Islands", "Somalia", "South Africa", "South Sudan", "Spain", "Sri Lanka",
            "Sudan", "Suriname", "Sweden", "Switzerland", "Syria", "Taiwan", "Tajikistan", "Tanzania",
            "Thailand", "Timor-Leste", "Togo", "Tonga", "Trinidad and Tobago", "Tunisia", "Turkey",
            "Turkmenistan", "Tuvalu", "Uganda", "Ukraine", "United Arab Emirates", "United Kingdom",
            "United States", "Uruguay", "Uzbekistan", "Vanuatu", "Vatican City", "Venezuela", "Vietnam",
            "Yemen", "Zambia", "Zimbabwe"
        ])
        form_layout.addRow("Nationality:", self.nationality)
        
        # Phone
        phone_layout = QHBoxLayout()
        self.phone_code = QLineEdit()
        self.phone_code.setPlaceholderText("Code")
        self.phone_code.setFixedWidth(60)
        self.phone_number = QLineEdit()
        self.phone_number.setPlaceholderText("Phone number")
        phone_layout.addWidget(self.phone_code)
        phone_layout.addWidget(self.phone_number)
        form_layout.addRow("Phone:", phone_layout)
        
        # Email
        self.email = QLineEdit()
        self.email.setPlaceholderText("Enter email address")
        form_layout.addRow("Email:", self.email)
        
        # Company
        self.company = QComboBox()
        self.company.setEditable(True)
        self.company.setPlaceholderText("Select or enter company name")
        self.populate_companies()
        form_layout.addRow("Company:", self.company)
        
        basic_info_layout.addLayout(form_layout)
        layout.addWidget(basic_info_frame)
        
        # --- Additional Information Section ---
        additional_frame = QFrame()
        additional_layout = QVBoxLayout(additional_frame)
        
        additional_label = QLabel("Additional Information")
        additional_label.setStyleSheet("font-weight: bold; margin-bottom: 8px;")
        additional_layout.addWidget(additional_label)
        
        add_form = QFormLayout()
        
        # Address
        self.address = QLineEdit()
        self.address.setPlaceholderText("Enter full address")
        add_form.addRow("Address:", self.address)
        
        # VIP Status
        self.vip_status = QComboBox()
        self.vip_status.addItems(["Regular", "VIP"])
        add_form.addRow("VIP Status:", self.vip_status)
        
        # Special Preferences
        self.preferences = QLineEdit()
        self.preferences.setPlaceholderText("e.g., smoking/non-smoking, floor preference, allergies")
        add_form.addRow("Special Preferences:", self.preferences)
        
        additional_layout.addLayout(add_form)
        layout.addWidget(additional_frame)
        
        # --- Dialog Buttons ---
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        # Set object names for the buttons
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Save)
        ok_button.setObjectName("dialogOkButton")
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setObjectName("dialogCancelButton")
        
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Load existing data if editing
        if self.guest_data:
            self.load_guest_data()
    
    def populate_companies(self):
        """Populate company dropdown with existing companies"""
        from app.core.db import get_company_accounts
        companies = get_company_accounts()
        self.company.clear()
        self.company.addItem("-- Select Company --", None)
        for company in companies:
            self.company.addItem(company['name'], company['id'])
    
    def load_guest_data(self):
        """Load existing guest data into the form"""
        self.first_name.setText(self.guest_data.get('first_name', ''))
        self.last_name.setText(self.guest_data.get('last_name', ''))
        
        # Set ID type
        id_type = self.guest_data.get('id_type')
        if id_type:
            index = self.id_type.findText(id_type)
            if index >= 0:
                self.id_type.setCurrentIndex(index)
        
        self.id_number.setText(self.guest_data.get('id_number', ''))
        
        # Set date of birth
        dob = self.guest_data.get('dob')
        if dob:
            self.dob.setDate(QDate.fromString(dob, 'yyyy-MM-dd'))
        
        # Set nationality
        nationality = self.guest_data.get('nationality')
        if nationality:
            index = self.nationality.findText(nationality)
            if index >= 0:
                self.nationality.setCurrentIndex(index)
        
        self.phone_code.setText(self.guest_data.get('phone_code', ''))
        self.phone_number.setText(self.guest_data.get('phone_number', ''))
        self.email.setText(self.guest_data.get('email', ''))
        
        # Set company
        company_id = self.guest_data.get('company_id')
        if company_id:
            for i in range(self.company.count()):
                if self.company.itemData(i) == company_id:
                    self.company.setCurrentIndex(i)
                    break
        
        self.address.setText(self.guest_data.get('address', ''))
        
        # Set VIP status
        vip_status = self.guest_data.get('vip_status')
        if vip_status:
            index = self.vip_status.findText(vip_status)
            if index >= 0:
                self.vip_status.setCurrentIndex(index)
        
        self.preferences.setText(self.guest_data.get('preferences', ''))
    
    def validate_and_accept(self):
        """Validate form data before accepting"""
        if not self.first_name.text().strip() or not self.last_name.text().strip():
            QMessageBox.warning(
                self,
                "Validation Error",
                "First name and last name are required fields.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        self.accept()

class GuestHistoryWidget(QWidget):
    """Widget for displaying guest history"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # History table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setHorizontalHeaderLabels([
            "Check-in Date", "Check-out Date", "Room Number",
            "Status", "Notes"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.history_table)

class GuestNotesWidget(QWidget):
    """Widget for managing guest notes"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Add note section
        add_note_layout = QHBoxLayout()
        self.note_input = QTextEdit()
        self.note_input.setMaximumHeight(100)
        self.add_note_btn = QPushButton("Add Note")
        add_note_layout.addWidget(self.note_input)
        add_note_layout.addWidget(self.add_note_btn)
        
        # Notes list
        self.notes_list = QTableWidget()
        self.notes_list.setColumnCount(3)
        self.notes_list.setAlternatingRowColors(True)
        self.notes_list.setHorizontalHeaderLabels([
            "Date", "Note", "Actions"
        ])
        self.notes_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        layout.addLayout(add_note_layout)
        layout.addWidget(self.notes_list)

class GuestsWidget(QWidget):
    """Main widget for guest management"""
    
    # Signals
    guest_selected = pyqtSignal(dict)
    check_in_requested = pyqtSignal()
    check_out_requested = pyqtSignal()
    guest_deleted = pyqtSignal()  # Add guest deletion signal
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Guest Management")
        title_label.setObjectName("pageTitle")
        header_layout.addWidget(title_label)
        
        # Search bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search guests...")
        self.search_input.setMinimumWidth(300)
        search_layout.addWidget(self.search_input)
        
        # Add guest button
        add_guest_btn = QPushButton("Add New Guest")
        add_guest_btn.setObjectName("actionButton")
        add_guest_btn.setIcon(QIcon(":/icons/add_user.png"))
        add_guest_btn.clicked.connect(self.add_new_guest)
        search_layout.addWidget(add_guest_btn)
        
        header_layout.addLayout(search_layout)
        main_layout.addLayout(header_layout)
        
        # Guest table
        self.guest_table = QTableWidget()
        self.guest_table.setColumnCount(8)
        self.guest_table.setAlternatingRowColors(True)
        self.guest_table.setHorizontalHeaderLabels([
            "Name", "ID Number", "Nationality", "Phone",
            "Email", "VIP Status", "Last Stay", "Actions"
        ])
        self.guest_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        for i in range(1, 8):
            self.guest_table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
        self.guest_table.verticalHeader().setDefaultSectionSize(50)  # Make rows thicker
        main_layout.addWidget(self.guest_table)
        
        # Connect signals
        self.search_input.textChanged.connect(self.search_guests)
        self.guest_table.itemSelectionChanged.connect(self.on_guest_selected)
        
        self.load_guests()
    
    def load_guests(self):
        guests = get_all_guests()
        self.guest_table.setRowCount(len(guests))
        for row, guest in enumerate(guests):
            name = f"{guest['first_name']} {guest['last_name']}"
            self.guest_table.setItem(row, 0, QTableWidgetItem(name))
            self.guest_table.setItem(row, 1, QTableWidgetItem(guest.get('id_number') or ""))
            self.guest_table.setItem(row, 2, QTableWidgetItem(guest.get('nationality') or ""))
            phone = f"{guest.get('phone_code') or ''} {guest.get('phone_number') or ''}"
            self.guest_table.setItem(row, 3, QTableWidgetItem(phone.strip()))
            self.guest_table.setItem(row, 4, QTableWidgetItem(guest.get('email') or ""))
            self.guest_table.setItem(row, 5, QTableWidgetItem(guest.get('vip_status') or ""))
            self.guest_table.setItem(row, 6, QTableWidgetItem("-"))  # Last Stay placeholder
            
            # Create action buttons widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(10)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("tableActionButton")
            edit_btn.setProperty("action", "edit")
            edit_btn.setFixedWidth(80)
            edit_btn.clicked.connect(lambda _, g=guest: self.edit_guest(g))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("tableActionButton")
            delete_btn.setProperty("action", "delete")
            delete_btn.setFixedWidth(80)
            delete_btn.clicked.connect(lambda _, g=guest: self.delete_guest(g))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.guest_table.setCellWidget(row, 7, actions_widget)

    def add_new_guest(self):
        dialog = GuestProfileDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            guest = {
                'first_name': dialog.first_name.text().upper(),
                'last_name': dialog.last_name.text().upper(),
                'id_type': dialog.id_type.currentText() if hasattr(dialog, 'id_type') else None,
                'id_number': dialog.id_number.text() if hasattr(dialog, 'id_number') else None,
                'dob': dialog.dob.date().toString('yyyy-MM-dd') if hasattr(dialog, 'dob') else None,
                'nationality': dialog.nationality.currentText() if hasattr(dialog, 'nationality') else None,
                'phone_code': dialog.phone_code.text() if hasattr(dialog, 'phone_code') else None,
                'phone_number': dialog.phone_number.text() if hasattr(dialog, 'phone_number') else None,
                'email': dialog.email.text() if hasattr(dialog, 'email') else None,
                'company_id': dialog.company.itemData(dialog.company.currentIndex()) if hasattr(dialog, 'company') else None,
                'address': dialog.address.text() if hasattr(dialog, 'address') else None,
                'vip_status': dialog.vip_status.currentText() if hasattr(dialog, 'vip_status') else None,
                'preferences': dialog.preferences.text() if hasattr(dialog, 'preferences') else None,
            }
            insert_guest(guest)
            self.load_guests()
            self.guest_data_changed.emit() # Emit the signal

    def edit_guest(self, guest):
        dialog = GuestProfileDialog(self, guest)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_guest = {
                'first_name': dialog.first_name.text().upper(),
                'last_name': dialog.last_name.text().upper(),
                'id_type': dialog.id_type.currentText() if hasattr(dialog, 'id_type') else None,
                'id_number': dialog.id_number.text() if hasattr(dialog, 'id_number') else None,
                'dob': dialog.dob.date().toString('yyyy-MM-dd') if hasattr(dialog, 'dob') else None,
                'nationality': dialog.nationality.currentText() if hasattr(dialog, 'nationality') else None,
                'phone_code': dialog.phone_code.text() if hasattr(dialog, 'phone_code') else None,
                'phone_number': dialog.phone_number.text() if hasattr(dialog, 'phone_number') else None,
                'email': dialog.email.text() if hasattr(dialog, 'email') else None,
                'company_id': dialog.company.itemData(dialog.company.currentIndex()) if hasattr(dialog, 'company') else None,
                'address': dialog.address.text() if hasattr(dialog, 'address') else None,
                'vip_status': dialog.vip_status.currentText() if hasattr(dialog, 'vip_status') else None,
                'preferences': dialog.preferences.text() if hasattr(dialog, 'preferences') else None,
            }
            update_guest(guest['id'], updated_guest)
            self.load_guests()
            self.guest_data_changed.emit()

    def delete_guest(self, guest):
        reply = QMessageBox.question(
            self,
            'Confirm Delete',
            f'Are you sure you want to delete {guest["first_name"]} {guest["last_name"]}?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            delete_guest(guest['id'])
            self.load_guests()
            self.guest_data_changed.emit()

    def search_guests(self):
        """Search guests based on input"""
        search_text = self.search_input.text().lower()
        
        # Get all guests from the database
        all_guests = get_all_guests()
        
        # Filter guests based on search text
        filtered_guests = []
        for guest in all_guests:
            full_name = f"{guest['first_name']} {guest['last_name']}".lower()
            if search_text in full_name:
                filtered_guests.append(guest)
        
        # Update the table with filtered results
        self.guest_table.setRowCount(len(filtered_guests))
        for row, guest in enumerate(filtered_guests):
            name = f"{guest['first_name']} {guest['last_name']}"
            self.guest_table.setItem(row, 0, QTableWidgetItem(name))
            self.guest_table.setItem(row, 1, QTableWidgetItem(guest.get('id_number') or ""))
            self.guest_table.setItem(row, 2, QTableWidgetItem(guest.get('nationality') or ""))
            phone = f"{guest.get('phone_code') or ''} {guest.get('phone_number') or ''}"
            self.guest_table.setItem(row, 3, QTableWidgetItem(phone.strip()))
            self.guest_table.setItem(row, 4, QTableWidgetItem(guest.get('email') or ""))
            self.guest_table.setItem(row, 5, QTableWidgetItem(guest.get('vip_status') or ""))
            self.guest_table.setItem(row, 6, QTableWidgetItem("-"))  # Last Stay placeholder
            
            # Create action buttons widget
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(10)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("tableActionButton")
            edit_btn.setProperty("action", "edit")
            edit_btn.setFixedWidth(80)
            edit_btn.clicked.connect(lambda _, g=guest: self.edit_guest(g))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("tableActionButton")
            delete_btn.setProperty("action", "delete")
            delete_btn.setFixedWidth(80)
            delete_btn.clicked.connect(lambda _, g=guest: self.delete_guest(g))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.guest_table.setCellWidget(row, 7, actions_widget)

    def on_guest_selected(self):
        """Handle guest selection"""
        selected_items = self.guest_table.selectedItems()
        if selected_items:
            row = selected_items[0].row()
            guest_data = {
                'first_name': self.guest_table.item(row, 0).text().split()[0],
                'last_name': self.guest_table.item(row, 0).text().split()[1],
                'id_number': self.guest_table.item(row, 1).text(),
                'nationality': self.guest_table.item(row, 2).text(),
                'phone': self.guest_table.item(row, 3).text(),
                'email': self.guest_table.item(row, 4).text(),
                'vip_status': self.guest_table.item(row, 5).text()
            }
            self.guest_selected.emit(guest_data)
    
    guest_data_changed = pyqtSignal()
