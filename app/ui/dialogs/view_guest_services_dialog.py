from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget, QTableWidgetItem, QMessageBox, QInputDialog
)
from PyQt6.QtCore import Qt
from app.core.db import get_all_checkins, get_booking_services, get_guest_services, mark_guest_services_paid
from decimal import Decimal
import os
from fpdf import FPDF
from datetime import datetime

class ViewGuestServicesDialog(QDialog):
    def __init__(self, guest, parent=None):
        super().__init__(parent)
        self.guest = guest
        self.parent = parent  # Store reference to parent for refresh
        self.setWindowTitle(f"Services for {guest['first_name']} {guest['last_name']}")
        self.setMinimumWidth(700)
        self.setMinimumHeight(400)
        self.setup_ui()
        self.load_services()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels([
            "Date", "Service Name", "Quantity", "Unit Price", "Total", "Status"
        ])
        self.services_table.horizontalHeader().setStretchLastSection(True)
        self.services_table.verticalHeader().setDefaultSectionSize(32)
        layout.addWidget(self.services_table)

        self.total_label = QLabel("Total: MAD 0.00")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        layout.addWidget(self.total_label)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        pay_btn = QPushButton("Pay")
        pay_btn.setObjectName("actionButton")
        pay_btn.clicked.connect(self.pay_for_services)
        btn_layout.addWidget(pay_btn)
        print_btn = QPushButton("Print Invoice")
        print_btn.setObjectName("actionButton")
        print_btn.clicked.connect(self.print_invoice)
        btn_layout.addWidget(print_btn)
        layout.addLayout(btn_layout)

    def load_services(self):
        # Show all extra services for this guest (by guest_id)
        services = get_guest_services(self.guest['id'])
        self.display_services(services)

    def display_services(self, services):
        self.services_table.setRowCount(len(services))
        total = Decimal('0')
        for row, s in enumerate(services):
            self.services_table.setItem(row, 0, QTableWidgetItem(s.get('charge_date', '')))
            self.services_table.setItem(row, 1, QTableWidgetItem(s.get('service_name', '')))
            self.services_table.setItem(row, 2, QTableWidgetItem(str(s.get('quantity', ''))))
            self.services_table.setItem(row, 3, QTableWidgetItem(f"MAD {Decimal(str(s.get('unit_price_at_time_of_charge', 0))):.2f}"))
            self.services_table.setItem(row, 4, QTableWidgetItem(f"MAD {Decimal(str(s.get('total_charge', 0))):.2f}"))
            total += Decimal(str(s.get('total_charge', 0)))
            # Payment status visual cue
            status = "Unpaid"
            color = Qt.GlobalColor.red
            if s.get('is_paid', 0):
                status = "Paid"
                color = Qt.GlobalColor.green
            elif Decimal(str(s.get('amount_paid', 0))) > 0:
                status = f"Partly Paid ({Decimal(str(s.get('remaining_amount', 0))):.2f} left)"
                color = Qt.GlobalColor.darkYellow
            status_item = QTableWidgetItem(status)
            status_item.setForeground(color)
            self.services_table.setItem(row, 5, status_item)
        self.total_label.setText(f"Total: MAD {total:.2f}")
        self.services = services
        self.total = total

    def print_invoice(self):
        if not self.services:
            QMessageBox.warning(self, "No Services", "No services to print.")
            return
        try:
            pdf_path = self.generate_services_invoice()
            if pdf_path and os.path.exists(pdf_path):
                os.startfile(pdf_path)
            else:
                QMessageBox.warning(self, "Error", "Failed to generate invoice PDF")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print invoice: {str(e)}")

    def generate_services_invoice(self):
        # Minimal version of generate_checkout_receipt, only for services
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font('Arial', 'B', 16)
        pdf.cell(0, 10, "HOTEL KISSAN AGDZ", 0, 1, "L")
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 5, "Avenue Mohamed V, Agdz, Province of Zagora, Morocco", 0, 1, "L")
        pdf.cell(0, 5, f"Guest: {self.guest['first_name']} {self.guest['last_name']}", 0, 1, "L")
        pdf.ln(5)
        pdf.set_font('Arial', 'B', 14)
        pdf.cell(0, 10, "INVOICE (Additional Services)", 0, 1, "C")
        pdf.ln(3)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(0, 8, "Services:", 0, 1, "L")
        pdf.set_font('Arial', 'B', 10)
        pdf.cell(60, 8, "Date", 1, 0, "L")
        pdf.cell(60, 8, "Service", 1, 0, "L")
        pdf.cell(25, 8, "Qty", 1, 0, "C")
        pdf.cell(25, 8, "Unit Price", 1, 0, "R")
        pdf.cell(25, 8, "Total", 1, 1, "R")
        pdf.set_font('Arial', '', 10)
        for s in self.services:
            pdf.cell(60, 8, s.get('charge_date', ''), 1, 0, "L")
            pdf.cell(60, 8, s.get('service_name', ''), 1, 0, "L")
            pdf.cell(25, 8, str(s.get('quantity', '')), 1, 0, "C")
            pdf.cell(25, 8, f"{Decimal(str(s.get('unit_price_at_time_of_charge', 0))):.2f}", 1, 0, "R")
            pdf.cell(25, 8, f"{Decimal(str(s.get('total_charge', 0))):.2f}", 1, 1, "R")
        pdf.ln(2)
        pdf.set_font('Arial', 'B', 12)
        pdf.cell(170, 8, "Total:", 1, 0, "R")
        pdf.cell(25, 8, f"{self.total:.2f}", 1, 1, "R")
        pdf.ln(5)
        pdf.set_font('Arial', '', 10)
        pdf.cell(0, 5, "Thank you for choosing HOTEL KISSAN AGDZ.", 0, 1, "C")
        # Save PDF
        filename = f"services_invoice_{self.guest['id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        pdf_path = os.path.join(os.getcwd(), "receipts", filename)
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        pdf.output(pdf_path)
        return pdf_path

    def pay_for_services(self):
        # Calculate remaining amount (total - amount already paid)
        total_unpaid = Decimal('0')
        for service in self.services:
            if not service.get('is_paid', 0):  # Only unpaid services
                total_unpaid += Decimal(str(service.get('total_charge', 0)))
        
        # If all services are already paid, show message
        if total_unpaid <= 0:
            QMessageBox.information(self, "Payment Status", "All services are already paid.")
            return
        
        # Calculate remaining amount to pay
        amount_already_paid = Decimal('0')
        if self.services:
            # Get amount already paid from first service (all services have same payment info)
            amount_already_paid = Decimal(str(self.services[0].get('amount_paid', 0)))
        
        remaining_to_pay = total_unpaid - amount_already_paid
        
        # Ensure remaining is not negative
        remaining_to_pay = max(Decimal('0'), remaining_to_pay)
        
        # If nothing remaining to pay, show message
        if remaining_to_pay <= 0:
            QMessageBox.information(self, "Payment Status", "All services are already paid.")
            return
        
        # Prompt for amount paid with remaining amount as default and maximum
        amount, ok = QInputDialog.getDouble(
            self, 
            "Pay for Services", 
            f"Enter amount paid (remaining: MAD {remaining_to_pay:.2f}):", 
            float(remaining_to_pay), 
            0, 
            float(remaining_to_pay), 
            2
        )
        
        if ok:
            # Validate that amount doesn't exceed remaining
            if amount > float(remaining_to_pay):
                QMessageBox.warning(self, "Invalid Amount", f"Amount cannot exceed remaining balance of MAD {remaining_to_pay:.2f}")
                return
            
            mark_guest_services_paid(self.guest['id'], amount, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            QMessageBox.information(self, "Payment Recorded", "Payment status updated.")
            self.load_services()
            
            # Refresh the parent services report tab if it exists
            if hasattr(self.parent, 'load_guests'):
                self.parent.load_guests() 