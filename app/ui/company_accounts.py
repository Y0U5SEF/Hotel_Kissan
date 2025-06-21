# before I do my own changes

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QFormLayout, QDialog, QDialogButtonBox,
    QMessageBox, QTabWidget, QTextEdit, QSpinBox, QDoubleSpinBox,
    QCheckBox, QComboBox, QGroupBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QResource, QFile
from PyQt6.QtGui import QIcon
from app.core.db import (
    add_company_account, get_company_accounts, get_company_account,
    update_company_account, get_company_charges, mark_company_charge_paid,
    get_company_balance, get_tax_rates
)
import os
from datetime import datetime, timedelta
from fpdf import FPDF
import traceback
import logging
from app.core.config import RECEIPTS_DIR
import tempfile
from num2words import num2words
import arabic_reshaper
from bidi.algorithm import get_display

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
        self.setMinimumWidth(1000)
        self.setMinimumHeight(700)
        
        layout = QVBoxLayout(self)
        
        # Company info
        info_frame = QFrame()
        info_layout = QFormLayout(info_frame)
        
        info_layout.addRow("Company:", QLabel(self.company['name']))
        info_layout.addRow("Address:", QLabel(self.company.get('address', '')))
        info_layout.addRow("Phone:", QLabel(self.company.get('phone', '')))
        info_layout.addRow("Email:", QLabel(self.company.get('email', '')))
        
        layout.addWidget(info_frame)
        
        # --- Tax Selection Section ---
        self.tax_options = {}
        tax_rates = get_tax_rates()
        tax_group = QGroupBox("Apply Taxes")
        tax_layout = QVBoxLayout()
        
        # Add language selector
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Invoice Language:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "French"])
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        tax_layout.addLayout(lang_layout)
        
        for tax in tax_rates:
            row_layout = QHBoxLayout()
            label = tax['name']
            if tax['tax_type'] == 'fixed':
                label += f" ({float(tax['amount']):.2f} MAD)"
            elif tax['tax_type'] == 'percentage':
                label += f" ({float(tax['percentage']):.2f}%)"
            cb = QCheckBox(label)
            cb.setChecked(True)
            row_layout.addWidget(cb)
            if tax['tax_type'] == 'fixed':
                mode = QComboBox()
                mode.addItems(["per stay", "per night"])
                mode.setCurrentText("per night")  # Default to per night for all fixed taxes
                row_layout.addWidget(mode)
                self.tax_options[tax['id']] = {'checkbox': cb, 'mode': mode, 'tax': tax}
            else:
                self.tax_options[tax['id']] = {'checkbox': cb, 'tax': tax}
            tax_layout.addLayout(row_layout)
        tax_group.setLayout(tax_layout)
        layout.addWidget(tax_group)
        
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

            # Gather selected taxes and their modes
            selected_taxes = []
            for tax_id, opt in self.tax_options.items():
                if opt['checkbox'].isChecked():
                    mode = None
                    if 'mode' in opt:
                        mode = opt['mode'].currentText()
                    selected_taxes.append({'tax': opt['tax'], 'mode': mode})

            invoice_path = self.generate_company_invoice(self.company, charges, selected_taxes)
            if invoice_path:
                # Open the PDF file
                os.startfile(invoice_path) if os.name == 'nt' else os.system(f'xdg-open "{invoice_path}"')
        except Exception as e:
            logger.error(f"Error generating invoice: {str(e)}")
            QMessageBox.critical(self, "Error", f"Failed to generate invoice: {str(e)}")

    def generate_company_invoice(self, company, charges, selected_taxes=None):
        def format_number_with_spaces(number):
            """Formats a number with a space as a thousand separator and two decimal places."""
            return f"{number:,.2f}".replace(",", " ")

        def write_row(pdf, cells, widths, alignments, lang, is_header=False, row_height=10):
            """Write a table row with support for header/data styles."""
            for cell, width, align in zip(cells, widths, alignments):
                if is_header:
                    pdf.set_font('segoeui', 'B', 9)
                else:
                    pdf.set_font('segoeui', '', 9)
                pdf.cell(width, row_height, str(cell), 1, 0, align, 1)
            pdf.ln()

        """Generate company invoice using FPDF"""
        try:
            # Create receipts directory if it doesn't exist
            os.makedirs(RECEIPTS_DIR, exist_ok=True)
            
            # Get selected language and map to correct key
            lang_map = {'English': 'en', 'French': 'fr'}
            lang = lang_map[self.lang_combo.currentText()]
            
            # Language-specific strings
            strings = {
                'en': {
                    'invoice': "INVOICE",
                    'invoice_details': "Invoice Details:",
                    'billed_to': "Billed To:",
                    'invoice_number': "Invoice Number:",
                    'invoice_date': "Invoice Date:",
                    'due_date': "Due Date:",
                    'company': "Company:",
                    'address': "Address:",
                    'tax_id': "ICE:",
                    'stay_details': "Stay Details:",
                    'guest_name': "Guest Name",
                    'check_in': "Check-in",
                    'check_out': "Check-out",
                    'nights': "Nights",
                    'room_no': "Room N°",
                    'rate': "Rate (MAD)",
                    'total': "Total (MAD)",
                    'subtotal': "Subtotal",
                    'total_due': "Total Due",
                    'total_in_words': "This invoice has been finalized in the amount of",
                    'thank_you': "Thank you for choosing HOTEL KISSAN AGDZ. We appreciate your business."
                },
                'fr': {
                    'invoice': "FACTURE",
                    'invoice_details': "Détails de la facture:",
                    'billed_to': "Facturé à:",
                    'invoice_number': "Numéro de facture:",
                    'invoice_date': "Date de facture:",
                    'due_date': "Date d'échéance:",
                    'company': "Société:",
                    'address': "Adresse:",
                    'tax_id': "ICE:",
                    'stay_details': "Détails du séjour:",
                    'guest_name': "Nom du client",
                    'check_in': "Arrivée",
                    'check_out': "Départ",
                    'nights': "Nuits",
                    'room_no': "Chambre N°",
                    'rate': "Tarif (MAD)",
                    'total': "Total (MAD)",
                    'subtotal': "Sous-total",
                    'total_due': "Total dû",
                    'total_in_words': "Arrêté la présente facture à la somme de",
                    'thank_you': "Merci d'avoir choisi HOTEL KISSAN AGDZ. Nous apprécions votre confiance."
                }
            }
            
            # Create a PDF object with UTF-8 support
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()
            y_margin = 6
            x_margin = 10
            pdf.set_auto_page_break(auto=True, margin = y_margin)
            pdf.set_left_margin(x_margin)
            pdf.set_top_margin(y_margin)
            pdf.set_right_margin(x_margin)
            
            # Set font with UTF-8 support
            font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'fonts')

            arial_font_path_regular = os.path.join(font_dir, 'segoeui.ttf')
            arial_font_path_bold = os.path.join(font_dir, 'segoeuib.ttf')

            pdf.add_font('segoeui', '', arial_font_path_regular, uni=True)
            pdf.add_font('segoeui', 'B', arial_font_path_bold, uni=True)

            page_width = pdf.w - 2 * pdf.l_margin

            # --- Hotel Information (Header) ---
            # Use Qt resource system for logo
            pdf.set_font('segoeui', '', 10)
            logo_width = 50  # mm
            logo_height = 50
            logo_path = ":/images/logo.png"
            qfile = QFile(logo_path)
            if qfile.open(QFile.OpenModeFlag.ReadOnly):
                data = qfile.readAll()
                with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                    tmp.write(data.data())
                    tmp_path = tmp.name
                x_logo = pdf.w - pdf.r_margin - logo_width
                y_logo = y_margin
                try:
                    pdf.image(tmp_path, x=x_logo, y=y_logo, w=logo_width)
                    pdf.ln(logo_width * 0.2)  # Adjust line spacing as needed
                except Exception:
                    pass  # If image fails, do nothing
            
            pdf.set_font('segoeui', 'B', 16)
            pdf.set_x(x_margin)
            pdf.set_y(y_margin)
            pdf.cell(page_width * 0.7, 10, "HOTEL KISSAN AGDZ", 0, 1, "L")
            pdf.set_font('segoeui', '', 10)
            pdf.cell(0, 5, "Avenue Mohamed V, Agdz, Province of Zagora, Morocco", 0, 1, "L")

            pdf.cell(18, 5, "Tél", 0, 0, "L")
            pdf.cell(3, 5, ":", 0, 0, "L")
            pdf.cell(0, 5, "+212 5 44 84 30 44", 0, 1, "L")

            pdf.cell(18, 5, "Fax", 0, 0, "L")
            pdf.cell(3, 5, ":", 0, 0, "L")
            pdf.cell(0, 5, "+212 5 44 84 32 58", 0, 1, "L")

            pdf.cell(18, 5, "Courriel", 0, 0, "L")
            pdf.cell(3, 5, ":", 0, 0, "L")
            pdf.cell(0, 5, "kissane@iam.net.ma", 0, 1, "L")

            pdf.ln(2)

            # --- Title "INVOICE" ---
            pdf.set_font('segoeui', 'B', 24)
            pdf.cell(0, 15, strings[lang]['invoice'], 0, 1, "C")
            pdf.ln(3)

            # --- Two Columns: Invoice Details (Left) and Billed To (Right) ---
            gap_width = page_width * 0.10
            col_width = page_width * 0.45
            pdf.set_font('segoeui', 'B', 12)

            pdf.set_fill_color(200, 220, 255)
            pdf.cell(col_width, 8, strings[lang]['invoice_details'], 0, 0, "L", 1)
            pdf.cell(gap_width, 5, "", 0, 0, "C")
            pdf.cell(col_width, 8, strings[lang]['billed_to'], 0, 1, "L", 1)
            pdf.ln(1)
            
            pdf.set_font('segoeui', '', 10)
            invoice_date = datetime.now().strftime('%d-%m-%Y')
            
            # Left Column: Invoice Number, Invoice Date
            pdf.cell(col_width, 5, f"{strings[lang]['invoice_number']} INV-{company['id']}-{datetime.now().strftime('%Y%m%d')}", 0, 0, "L")
            pdf.cell(gap_width, 5, "", 0, 0, "C")
            # Right Column: Company Name
            pdf.cell(col_width, 5, f"{strings[lang]['company']} {company['name']}", 0, 1, "L")

            pdf.cell(col_width, 5, f"{strings[lang]['invoice_date']} {invoice_date}", 0, 0, "L")
            pdf.cell(gap_width, 5, "", 0, 0, "C")
            # Right Column: Company tax id
            pdf.cell(col_width, 5, f"{strings[lang]['tax_id']} {company.get('tax_id', '')}", 0, 1, "L")

            pdf.ln(1)

            # --- Stay Details Table ---
            pdf.set_font('segoeui', 'B', 12)
            pdf.set_draw_color(200, 200, 200)
            pdf.cell(0, 10, strings[lang]['stay_details'], 0, 1, "L")
            pdf.set_fill_color(200, 220, 255)
            pdf.set_text_color(0, 0, 0)
            
            # Calculate column widths
            index_col_width = page_width * 0.03      # 5%
            guest_col_width = page_width * 0.34      # 31%
            checkin_col_width = page_width * 0.12    # 12%
            checkout_col_width = page_width * 0.12   # 12%
            nights_col_width = page_width * 0.08     # 10%
            room_col_width = page_width * 0.08       # 10%
            rate_col_width = page_width * 0.11       # 10%
            total_col_width = page_width * 0.12      # 12%

            headers = [
                "#", strings[lang]['guest_name'], strings[lang]['check_in'],
                strings[lang]['check_out'], strings[lang]['nights'], strings[lang]['room_no'],
                strings[lang]['rate'], strings[lang]['total']
            ]
            widths = [
                index_col_width, guest_col_width, checkin_col_width, checkout_col_width,
                nights_col_width, room_col_width, rate_col_width, total_col_width
            ]

            alignments = ["C", "L", "C", "C", "C", "C", "R", "R"]

            write_row(pdf, headers, widths, alignments, lang, is_header=True)

            # Sort charges by check-in date (most recent first)
            sorted_charges = sorted(charges, key=lambda x: datetime.strptime(x['arrival_date'], '%Y-%m-%d'), reverse=True)
            
            # Add all charges
            total_amount = 0
            row_index = 1

            for charge in sorted_charges:
                arrival = datetime.strptime(charge['arrival_date'], '%Y-%m-%d')
                departure = datetime.strptime(charge['departure_date'], '%Y-%m-%d')
                nights = (departure - arrival).days
                night_rate = float(charge['room_charges']) / nights if nights > 0 else 0

                room_number = charge.get('room_number', '-')
                if room_number != '-' and str(room_number).isdigit():
                    room_number = f"{int(room_number):02d}"

                row_height = 7
                fill_color = '#f8f9f9' if row_index % 2 == 0 else '#ffffff'
                pdf.set_fill_color(229, 231, 233) if fill_color == '#f8f9f9' else pdf.set_fill_color(255, 255, 255)

                # Prepare row data
                row_data = [
                    f"{charge['first_name']} {charge['last_name']}",
                    arrival.strftime('%d-%m-%Y'),
                    departure.strftime('%d-%m-%Y'),
                    str(nights),
                    room_number,
                    format_number_with_spaces(night_rate),
                    format_number_with_spaces(float(charge.get('room_charges', 0) or 0))
                ]
                row = [row_index] + row_data
                alignments = ["C", "L", "C", "C", "C", "C", "R", "R"]

                write_row(pdf, row, widths, alignments, lang, is_header=False, row_height=row_height)

                total_amount += float(charge['room_charges'])
                row_index += 1

            pdf.ln(2)

            # --- Totals (Right Aligned) ---
            num_stays = len(sorted_charges)
            total_nights = sum((datetime.strptime(charge['departure_date'], '%Y-%m-%d') - datetime.strptime(charge['arrival_date'], '%Y-%m-%d')).days for charge in sorted_charges)
            totals_left_col_width = checkin_col_width + checkout_col_width + nights_col_width + room_col_width
            totals_right_col_width = rate_col_width + total_col_width
            totals_x = pdf.l_margin + index_col_width + guest_col_width
            pdf.set_font('segoeui', '', 9)

            pdf.set_x(totals_x)
            pdf.cell(totals_left_col_width, row_height, strings[lang]['subtotal'], 1, 0, "L")
            pdf.cell(totals_right_col_width, row_height, f"{format_number_with_spaces(total_amount)} MAD", 1, 1, "R")
            # Calculate and display only selected taxes
            fixed_total = 0
            tva_percentage = 0
            tva_tax = None
            for entry in selected_taxes or []:
                tax = entry['tax']
                if tax['tax_type'] == 'fixed':
                    mode = entry['mode']
                    if mode == 'per stay':
                        tax_total = num_stays * float(tax['amount'])
                        label = f"{tax['name']} ({float(tax['amount']):.2f} MAD)"
                    elif mode == 'per night':
                        tax_total = total_nights * float(tax['amount'])
                        label = f"{tax['name']} ({float(tax['amount']):.2f} MAD)"
                    else:
                        tax_total = 0
                        label = tax['name']
                    fixed_total += tax_total
                    pdf.set_x(totals_x)
                    pdf.cell(totals_left_col_width, row_height, label, 1, 0, "L")
                    pdf.cell(totals_right_col_width, row_height, f"{format_number_with_spaces(tax_total)} MAD", 1, 1, "R")
                elif tax['tax_type'] == 'percentage':
                    tva_percentage = float(tax['percentage']) / 100
                    tva_tax = tax

            # Apply percentage tax (e.g., TVA) if selected
            tva_total = 0
            if tva_tax:
                tva_base = total_amount + fixed_total
                tva_total = tva_base * tva_percentage
                pdf.set_x(totals_x)
                pdf.cell(totals_left_col_width, row_height, f"{tva_tax['name']} ({int(tva_tax['percentage'])}%)", 1, 0, "L")
                pdf.cell(totals_right_col_width, row_height, f"{format_number_with_spaces(tva_total)} MAD", 1, 1, "R")

            grand_total = total_amount + fixed_total + tva_total
            formatted_grand_total = format_number_with_spaces(grand_total)
            # formatted_grand_total = f"{grand_total:.2f}"

            pdf.set_font('segoeui', 'B', 11)
            pdf.set_x(totals_x)
            pdf.set_fill_color(229, 231, 233)
            pdf.cell(totals_left_col_width, row_height, strings[lang]['total_due'], 1, 0, "L", 1)
            pdf.cell(totals_right_col_width, row_height, f"{formatted_grand_total} MAD", 1, 1, "R", 1)
            pdf.ln(3)

            # Add total due in words after totals table
            pdf.set_font('segoeui', 'B', 11)
            int_part, dec_part = formatted_grand_total.split('.')

            # Remove spaces before passing to num2words
            int_part_clean = int_part.replace(" ", "")
            dec_part_clean = dec_part.replace(" ", "")

            if lang == 'fr':
                int_words = num2words(int_part_clean, lang="fr")
                dec_words = num2words(dec_part_clean, lang="fr")
                if int(dec_part_clean) == 0: # Use dec_part_clean here
                    total_words = f"{int_words} dirhams"
                else:
                    total_words = f"{int_words} dirhams," + " et ".lower() + f"{dec_words} centimes"
            else:
                int_words = num2words(int_part_clean, lang="en")
                dec_words = num2words(dec_part_clean, lang="en")
                if int(dec_part_clean) == 0: # Use dec_part_clean here
                    total_words = f"{int_words} dirhams"
                else:
                    total_words = f"{int_words} dirhams," + " and ".lower() + f"{dec_words} centimes"

            pdf.multi_cell(page_width, 5, f"{strings[lang]['total_in_words']} {total_words}.", 0, "L")

            # ----------------------------------- F O O T E R -----------------------------------------
            pdf.set_font('segoeui', '', 11)
            
            pdf.set_draw_color(0, 0, 0)
            pdf.set_y(pdf.h - pdf.b_margin - 34)
            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(1)

            pdf.cell(0, 5, "Relevé d'Identité Bancaire (RIB): 101 566 2121114709320005 67 - Banque Populaire", 0, 1, "C")
            pdf.cell(0, 5, "Identifiant Commun de l'Entreprise (ICE): 001743O83000092", 0, 1, "C")
            pdf.cell(0, 5, "Patente: 457700803", 0, 1, "C")
            pdf.cell(0, 5, "Identifiant Fiscal (IF): 6590375", 0, 1, "C")
            pdf.cell(0, 5, "Registre de Commerce (RC): 12/58", 0, 1, "C")

            pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
            pdf.ln(1)

            pdf.set_font('segoeui', 'B', 9)
            pdf.multi_cell(0, 5, strings[lang]['thank_you'], 0, "C")

            # Save the PDF
            output_pdf_file = os.path.join(RECEIPTS_DIR, f"company_invoice_{company['id']}_{datetime.now().strftime('%Y%m%d')}.pdf")
            pdf.output(output_pdf_file)
            
            return output_pdf_file

        except Exception as e:
            logger.error(f"Error generating company invoice: {str(e)}")
            logger.error(traceback.format_exc())
            QMessageBox.critical(self, "Error", f"Failed to generate company invoice: {str(e)}")
            return None 