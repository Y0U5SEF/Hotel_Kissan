from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QLineEdit, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QComboBox, QCheckBox, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon, QColor, QPainter, QPixmap
from app.core.db import (
    get_hotel_settings, update_hotel_settings,
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
        self.tax_rates_table.verticalHeader().setDefaultSectionSize(50)
        self.tax_rates_table.setAlternatingRowColors(True)
        self.tax_rates_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

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
            
            # Create status indicators for rooms and services
            rooms_indicator = QLabel()
            rooms_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            rooms_pixmap = self.create_status_indicator(rate['apply_to_rooms'])
            rooms_indicator.setPixmap(rooms_pixmap)
            self.tax_rates_table.setCellWidget(row, 3, rooms_indicator)
            
            services_indicator = QLabel()
            services_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
            services_pixmap = self.create_status_indicator(rate['apply_to_services'])
            services_indicator.setPixmap(services_pixmap)
            self.tax_rates_table.setCellWidget(row, 4, services_indicator)
            
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
            
    def create_status_indicator(self, is_active):
        """Create a colored dot indicator for status"""
        size = 16
        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)
        
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Draw circle
        color = QColor("#4CAF50") if is_active else QColor("#9E9E9E")
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(2, 2, size-4, size-4)
        painter.end()
        
        return pixmap
        
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