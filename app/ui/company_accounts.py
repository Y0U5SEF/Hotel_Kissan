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
import os
from datetime import datetime, timedelta
from fpdf import FPDF
import traceback
import logging
from app.core.config import RECEIPTS_DIR

logger = logging.getLogger(__name__)

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
        self.company_table.verticalHeader().setDefaultSectionSize(50)
        self.company_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
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
        
        # Add Generate Invoice button at the top
        invoice_btn = QPushButton("Generate Invoice")
        invoice_btn.setObjectName("actionButton")
        invoice_btn.clicked.connect(self.generate_company_invoice_all)
        layout.addWidget(invoice_btn)
        
        # Charges table
        self.charges_table = QTableWidget()
        self.charges_table.setColumnCount(10)
        self.charges_table.setHorizontalHeaderLabels([
            "Date", "Guest", "Check-in ID", "Arrival", "Departure",
            "Room Number", "Room Charges", "Service Charges", "Total", "Status"
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
            
            # Room Number
            self.charges_table.setItem(row, 5, QTableWidgetItem(charge.get('room_number', '-')))
            
            # Room Charges
            room_charges = f"{charge['room_charges']:.2f} MAD"
            self.charges_table.setItem(row, 6, QTableWidgetItem(room_charges))
            
            # Service Charges
            service_charges = f"{charge['service_charges']:.2f} MAD"
            self.charges_table.setItem(row, 7, QTableWidgetItem(service_charges))
            
            # Total
            total = f"{charge['total_amount']:.2f} MAD"
            self.charges_table.setItem(row, 8, QTableWidgetItem(total))
            
            # Status
            status = "Paid" if charge['is_paid'] else "Unpaid"
            status_item = QTableWidgetItem(status)
            status_item.setForeground(Qt.GlobalColor.green if charge['is_paid'] else Qt.GlobalColor.red)
            self.charges_table.setItem(row, 9, status_item)
    
    def generate_company_invoice_all(self):
        """Generate invoice for all company charges"""
        try:
            charges = get_company_charges(self.company['id'])
            if not charges:
                QMessageBox.warning(self, "Warning", "No charges found for this company.")
                return
                
            invoice_path = self.generate_company_invoice(self.company, charges)
            if invoice_path:
                # Open the PDF file
                os.startfile(invoice_path) if os.name == 'nt' else os.system(f'xdg-open "{invoice_path}"')
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate invoice: {str(e)}")

    def generate_company_invoice(self, company, charges):
        """Generate company invoice using FPDF"""
        try:
            # Create receipts directory if it doesn't exist
            os.makedirs(RECEIPTS_DIR, exist_ok=True)
            
            # Create a PDF object with UTF-8 support
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()
            pdf.set_auto_page_break(auto=True, margin=6)
            pdf.set_left_margin(6)
            pdf.set_top_margin(6)
            pdf.set_right_margin(6)
            
            # Set font with UTF-8 support
            font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')
            font_path_regular = os.path.join(font_dir, 'DejaVuSans.ttf')
            font_path_bold = os.path.join(font_dir, 'DejaVuSans-Bold.ttf')
            pdf.add_font('DejaVu', '', font_path_regular, uni=True)
            pdf.add_font('DejaVu', 'B', font_path_bold, uni=True)
            pdf.set_font('DejaVu', '', 10)

            page_width = pdf.w - 2 * pdf.l_margin

            # --- Hotel Information (Header) ---
            pdf.set_font('DejaVu', 'B', 16)
            pdf.cell(page_width * 0.7, 10, "HOTEL KISSAN AGDZ", 0, 0, "L")
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(page_width * 0.3, 10, "LOGO HERE", 0, 1, "R")
            
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 5, "Avenue Mohamed V, Agdz, Province of Zagora, Morocco", 0, 1, "L")
            pdf.cell(0, 5, "Phone: +212 5 44 84 30 44", 0, 1, "L")
            pdf.cell(0, 5, "Fax: +212 5 44 84 32 58", 0, 1, "L")
            pdf.cell(0, 5, "Email: kissane@iam.net.ma", 0, 1, "L")
            pdf.ln(5)

            # --- Title "INVOICE" ---
            pdf.set_font('DejaVu', 'B', 24)
            pdf.cell(0, 15, "INVOICE", 0, 1, "C")
            pdf.ln(3)

            # --- Two Columns: Invoice Details (Left) and Billed To (Right) ---
            col_width = page_width / 2
            pdf.set_font('DejaVu', 'B', 12)
            pdf.cell(col_width, 5, "Invoice Details:", 0, 0, "L")
            pdf.cell(col_width, 5, "Billed To:", 0, 1, "L")
            
            pdf.set_font('DejaVu', '', 10)
            invoice_date = datetime.now().strftime('%d-%m-%Y')
            
            # Left Column: Invoice Number, Invoice Date
            pdf.cell(col_width, 4, f"Invoice Number: INV-{company['id']}-{datetime.now().strftime('%Y%m%d')}", 0, 0, "L")
            # Right Column: Company Name
            pdf.cell(col_width, 4, f"Company: {company['name']}", 0, 1, "L")

            pdf.cell(col_width, 4, f"Invoice Date: {invoice_date}", 0, 0, "L")
            # Right Column: Company Address
            pdf.cell(col_width, 4, f"Address: {company.get('address', '')}", 0, 1, "L")

            pdf.cell(col_width, 4, f"Due Date: {(datetime.now() + timedelta(days=company.get('payment_due_days', 30))).strftime('%d-%m-%Y')}", 0, 0, "L")
            # Right Column: Company Tax ID
            pdf.cell(col_width, 4, f"Tax ID: {company.get('tax_id', '')}", 0, 1, "L")
            pdf.ln(2)

            # --- Stay Details Table ---
            pdf.set_font('DejaVu', 'B', 12)
            pdf.cell(0, 10, "Stay Details:", 0, 1, "L")
            pdf.set_fill_color(200, 220, 255)
            pdf.set_text_color(0, 0, 0)
            pdf.set_font('DejaVu', 'B', 9)  # Reduced font size for headers
            
            # Calculate column widths
            guest_col_width = page_width * 0.35      # 33%
            checkin_col_width = page_width * 0.12    # 12%
            checkout_col_width = page_width * 0.12   # 12%
            nights_col_width = page_width * 0.10     # 10%
            room_col_width = page_width * 0.10       # 10%
            rate_col_width = page_width * 0.10       # 10%
            total_col_width = page_width * 0.12     # 13%

            # Table headers
            pdf.cell(guest_col_width, 6, "Guest Name", 1, 0, "L", 1)
            pdf.cell(checkin_col_width, 6, "Check-in", 1, 0, "C", 1)
            pdf.cell(checkout_col_width, 6, "Check-out", 1, 0, "C", 1)
            pdf.cell(nights_col_width, 6, "Nights", 1, 0, "C", 1)
            pdf.cell(room_col_width, 6, "Room N", 1, 0, "C", 1)
            pdf.cell(rate_col_width, 6, "Rate", 1, 0, "R", 1)
            pdf.cell(total_col_width, 6, "Total", 1, 1, "R", 1)

            pdf.set_font('DejaVu', '', 9)  # Reduced font size for table content
            
            # Add all charges
            total_amount = 0
            for charge in charges:
                # Calculate nights
                arrival = datetime.strptime(charge['arrival_date'], '%Y-%m-%d')
                departure = datetime.strptime(charge['departure_date'], '%Y-%m-%d')
                nights = (departure - arrival).days
                
                # Calculate night rate
                night_rate = float(charge['room_charges']) / nights if nights > 0 else 0
                
                # body rows height
                row_height = 5

                # Room charges
                pdf.cell(guest_col_width, row_height, f"{charge['first_name']} {charge['last_name']}", 1, 0, "L")
                pdf.cell(checkin_col_width, row_height, charge['arrival_date'], 1, 0, "C")
                pdf.cell(checkout_col_width, row_height, charge['departure_date'], 1, 0, "C")
                pdf.cell(nights_col_width, row_height, str(nights), 1, 0, "C")
                pdf.cell(room_col_width, row_height, charge.get('room_number', '-'), 1, 0, "C")
                pdf.cell(rate_col_width, row_height, f"{night_rate:.2f}", 1, 0, "R")
                pdf.cell(total_col_width, row_height, f"{float(charge['room_charges']):.2f}", 1, 1, "R")
                total_amount += float(charge['room_charges'])

                # Service charges if any
                if float(charge['service_charges']) > 0:
                    pdf.cell(guest_col_width, 8, f"{charge['first_name']} {charge['last_name']}", 1, 0, "L")
                    pdf.cell(checkin_col_width, 8, charge['arrival_date'], 1, 0, "L")
                    pdf.cell(checkout_col_width, 8, charge['departure_date'], 1, 0, "L")
                    pdf.cell(nights_col_width, 8, "-", 1, 0, "C")
                    pdf.cell(room_col_width, 8, "-", 1, 0, "L")
                    pdf.cell(rate_col_width, 8, "-", 1, 0, "R")
                    pdf.cell(total_col_width, 8, f"{float(charge['service_charges']):.2f}", 1, 1, "R")
                    total_amount += float(charge['service_charges'])

            pdf.ln(2)

            # --- Totals (Right Aligned) ---
            pdf.set_x(pdf.l_margin + page_width * 0.6)
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(page_width * 0.2, 8, "Subtotal:", 1, 0, "L")
            pdf.cell(page_width * 0.2, 8, f"{total_amount:.2f} MAD", 1, 1, "R")
            
            pdf.set_x(pdf.l_margin + page_width * 0.6)
            pdf.set_font('DejaVu', 'B', 12)
            pdf.cell(page_width * 0.2, 8, "Total Due:", 1, 0, "L")
            pdf.cell(page_width * 0.2, 8, f"{total_amount:.2f} MAD", 1, 1, "R")
            pdf.ln(20)

            # --- Payment Information ---
            pdf.set_font('DejaVu', 'B', 12)
            pdf.cell(0, 10, "PAYMENT INFORMATION", 0, 1, "L")
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 5, "Please make payment to:", 0, 1, "L")
            pdf.cell(0, 5, "Banque Populaire", 0, 1, "L")
            pdf.cell(0, 5, "RIB: 10156621211 1470932000567", 0, 1, "L")
            pdf.ln(5)

            # --- Footer ---
            footer_text = "Thank you for choosing HOTEL KISSAN AGDZ. We appreciate your business.\n\nICE 001743O83000092\nPatente N°457700803 IF N°6590375 R.C N°12/58"
            
            # Position footer at bottom
            footer_content_height = 30
            footer_start_y = pdf.h - pdf.b_margin - footer_content_height
            pdf.set_y(footer_start_y)

            # Draw line
            pdf.set_draw_color(0, 0, 0)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(5)

            # Add footer text
            pdf.set_font('DejaVu', '', 10)
            pdf.multi_cell(0, 5, footer_text, 0, "C")

            # Save the PDF
            output_pdf_file = os.path.join(RECEIPTS_DIR, f"company_invoice_{company['id']}_{datetime.now().strftime('%Y%m%d')}.pdf")
            pdf.output(output_pdf_file)
            
            return output_pdf_file

        except Exception as e:
            logger.error(f"Error generating company invoice: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to generate company invoice: {str(e)}")
            return None 