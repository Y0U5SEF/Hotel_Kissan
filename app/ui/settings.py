from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QLineEdit, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QComboBox, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
from app.core.db import (
    get_hotel_settings, update_hotel_settings, get_room_rates, update_room_rate,
    get_services, add_service, update_service, delete_service,
    get_tax_rates, add_tax_rate, update_tax_rate, delete_tax_rate
)

class SettingsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Hotel Information tab
        self.hotel_info_tab = QWidget()
        self.setup_hotel_info_tab()
        self.tab_widget.addTab(self.hotel_info_tab, QIcon(":/icons/hotel_info.png"), "Hotel Information")
        
        # Room Rates tab
        self.room_rates_tab = QWidget()
        self.setup_room_rates_tab()
        self.tab_widget.addTab(self.room_rates_tab, QIcon(":/icons/room_rates.png"), "Room Rates")
        
        # Services tab
        self.services_tab = QWidget()
        self.setup_services_tab()
        self.tab_widget.addTab(self.services_tab, QIcon(":/icons/services.png"), "Services")
        
        # Tax Rates tab
        self.tax_rates_tab = QWidget()
        self.setup_tax_rates_tab()
        self.tab_widget.addTab(self.tax_rates_tab, QIcon(":/icons/tax_rates.png"), "Tax Rates")
        
        layout.addWidget(self.tab_widget)
        
    def setup_hotel_info_tab(self):
        layout = QVBoxLayout(self.hotel_info_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Hotel Information Form
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_layout = QFormLayout(form_frame)
        
        self.hotel_name = QLineEdit()
        self.hotel_address = QLineEdit()
        self.hotel_phone = QLineEdit()
        self.hotel_email = QLineEdit()
        self.hotel_website = QLineEdit()
        
        form_layout.addRow("Hotel Name:", self.hotel_name)
        form_layout.addRow("Hotel Address:", self.hotel_address)
        form_layout.addRow("Phone:", self.hotel_phone)
        form_layout.addRow("Email:", self.hotel_email)
        form_layout.addRow("Website:", self.hotel_website)
        
        layout.addWidget(form_frame)
        
        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.setObjectName("actionButton")
        save_btn.clicked.connect(self.save_hotel_info)
        layout.addWidget(save_btn)
        
        # Load existing settings
        self.load_hotel_info()
        
    def setup_room_rates_tab(self):
        layout = QVBoxLayout(self.room_rates_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Room Rates Table
        self.room_rates_table = QTableWidget()
        self.room_rates_table.setColumnCount(3)
        self.room_rates_table.setHorizontalHeaderLabels(["Room Type", "Night Rate", "Actions"])
        self.room_rates_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.room_rates_table.setObjectName("dataTable")
        layout.addWidget(self.room_rates_table)
        
        # Add Rate button
        add_btn = QPushButton("Add Room Rate")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self.add_room_rate)
        layout.addWidget(add_btn)
        
        # Load existing rates
        self.load_room_rates()
        
    def setup_services_tab(self):
        layout = QVBoxLayout(self.services_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Services Table
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(4)
        self.services_table.setHorizontalHeaderLabels(["Service Name", "Default Price", "Unit", "Actions"])
        self.services_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.services_table.setObjectName("dataTable")
        layout.addWidget(self.services_table)
        
        # Add Service button
        add_btn = QPushButton("Add Service")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self.add_service)
        layout.addWidget(add_btn)
        
        # Load existing services
        self.load_services()
        
    def setup_tax_rates_tab(self):
        layout = QVBoxLayout(self.tax_rates_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Tax Rates Table
        self.tax_rates_table = QTableWidget()
        self.tax_rates_table.setColumnCount(6)
        self.tax_rates_table.setHorizontalHeaderLabels([
            "Tax Name", "Type", "Value", "Apply to Rooms", "Apply to Services", "Actions"
        ])
        self.tax_rates_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.tax_rates_table.setObjectName("dataTable")
        layout.addWidget(self.tax_rates_table)
        
        # Add Tax Rate button
        add_btn = QPushButton("Add Tax Rate")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self.add_tax_rate)
        layout.addWidget(add_btn)
        
        # Load existing tax rates
        self.load_tax_rates()
        
    def load_hotel_info(self):
        settings = get_hotel_settings()
        if settings:
            self.hotel_name.setText(settings['hotel_name'] or '')
            self.hotel_address.setText(settings['hotel_address'] or '')
            self.hotel_phone.setText(settings['phone'] or '')
            self.hotel_email.setText(settings['email'] or '')
            self.hotel_website.setText(settings['website'] or '')
            
    def save_hotel_info(self):
        settings = {
            'hotel_name': self.hotel_name.text(),
            'hotel_address': self.hotel_address.text(),
            'phone': self.hotel_phone.text(),
            'email': self.hotel_email.text(),
            'website': self.hotel_website.text()
        }
        update_hotel_settings(settings)
        
    def load_room_rates(self):
        self.room_rates_table.setRowCount(0)
        rates = get_room_rates()
        
        for rate in rates:
            row = self.room_rates_table.rowCount()
            self.room_rates_table.insertRow(row)
            
            self.room_rates_table.setItem(row, 0, QTableWidgetItem(rate['room_type']))
            self.room_rates_table.setItem(row, 1, QTableWidgetItem(f"MAD {rate['night_rate']:.2f}"))
            
            # Add edit button
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("actionButton")
            edit_btn.clicked.connect(lambda _, r=rate: self.edit_room_rate(r))
            
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.addWidget(edit_btn)
            
            self.room_rates_table.setCellWidget(row, 2, actions_widget)
            
    def add_room_rate(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Room Rate")
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        room_type = QLineEdit()
        form.addRow("Room Type:", room_type)
        
        night_rate = QDoubleSpinBox()
        night_rate.setRange(0, 10000)
        night_rate.setDecimals(2)
        night_rate.setPrefix("MAD ")
        form.addRow("Night Rate:", night_rate)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            update_room_rate(room_type.text(), night_rate.value())
            self.load_room_rates()
            
    def edit_room_rate(self, rate):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Room Rate")
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        room_type = QLineEdit(rate['room_type'])
        form.addRow("Room Type:", room_type)
        
        night_rate = QDoubleSpinBox()
        night_rate.setRange(0, 10000)
        night_rate.setDecimals(2)
        night_rate.setPrefix("MAD ")
        night_rate.setValue(rate['night_rate'])
        form.addRow("Night Rate:", night_rate)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            update_room_rate(room_type.text(), night_rate.value())
            self.load_room_rates()
            
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
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
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
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
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
        
    def load_tax_rates(self):
        self.tax_rates_table.setRowCount(0)
        rates = get_tax_rates()
        
        for rate in rates:
            row = self.tax_rates_table.rowCount()
            self.tax_rates_table.insertRow(row)
            
            self.tax_rates_table.setItem(row, 0, QTableWidgetItem(rate['name']))
            self.tax_rates_table.setItem(row, 1, QTableWidgetItem(rate['tax_type'].capitalize()))
            
            # Display value based on tax type
            if rate['tax_type'] == 'percentage':
                value = f"{rate['percentage']}%"
            else:
                value = f"MAD {rate['amount']:.2f}"
            self.tax_rates_table.setItem(row, 2, QTableWidgetItem(value))
            
            # Add checkboxes for apply to rooms/services
            rooms_check = QCheckBox()
            rooms_check.setChecked(rate['apply_to_rooms'])
            rooms_check.stateChanged.connect(lambda state, r=rate: self.update_tax_rate_apply(r, 'rooms', state))
            self.tax_rates_table.setCellWidget(row, 3, rooms_check)
            
            services_check = QCheckBox()
            services_check.setChecked(rate['apply_to_services'])
            services_check.stateChanged.connect(lambda state, r=rate: self.update_tax_rate_apply(r, 'services', state))
            self.tax_rates_table.setCellWidget(row, 4, services_check)
            
            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("actionButton")
            edit_btn.clicked.connect(lambda _, r=rate: self.edit_tax_rate(r))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("actionButton")
            delete_btn.clicked.connect(lambda _, r=rate: self.delete_tax_rate(r))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            
            self.tax_rates_table.setCellWidget(row, 5, actions_widget)
            
    def add_tax_rate(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Tax Rate")
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        name = QLineEdit()
        form.addRow("Tax Name:", name)
        
        # Tax type selection
        tax_type = QComboBox()
        tax_type.addItems(["percentage", "fixed"])
        tax_type.currentTextChanged.connect(lambda: self.update_tax_value_widget(form, tax_type, percentage, amount))
        form.addRow("Tax Type:", tax_type)
        
        # Tax value widgets
        percentage = QDoubleSpinBox()
        percentage.setRange(0, 100)
        percentage.setDecimals(2)
        percentage.setSuffix("%")
        
        amount = QDoubleSpinBox()
        amount.setRange(0, 10000)
        amount.setDecimals(2)
        amount.setPrefix("MAD ")
        
        # Add initial value widget
        form.addRow("Value:", percentage)
        
        apply_to_rooms = QCheckBox()
        apply_to_rooms.setChecked(True)
        form.addRow("Apply to Room Charges:", apply_to_rooms)
        
        apply_to_services = QCheckBox()
        apply_to_services.setChecked(True)
        form.addRow("Apply to Services:", apply_to_services)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            tax_rate = {
                'name': name.text(),
                'tax_type': tax_type.currentText(),
                'percentage': percentage.value() if tax_type.currentText() == "percentage" else None,
                'amount': amount.value() if tax_type.currentText() == "fixed" else None,
                'apply_to_rooms': apply_to_rooms.isChecked(),
                'apply_to_services': apply_to_services.isChecked()
            }
            add_tax_rate(tax_rate)
            self.load_tax_rates()
            
    def edit_tax_rate(self, rate):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Tax Rate")
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        name = QLineEdit(rate['name'])
        form.addRow("Tax Name:", name)
        
        # Tax type selection
        tax_type = QComboBox()
        tax_type.addItems(["percentage", "fixed"])
        tax_type.setCurrentText(rate['tax_type'])
        tax_type.currentTextChanged.connect(lambda: self.update_tax_value_widget(form, tax_type, percentage, amount))
        form.addRow("Tax Type:", tax_type)
        
        # Tax value widgets
        percentage = QDoubleSpinBox()
        percentage.setRange(0, 100)
        percentage.setDecimals(2)
        percentage.setSuffix("%")
        percentage.setValue(rate['percentage'] if rate['percentage'] is not None else 0)
        
        amount = QDoubleSpinBox()
        amount.setRange(0, 10000)
        amount.setDecimals(2)
        amount.setPrefix("MAD ")
        amount.setValue(rate['amount'] if rate['amount'] is not None else 0)
        
        # Add initial value widget
        if rate['tax_type'] == 'percentage':
            form.addRow("Value:", percentage)
        else:
            form.addRow("Value:", amount)
        
        apply_to_rooms = QCheckBox()
        apply_to_rooms.setChecked(rate['apply_to_rooms'])
        form.addRow("Apply to Room Charges:", apply_to_rooms)
        
        apply_to_services = QCheckBox()
        apply_to_services.setChecked(rate['apply_to_services'])
        form.addRow("Apply to Services:", apply_to_services)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_rate = {
                'name': name.text(),
                'tax_type': tax_type.currentText(),
                'percentage': percentage.value() if tax_type.currentText() == "percentage" else None,
                'amount': amount.value() if tax_type.currentText() == "fixed" else None,
                'apply_to_rooms': apply_to_rooms.isChecked(),
                'apply_to_services': apply_to_services.isChecked()
            }
            update_tax_rate(rate['id'], updated_rate)
            self.load_tax_rates()
            
    def update_tax_value_widget(self, form, tax_type, percentage, amount):
        """Update the tax value widget based on selected tax type"""
        # Remove the current value widget
        for i in range(form.rowCount()):
            if form.itemAt(i, QFormLayout.ItemRole.FieldRole) and form.itemAt(i, QFormLayout.ItemRole.FieldRole).widget() in [percentage, amount]:
                form.removeRow(i)
                break
        
        # Add the appropriate widget
        if tax_type.currentText() == "percentage":
            form.addRow("Value:", percentage)
        else:
            form.addRow("Value:", amount)
            
    def update_tax_rate_apply(self, rate, field, state):
        updated_rate = dict(rate)
        if field == 'rooms':
            updated_rate['apply_to_rooms'] = bool(state)
        else:
            updated_rate['apply_to_services'] = bool(state)
        update_tax_rate(rate['id'], updated_rate)
        
    def delete_tax_rate(self, rate):
        delete_tax_rate(rate['id'])
        self.load_tax_rates() 