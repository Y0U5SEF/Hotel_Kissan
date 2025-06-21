from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QFormLayout, QDialog, QDialogButtonBox, QDoubleSpinBox, QSpinBox, QComboBox, QTextEdit, QCheckBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import json
from app.core.db import add_invoice, get_invoices, get_company_accounts, get_company_account
from datetime import datetime, timedelta
import os
from fpdf import FPDF
from num2words import num2words

RECEIPTS_DIR = os.path.join(os.getcwd(), "receipts")

class InvoicesWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # --- Top: Individual/Company selection and company combo ---
        top_layout = QHBoxLayout()
        self.individual_checkbox = QCheckBox("Individual")
        self.company_checkbox = QCheckBox("Company")
        self.company_combo = QComboBox()
        self.company_combo.setEnabled(False)
        self.company_combo.setMinimumWidth(250)
        top_layout.addWidget(self.individual_checkbox)
        top_layout.addWidget(self.company_checkbox)
        top_layout.addWidget(QLabel("Company:"))
        top_layout.addWidget(self.company_combo)
        top_layout.addStretch()
        layout.addLayout(top_layout)

        self.individual_checkbox.setChecked(True)
        self.individual_checkbox.toggled.connect(self.on_individual_checked)
        self.company_checkbox.toggled.connect(self.on_company_checked)
        self.company_combo.currentIndexChanged.connect(self.on_company_selected)

        self.load_companies()

        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # New Invoice Tab
        self.new_invoice_tab = QWidget()
        self.setup_new_invoice_tab()
        self.tab_widget.addTab(self.new_invoice_tab, QIcon(":/icons/add.png"), "New Invoice")

        # History Tab
        self.history_tab = QWidget()
        self.setup_history_tab()
        self.tab_widget.addTab(self.history_tab, QIcon(":/icons/list.png"), "History")

    def load_companies(self):
        self.company_combo.clear()
        self.companies = get_company_accounts()
        self.company_combo.addItem("Select company", None)
        for c in self.companies:
            self.company_combo.addItem(c['name'], c['id'])

    def on_individual_checked(self, checked):
        if checked:
            self.company_checkbox.setChecked(False)
            self.company_combo.setEnabled(False)
        else:
            self.company_checkbox.setChecked(True)
            self.company_combo.setEnabled(True)

    def on_company_checked(self, checked):
        if checked:
            self.individual_checkbox.setChecked(False)
            self.company_combo.setEnabled(True)
        else:
            self.individual_checkbox.setChecked(True)
            self.company_combo.setEnabled(False)

    def on_company_selected(self, idx):
        if not self.company_checkbox.isChecked():
            return
        company_id = self.company_combo.currentData()
        if company_id:
            company = get_company_account(company_id)
            if company:
                self.customer_name.setText(company.get('name', ''))
                self.customer_email.setText(company.get('email', ''))
                self.customer_phone.setText(company.get('phone', ''))
                self.billing_address.setText(company.get('address', ''))
                self.tax_id.setText(company.get('tax_id', ''))
                self.payment_terms.setPlainText(company.get('billing_terms', ''))
        else:
            self.customer_name.clear()
            self.customer_email.clear()
            self.customer_phone.clear()
            self.billing_address.clear()
            self.tax_id.clear()
            self.payment_terms.clear()

    def setup_new_invoice_tab(self):
        layout = QVBoxLayout(self.new_invoice_tab)
        form = QFormLayout()

        self.customer_name = QLineEdit()
        form.addRow("Customer Name:", self.customer_name)

        self.customer_email = QLineEdit()
        form.addRow("Customer Email:", self.customer_email)

        self.customer_phone = QLineEdit()
        form.addRow("Customer Phone:", self.customer_phone)

        self.billing_address = QLineEdit()
        form.addRow("Billing Address:", self.billing_address)

        self.tax_id = QLineEdit()
        form.addRow("Tax ID:", self.tax_id)

        self.due_date = QLineEdit()
        self.due_date.setPlaceholderText("YYYY-MM-DD")
        form.addRow("Due Date:", self.due_date)

        layout.addLayout(form)

        # Items Table
        self.items = []
        self.items_table = QTableWidget(0, 3)
        self.items_table.setHorizontalHeaderLabels(["Description", "Quantity", "Unit Price"])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.items_table.verticalHeader().setDefaultSectionSize(50)
        layout.addWidget(QLabel("Invoice Items:"))
        layout.addWidget(self.items_table)

        add_item_btn = QPushButton("Add Item")
        add_item_btn.clicked.connect(self.add_item_row)
        layout.addWidget(add_item_btn)

        # Global Tax Section
        tax_layout = QHBoxLayout()
        self.tax_name = QLineEdit()
        self.tax_name.setPlaceholderText("Tax Name (e.g. VAT)")
        self.tax_value = QDoubleSpinBox()
        self.tax_value.setRange(0, 100000)
        self.tax_value.setDecimals(2)
        self.tax_type_combo = QComboBox()
        self.tax_type_combo.addItems(["Amount (MAD)", "Percentage (%)"])
        tax_layout.addWidget(QLabel("Tax:"))
        tax_layout.addWidget(self.tax_name)
        tax_layout.addWidget(self.tax_value)
        tax_layout.addWidget(self.tax_type_combo)
        tax_layout.addStretch()
        layout.addLayout(tax_layout)

        # Invoice Language
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Invoice Language:")
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["English", "French"])
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # Payment Terms and Special Instructions
        self.payment_terms = QTextEdit()
        self.payment_terms.setMaximumHeight(60)
        layout.addWidget(QLabel("Payment Terms:"))
        layout.addWidget(self.payment_terms)

        self.special_instructions = QTextEdit()
        self.special_instructions.setMaximumHeight(60)
        layout.addWidget(QLabel("Special Instructions:"))
        layout.addWidget(self.special_instructions)

        # Submit Button
        submit_btn = QPushButton("Generate Invoice")
        submit_btn.setObjectName("actionButton")
        submit_btn.clicked.connect(self.generate_invoice)
        layout.addWidget(submit_btn)

    def add_item_row(self):
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        for col in range(3):
            if col == 1:  # Quantity
                spin = QSpinBox()
                spin.setRange(1, 1000)
                self.items_table.setCellWidget(row, col, spin)
            elif col == 2:  # Unit Price
                spin = QDoubleSpinBox()
                spin.setRange(0, 1000000)
                spin.setDecimals(2)
                self.items_table.setCellWidget(row, col, spin)
            else:
                self.items_table.setItem(row, col, QTableWidgetItem(""))
        self.items_table.setRowHeight(row, 50)

    def setup_history_tab(self):
        layout = QVBoxLayout(self.history_tab)
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels([
            "Invoice #", "Customer", "Date", "Total", "PDF", "Actions"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.history_table)
        self.load_invoices()

    def load_invoices(self):
        invoices = get_invoices()
        self.history_table.setRowCount(len(invoices))
        for row, inv in enumerate(invoices):
            self.history_table.setItem(row, 0, QTableWidgetItem(inv['invoice_number']))
            self.history_table.setItem(row, 1, QTableWidgetItem(inv['customer_name']))
            self.history_table.setItem(row, 2, QTableWidgetItem(inv['date_generated']))
            self.history_table.setItem(row, 3, QTableWidgetItem(f"{inv['total_amount']:.2f}"))
            self.history_table.setItem(row, 4, QTableWidgetItem(os.path.basename(inv['pdf_path']) if inv['pdf_path'] else "-"))
            btn = QPushButton("Review PDF")
            btn.clicked.connect(lambda checked, path=inv['pdf_path']: self.open_pdf(path))
            self.history_table.setCellWidget(row, 5, btn)

    def open_pdf(self, path):
        if path and os.path.exists(path):
            os.startfile(path) if os.name == 'nt' else os.system(f'xdg-open "{path}"')

    def generate_invoice(self):
        # Gather form data
        customer_name = self.customer_name.text().strip()
        customer_email = self.customer_email.text().strip()
        customer_phone = self.customer_phone.text().strip()
        billing_address = self.billing_address.text().strip()
        tax_id = self.tax_id.text().strip()
        due_date = self.due_date.text().strip()
        payment_terms = self.payment_terms.toPlainText().strip()
        special_instructions = self.special_instructions.toPlainText().strip()
        date_generated = datetime.now().strftime('%Y-%m-%d')
        invoice_number = f"INV-{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Gather items
        items = []
        subtotal = 0
        for row in range(self.items_table.rowCount()):
            desc = self.items_table.item(row, 0).text() if self.items_table.item(row, 0) else ""
            qty = self.items_table.cellWidget(row, 1).value() if self.items_table.cellWidget(row, 1) else 1
            unit_price = self.items_table.cellWidget(row, 2).value() if self.items_table.cellWidget(row, 2) else 0
            line_total = qty * unit_price
            subtotal += line_total
            items.append({
                'description': desc,
                'quantity': qty,
                'unit_price': unit_price,
                'line_total': line_total
            })
        # Global tax
        tax_name = self.tax_name.text().strip()
        tax_value = self.tax_value.value()
        tax_type = self.tax_type_combo.currentText()
        if tax_type == "Percentage (%)":
            tax_amount = subtotal * (tax_value / 100)
        else:
            tax_amount = tax_value
        total_amount = subtotal + tax_amount
        balance_due = total_amount

        # Generate PDF
        os.makedirs(RECEIPTS_DIR, exist_ok=True)
        pdf_path = os.path.join(RECEIPTS_DIR, f"invoice_{invoice_number}.pdf")
        self.generate_invoice_pdf(
            pdf_path, invoice_number, date_generated, due_date, customer_name, customer_email, customer_phone,
            billing_address, tax_id, items, subtotal, tax_name, tax_value, tax_type, tax_amount, total_amount, payment_terms, special_instructions
        )

        # Save invoice to DB
        invoice = {
            'invoice_number': invoice_number,
            'date_generated': date_generated,
            'due_date': due_date,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'billing_address': billing_address,
            'tax_id': tax_id,
            'items': json.dumps(items),
            'subtotal': subtotal,
            'tax_amount': tax_amount,
            'total_amount': total_amount,
            'amount_paid': 0,
            'balance_due': balance_due,
            'payment_terms': payment_terms,
            'special_instructions': special_instructions,
            'pdf_path': pdf_path
        }
        add_invoice(invoice)
        self.load_invoices()
        self.tab_widget.setCurrentIndex(1)
        self.open_pdf(pdf_path)

    def generate_invoice_pdf(self, pdf_path, invoice_number, date_generated, due_date, customer_name, customer_email, customer_phone,
                            billing_address, tax_id, items, subtotal, tax_name, tax_value, tax_type, tax_amount, total_amount, payment_terms, special_instructions):
        # --- CLONED LAYOUT FROM COMPANY ACCOUNTS ---
        def format_number_with_spaces(number):
            """Formats a number with a space as a thousand separator and two decimal places."""
            return f"{number:,.2f}".replace(",", " ")
        from PyQt6.QtCore import QFile
        import tempfile
        import os
        try:
            lang_map = {'English': 'en', 'French': 'fr'}
            lang = lang_map.get(self.lang_combo.currentText(), 'en')
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
                    'stay_details': "Invoice Items:",
                    'check_in': "Description",
                    'check_out': "Qty",
                    'nights': "Unit Price",
                    'total': "Line Total",
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
                    'stay_details': "Articles de la facture:",
                    'check_in': "Description",
                    'check_out': "Qté",
                    'nights': "Prix Unitaire",
                    'total': "Total Ligne",
                    'subtotal': "Sous-total",
                    'total_due': "Total dû",
                    'total_in_words': "Arrêté la présente facture à la somme de",
                    'thank_you': "Merci d'avoir choisi HOTEL KISSAN AGDZ. Nous apprécions votre confiance."
                }
            }
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.add_page()
            y_margin = 6
            x_margin = 10
            pdf.set_auto_page_break(auto=True, margin = y_margin)
            pdf.set_left_margin(x_margin)
            pdf.set_top_margin(y_margin)
            pdf.set_right_margin(x_margin)
            # Try to use SegoeUI, fallback to Arial
            font_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '..', 'fonts')
            segoeui = os.path.join(font_dir, 'segoeui.ttf')
            segoeuib = os.path.join(font_dir, 'segoeuib.ttf')
            try:
                pdf.add_font('segoeui', '', segoeui, uni=True)
                pdf.add_font('segoeui', 'B', segoeuib, uni=True)
                main_font = 'segoeui'
            except Exception:
                pdf.set_font('Arial', '', 10)
                main_font = 'Arial'
            page_width = pdf.w - 2 * pdf.l_margin
            # --- Hotel Information (Header) ---
            pdf.set_font(main_font, '', 10)
            logo_width = 50  # mm
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
                    pdf.ln(logo_width * 0.2)
                except Exception:
                    pass
            pdf.set_font(main_font, 'B', 16)
            pdf.set_x(x_margin)
            pdf.set_y(y_margin)
            pdf.cell(page_width * 0.7, 10, "HOTEL KISSAN AGDZ", 0, 1, "L")
            pdf.set_font(main_font, '', 10)
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
            pdf.set_font(main_font, 'B', 24)
            pdf.cell(0, 15, strings[lang]['invoice'], 0, 1, "C")
            pdf.ln(3)
            # --- Two Columns: Invoice Details (Left) and Billed To (Right) ---
            gap_width = page_width * 0.10
            col_width = page_width * 0.45
            pdf.set_font(main_font, 'B', 12)
            pdf.set_fill_color(200, 220, 255)
            pdf.cell(col_width, 8, strings[lang]['invoice_details'], 0, 0, "L", 1)
            pdf.cell(gap_width, 5, "", 0, 0, "C")
            pdf.cell(col_width, 8, strings[lang]['billed_to'], 0, 1, "L", 1)
            pdf.ln(1)
            pdf.set_font(main_font, '', 10)
            pdf.cell(col_width, 5, f"{strings[lang]['invoice_number']} {invoice_number}", 0, 0, "L")
            pdf.cell(gap_width, 5, "", 0, 0, "C")
            # --- Billed To Section ---
            if self.company_checkbox.isChecked():
                billed_to_line = f"{strings[lang]['company']} {customer_name}"
                billed_to_line2 = f"{strings[lang]['tax_id']} {tax_id}"
            else:
                billed_to_line = customer_name
                billed_to_line2 = billing_address
            pdf.cell(col_width, 5, billed_to_line, 0, 1, "L")
            pdf.cell(col_width, 5, f"{strings[lang]['invoice_date']} {date_generated}", 0, 0, "L")
            pdf.cell(gap_width, 5, "", 0, 0, "C")
            pdf.cell(col_width, 5, billed_to_line2, 0, 1, "L")
            pdf.ln(1)
            # --- Invoice Items Table ---
            pdf.set_font(main_font, 'B', 12)
            pdf.set_draw_color(200, 200, 200)
            pdf.cell(0, 10, strings[lang]['stay_details'], 0, 1, "L")
            pdf.set_fill_color(200, 220, 255)
            pdf.set_text_color(0, 0, 0)
            # Table headers
            # Fit table to page width
            table_width = page_width
            desc_w = table_width * 0.50
            qty_w = table_width * 0.15
            unit_w = table_width * 0.15
            total_w = table_width * 0.20
            headers = [strings[lang]['check_in'], strings[lang]['check_out'], strings[lang]['nights'], strings[lang]['total']]
            widths = [desc_w, qty_w, unit_w, total_w]
            alignments = ["L", "C", "R", "R"]
            def write_row(pdf, cells, widths, alignments, is_header=False, row_height=10, fill=False):
                for cell, width, align in zip(cells, widths, alignments):
                    if is_header:
                        pdf.set_font(main_font, 'B', 10)
                    else:
                        pdf.set_font(main_font, '', 10)
                    pdf.cell(width, row_height, str(cell), 1, 0, align, fill)
                pdf.ln()
            # Header row (blue)
            write_row(pdf, headers, widths, alignments, is_header=True, row_height=10, fill=True)
            # Table rows (striped)
            for idx, item in enumerate(items):
                fill = (idx % 2 == 0)
                if fill:
                    pdf.set_fill_color(255, 255, 255)  # off-white
                else:
                    pdf.set_fill_color(229, 231, 233)  # white
                row = [item['description'], item['quantity'], f"{item['unit_price']:.2f}", format_number_with_spaces(item['line_total'])]
                write_row(pdf, row, widths, alignments, is_header=False, row_height=8, fill=True)
            pdf.ln(2)
            # --- Totals ---
            pdf.set_font(main_font, '', 10)
            pdf.cell(table_width - total_w, 8, strings[lang]['subtotal'], 1, 0, "R")
            pdf.cell(total_w, 8, f"{subtotal:.2f}", 1, 1, "R")
            if tax_name:
                if tax_type == "Percentage (%)":
                    tax_label = f"{tax_name} ({tax_value:.2f}%)"
                else:
                    tax_label = f"{tax_name} ({tax_value:.2f} MAD)"
                pdf.cell(table_width - total_w, 8, tax_label, 1, 0, "R")
                pdf.cell(total_w, 8, f"{tax_amount:.2f}", 1, 1, "R")
            pdf.set_font(main_font, 'B', 12)
            pdf.cell(table_width - total_w, 8, strings[lang]['total_due'], 1, 0, "R", 1)
            pdf.cell(total_w, 8, format_number_with_spaces(total_amount), 1, 1, "R", 1)
            pdf.ln(3)

            int_part, dec_part = str(total_amount).split('.')

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
            # --- Footer ---
            pdf.set_font(main_font, '', 10)
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
            pdf.set_font(main_font, 'B', 9)
            pdf.multi_cell(0, 5, strings[lang]['thank_you'], 0, "C")
            pdf.output(pdf_path)
        except Exception as e:
            print(f"Error generating invoice PDF: {e}") 