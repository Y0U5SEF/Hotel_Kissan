from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QComboBox, QSpinBox, QLineEdit, QFormLayout, QMessageBox, QDateEdit
)
from PyQt6.QtCore import Qt, QDate
from app.core.db import get_services, add_booking_service
from datetime import datetime

class AddExtraServiceDialog(QDialog):
    def __init__(self, guest, parent=None):
        super().__init__(parent)
        self.guest = guest
        self.setup_ui()

    def setup_ui(self):
        self.setWindowTitle(f"Add Extra Service for {self.guest['first_name']} {self.guest['last_name']}")
        self.setMinimumWidth(400)

        layout = QVBoxLayout(self)

        # Guest info
        info_label = QLabel(f"Guest: {self.guest['first_name']} {self.guest['last_name']}")
        info_label.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(info_label)

        # Form layout
        form = QFormLayout()

        # Service selection
        self.service_combo = QComboBox()
        self.service_combo.setMinimumWidth(200)
        self.populate_services()
        self.service_combo.currentIndexChanged.connect(self.update_total)
        form.addRow("Service:", self.service_combo)

        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self.update_total)
        form.addRow("Quantity:", self.quantity_spin)

        # Unit price
        self.price_label = QLabel("MAD 0.00")
        form.addRow("Unit Price:", self.price_label)

        # Total
        self.total_label = QLabel("MAD 0.00")
        self.total_label.setStyleSheet("font-weight: bold;")
        form.addRow("Total:", self.total_label)

        # Date
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form.addRow("Date:", self.date_edit)

        # Notes
        self.notes_edit = QLineEdit()
        form.addRow("Notes:", self.notes_edit)

        layout.addLayout(form)

        # Buttons
        button_layout = QHBoxLayout()
        add_btn = QPushButton("Add Charge")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self.add_charge)

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("actionButton")
        cancel_btn.clicked.connect(self.reject)

        button_layout.addWidget(add_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)
        # Ensure price and total are initialized
        self.update_total()

    def populate_services(self):
        services = get_services()
        self.services = services  # Store for later use
        for service in services:
            self.service_combo.addItem(f"{service['name']} (MAD {service['default_price']:.2f})", service)

    def update_total(self):
        if self.service_combo.currentData():
            service = self.service_combo.currentData()
            unit_price = service['default_price']
            quantity = self.quantity_spin.value()
            total = unit_price * quantity
            self.price_label.setText(f"MAD {unit_price:.2f}")
            self.total_label.setText(f"MAD {total:.2f}")

    def add_charge(self):
        if not self.service_combo.currentData():
            QMessageBox.warning(self, "Error", "Please select a service")
            return
        service = self.service_combo.currentData()
        quantity = self.quantity_spin.value()
        unit_price = service['default_price']
        total = unit_price * quantity
        charge_date = self.date_edit.date().toString('yyyy-MM-dd')
        # For this context, we assume a booking_id of None or 0, and store guest_id instead
        booking_service = {
            'booking_id': None,  # Not linked to a booking
            'guest_id': self.guest['id'],
            'service_id': service['id'],
            'quantity': quantity,
            'unit_price_at_time_of_charge': unit_price,
            'total_charge': total,
            'notes': self.notes_edit.text(),
            'charge_date': charge_date
        }
        try:
            add_booking_service(booking_service)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add charge: {str(e)}") 