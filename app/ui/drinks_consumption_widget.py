from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QSpinBox, QDoubleSpinBox, QPushButton, 
                             QDateEdit, QTextEdit, QMessageBox, QTableWidget, 
                             QTableWidgetItem, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from datetime import datetime
from app.services.drinks_service import DrinksService
from app.models.customer import Customer

class DrinksConsumptionWidget(QWidget):
    def __init__(self, db_session, parent=None):
        super().__init__(parent)
        self.db = db_session
        self.drinks_service = DrinksService(db_session)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Customer selection
        customer_layout = QHBoxLayout()
        customer_label = QLabel("Select Customer:")
        self.customer_combo = QComboBox()
        self.load_customers()
        customer_layout.addWidget(customer_label)
        customer_layout.addWidget(self.customer_combo)
        layout.addLayout(customer_layout)

        # Drink details
        drink_layout = QHBoxLayout()
        self.drink_name = QTextEdit()
        self.drink_name.setMaximumHeight(30)
        self.drink_name.setPlaceholderText("Drink Name")
        self.quantity = QSpinBox()
        self.quantity.setMinimum(1)
        self.quantity.setMaximum(100)
        self.price = QDoubleSpinBox()
        self.price.setMinimum(0.0)
        self.price.setMaximum(1000.0)
        self.price.setDecimals(2)
        
        drink_layout.addWidget(self.drink_name)
        drink_layout.addWidget(self.quantity)
        drink_layout.addWidget(self.price)
        layout.addLayout(drink_layout)

        # Date selection
        date_layout = QHBoxLayout()
        date_label = QLabel("Date:")
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(date_label)
        date_layout.addWidget(self.date_edit)
        layout.addLayout(date_layout)

        # Add consumption button
        add_button = QPushButton("Add Consumption")
        add_button.clicked.connect(self.add_consumption)
        layout.addWidget(add_button)

        # Generate bill button
        bill_button = QPushButton("Generate Customer Bill")
        bill_button.clicked.connect(self.generate_customer_bill)
        layout.addWidget(bill_button)

        # Generate global invoice button
        invoice_button = QPushButton("Generate Global Invoice")
        invoice_button.clicked.connect(self.generate_global_invoice)
        layout.addWidget(invoice_button)

        # Consumption history table
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(5)
        self.history_table.setHorizontalHeaderLabels([
            "Date", "Drink", "Quantity", "Price", "Total"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.history_table)

        self.setLayout(layout)
        self.update_history_table()

    def load_customers(self):
        customers = self.db.query(Customer).all()
        self.customer_combo.clear()
        for customer in customers:
            self.customer_combo.addItem(f"{customer.name} ({customer.id})", customer.id)

    def add_consumption(self):
        try:
            customer_id = self.customer_combo.currentData()
            drink_name = self.drink_name.toPlainText()
            quantity = self.quantity.value()
            price = self.price.value()
            date = self.date_edit.date().toPyDate()

            if not drink_name:
                QMessageBox.warning(self, "Error", "Please enter a drink name")
                return

            self.drinks_service.add_drink_consumption(
                customer_id=customer_id,
                drink_name=drink_name,
                quantity=quantity,
                price_per_unit=price,
                consumption_date=datetime.combine(date, datetime.min.time())
            )

            self.update_history_table()
            self.drink_name.clear()
            self.quantity.setValue(1)
            self.price.setValue(0.0)

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def update_history_table(self):
        customer_id = self.customer_combo.currentData()
        consumptions = self.drinks_service.get_customer_consumptions(customer_id)
        
        self.history_table.setRowCount(len(consumptions))
        for i, consumption in enumerate(consumptions):
            self.history_table.setItem(i, 0, QTableWidgetItem(
                consumption.consumption_date.strftime("%Y-%m-%d %H:%M")))
            self.history_table.setItem(i, 1, QTableWidgetItem(consumption.drink_name))
            self.history_table.setItem(i, 2, QTableWidgetItem(str(consumption.quantity)))
            self.history_table.setItem(i, 3, QTableWidgetItem(f"${consumption.price_per_unit:.2f}"))
            self.history_table.setItem(i, 4, QTableWidgetItem(f"${consumption.total_price:.2f}"))

    def generate_customer_bill(self):
        try:
            customer_id = self.customer_combo.currentData()
            bill = self.drinks_service.generate_customer_bill(customer_id)
            
            # Here you would typically show a bill preview or save it as PDF
            QMessageBox.information(
                self, 
                "Bill Generated", 
                f"Bill generated for {bill['customer']['name']}\n"
                f"Total Amount: ${bill['total_amount']:.2f}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

    def generate_global_invoice(self):
        try:
            invoice = self.drinks_service.generate_global_invoice()
            
            # Here you would typically show an invoice preview or save it as PDF
            QMessageBox.information(
                self, 
                "Global Invoice Generated", 
                f"Total Amount: ${invoice['total_amount']:.2f}\n"
                f"Number of Customers: {len(invoice['customers'])}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e)) 