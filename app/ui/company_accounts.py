from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QFormLayout, QDialog, QDialogButtonBox,
    QMessageBox, QTabWidget, QTextEdit, QSpinBox, QDoubleSpinBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from app.core.db import (
    add_company_account, get_company_accounts, get_company_account,
    update_company_account, get_company_charges, mark_company_charge_paid,
    get_company_balance
)

class CompanyAccountDialog(QDialog):
    """Dialog for adding/editing company accounts"""
    def __init__(self, parent=None, company_data=None):
        super().__init__(parent)
        self.company_data = company_data
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Edit Company" if self.company_data else "Add New Company")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Basic Information
        form_layout = QFormLayout()
        
        # Company Name
        self.name = QLineEdit()
        self.name.setPlaceholderText("Enter company name")
        form_layout.addRow("Company Name *:", self.name)
        
        # Address
        self.address = QLineEdit()
        self.address.setPlaceholderText("Enter company address")
        form_layout.addRow("Address:", self.address)
        
        # Phone
        self.phone = QLineEdit()
        self.phone.setPlaceholderText("Enter phone number")
        form_layout.addRow("Phone:", self.phone)
        
        # Email
        self.email = QLineEdit()
        self.email.setPlaceholderText("Enter email address")
        form_layout.addRow("Email:", self.email)
        
        # Tax ID
        self.tax_id = QLineEdit()
        self.tax_id.setPlaceholderText("Enter tax ID")
        form_layout.addRow("Tax ID:", self.tax_id)
        
        # Billing Terms
        self.billing_terms = QTextEdit()
        self.billing_terms.setPlaceholderText("Enter billing terms")
        self.billing_terms.setMaximumHeight(100)
        form_layout.addRow("Billing Terms:", self.billing_terms)
        
        # Credit Limit
        self.credit_limit = QDoubleSpinBox()
        self.credit_limit.setRange(0, 1000000)
        self.credit_limit.setDecimals(2)
        self.credit_limit.setSuffix(" MAD")
        form_layout.addRow("Credit Limit:", self.credit_limit)
        
        # Payment Due Days
        self.payment_due_days = QSpinBox()
        self.payment_due_days.setRange(0, 365)
        self.payment_due_days.setSuffix(" days")
        form_layout.addRow("Payment Due Days:", self.payment_due_days)
        
        layout.addLayout(form_layout)
        
        # Dialog Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        # Load existing data if editing
        if self.company_data:
            self.load_company_data()
    
    def load_company_data(self):
        """Load existing company data into the form"""
        self.name.setText(self.company_data.get('name', ''))
        self.address.setText(self.company_data.get('address', ''))
        self.phone.setText(self.company_data.get('phone', ''))
        self.email.setText(self.company_data.get('email', ''))
        self.tax_id.setText(self.company_data.get('tax_id', ''))
        self.billing_terms.setText(self.company_data.get('billing_terms', ''))
        self.credit_limit.setValue(self.company_data.get('credit_limit', 0))
        self.payment_due_days.setValue(self.company_data.get('payment_due_days', 30))
    
    def validate_and_accept(self):
        """Validate form data before accepting"""
        if not self.name.text().strip():
            QMessageBox.warning(
                self,
                "Validation Error",
                "Company name is required.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        self.accept()

class CompanyAccountsWidget(QWidget):
    """Widget for managing company accounts"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        header_layout = QHBoxLayout()
        
        title_label = QLabel("Company Accounts")
        title_label.setObjectName("pageTitle")
        header_layout.addWidget(title_label)
        
        # Add company button
        add_company_btn = QPushButton("Add New Company")
        add_company_btn.setObjectName("actionButton")
        add_company_btn.setIcon(QIcon(":/icons/add.png"))
        add_company_btn.clicked.connect(self.add_new_company)
        header_layout.addWidget(add_company_btn)
        
        layout.addLayout(header_layout)
        
        # Company accounts table
        self.company_table = QTableWidget()
        self.company_table.setColumnCount(8)
        self.company_table.setHorizontalHeaderLabels([
            "Company Name", "Address", "Phone", "Email",
            "Tax ID", "Credit Limit", "Balance", "Actions"
        ])
        self.company_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.company_table.setAlternatingRowColors(True)
        layout.addWidget(self.company_table)
        
        # Load initial data
        self.load_companies()
    
    def load_companies(self):
        """Load company accounts into the table"""
        companies = get_company_accounts()
        self.company_table.setRowCount(len(companies))
        
        for row, company in enumerate(companies):
            # Company Name
            name_item = QTableWidgetItem(company['name'])
            name_item.setData(Qt.ItemDataRole.UserRole, company['id'])
            self.company_table.setItem(row, 0, name_item)
            
            # Address
            self.company_table.setItem(row, 1, QTableWidgetItem(company.get('address', '')))
            
            # Phone
            self.company_table.setItem(row, 2, QTableWidgetItem(company.get('phone', '')))
            
            # Email
            self.company_table.setItem(row, 3, QTableWidgetItem(company.get('email', '')))
            
            # Tax ID
            self.company_table.setItem(row, 4, QTableWidgetItem(company.get('tax_id', '')))
            
            # Credit Limit
            credit_limit = f"{company.get('credit_limit', 0):.2f} MAD"
            self.company_table.setItem(row, 5, QTableWidgetItem(credit_limit))
            
            # Balance
            balance = get_company_balance(company['id'])
            balance_text = f"{balance:.2f} MAD"
            balance_item = QTableWidgetItem(balance_text)
            balance_item.setForeground(Qt.GlobalColor.red if balance > 0 else Qt.GlobalColor.green)
            self.company_table.setItem(row, 6, balance_item)
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("tableButton")
            edit_btn.clicked.connect(lambda checked, c=company: self.edit_company(c))
            
            charges_btn = QPushButton("Charges")
            charges_btn.setObjectName("tableButton")
            charges_btn.clicked.connect(lambda checked, c=company: self.view_charges(c))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(charges_btn)
            actions_layout.addStretch()
            
            self.company_table.setCellWidget(row, 7, actions_widget)
    
    def add_new_company(self):
        """Open dialog to add a new company"""
        dialog = CompanyAccountDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            company = {
                'name': dialog.name.text(),
                'address': dialog.address.text(),
                'phone': dialog.phone.text(),
                'email': dialog.email.text(),
                'tax_id': dialog.tax_id.text(),
                'billing_terms': dialog.billing_terms.toPlainText(),
                'credit_limit': dialog.credit_limit.value(),
                'payment_due_days': dialog.payment_due_days.value()
            }
            add_company_account(company)
            self.load_companies()
    
    def edit_company(self, company):
        """Open dialog to edit a company"""
        dialog = CompanyAccountDialog(self, company)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            company.update({
                'name': dialog.name.text(),
                'address': dialog.address.text(),
                'phone': dialog.phone.text(),
                'email': dialog.email.text(),
                'tax_id': dialog.tax_id.text(),
                'billing_terms': dialog.billing_terms.toPlainText(),
                'credit_limit': dialog.credit_limit.value(),
                'payment_due_days': dialog.payment_due_days.value()
            })
            update_company_account(company)
            self.load_companies()
    
    def view_charges(self, company):
        """Open dialog to view company charges"""
        dialog = CompanyChargesDialog(self, company)
        dialog.exec()

class CompanyChargesDialog(QDialog):
    """Dialog for viewing and managing company charges"""
    def __init__(self, parent=None, company=None):
        super().__init__(parent)
        self.company = company
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle(f"Charges - {self.company['name']}")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Company info
        info_frame = QFrame()
        info_layout = QFormLayout(info_frame)
        
        info_layout.addRow("Company:", QLabel(self.company['name']))
        info_layout.addRow("Address:", QLabel(self.company.get('address', '')))
        info_layout.addRow("Phone:", QLabel(self.company.get('phone', '')))
        info_layout.addRow("Email:", QLabel(self.company.get('email', '')))
        
        layout.addWidget(info_frame)
        
        # Charges table
        self.charges_table = QTableWidget()
        self.charges_table.setColumnCount(8)
        self.charges_table.setHorizontalHeaderLabels([
            "Date", "Guest", "Check-in ID", "Arrival", "Departure",
            "Room Charges", "Service Charges", "Total", "Status"
        ])
        self.charges_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.charges_table.setAlternatingRowColors(True)
        layout.addWidget(self.charges_table)
        
        # Load charges
        self.load_charges()
        
        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def load_charges(self):
        """Load company charges into the table"""
        charges = get_company_charges(self.company['id'])
        self.charges_table.setRowCount(len(charges))
        
        for row, charge in enumerate(charges):
            # Date
            self.charges_table.setItem(row, 0, QTableWidgetItem(charge['charge_date']))
            
            # Guest
            guest_name = f"{charge['first_name']} {charge['last_name']}"
            self.charges_table.setItem(row, 1, QTableWidgetItem(guest_name))
            
            # Check-in ID
            self.charges_table.setItem(row, 2, QTableWidgetItem(charge['checkin_id']))
            
            # Arrival
            self.charges_table.setItem(row, 3, QTableWidgetItem(charge['arrival_date']))
            
            # Departure
            self.charges_table.setItem(row, 4, QTableWidgetItem(charge['departure_date']))
            
            # Room Charges
            room_charges = f"{charge['room_charges']:.2f} MAD"
            self.charges_table.setItem(row, 5, QTableWidgetItem(room_charges))
            
            # Service Charges
            service_charges = f"{charge['service_charges']:.2f} MAD"
            self.charges_table.setItem(row, 6, QTableWidgetItem(service_charges))
            
            # Total
            total = f"{charge['total_amount']:.2f} MAD"
            self.charges_table.setItem(row, 7, QTableWidgetItem(total))
            
            # Status
            status = "Paid" if charge['is_paid'] else "Unpaid"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.GlobalColor.green if charge['is_paid'] else Qt.GlobalColor.red)
            self.charges_table.setItem(row, 8, status_item)
            
            # Add mark as paid button if unpaid
            if not charge['is_paid']:
                mark_paid_btn = QPushButton("Mark as Paid")
                mark_paid_btn.setObjectName("tableButton")
                mark_paid_btn.clicked.connect(lambda checked, c=charge: self.mark_as_paid(c))
                self.charges_table.setCellWidget(row, 9, mark_paid_btn)
    
    def mark_as_paid(self, charge):
        """Mark a charge as paid"""
        reply = QMessageBox.question(
            self,
            "Confirm Payment",
            f"Mark charge of {charge['total_amount']:.2f} MAD as paid?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            mark_company_charge_paid(charge['id'])
            self.load_charges() 