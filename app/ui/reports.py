from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDateEdit, QComboBox, QFileDialog,
    QFormLayout, QFrame, QStackedWidget
, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from app.core.db import get_filtered_reservations, get_filtered_checkins
from app.utils.report_exporter import export_checkins_pdf, export_checkins_xlsx
import os

class ReportsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # --- Filters Section ---
        filter_frame = QFrame()
        filter_layout = QVBoxLayout(filter_frame)

        # Report type selector
        self.report_type = QComboBox()
        self.report_type.addItems(["Reservations", "Check-ins", "Check-outs", "Guests", "Revenue", "Services"])
        self.report_type.currentIndexChanged.connect(self.load_report_data)
        filter_layout.addWidget(self.report_type)

        # From and To Dates
        date_layout = QHBoxLayout()
        from_layout = QVBoxLayout()
        from_label = QLabel("From Date:")
        self.date_from = QDateEdit()
        self.date_from.setCalendarPopup(True)
        self.date_from.setDate(QDate.currentDate().addMonths(-1))
        from_layout.addWidget(from_label)
        from_layout.addWidget(self.date_from)

        to_layout = QVBoxLayout()
        to_label = QLabel("To Date:")
        self.date_to = QDateEdit()
        self.date_to.setCalendarPopup(True)
        self.date_to.setDate(QDate.currentDate())
        to_layout.addWidget(to_label)
        to_layout.addWidget(self.date_to)

        date_layout.addLayout(from_layout)
        date_layout.addLayout(to_layout)
        filter_layout.addLayout(date_layout)

        form_layout = QFormLayout()
        self.room_type_filter = QComboBox()
        self.room_type_filter.addItem("All")
        self.room_type_filter.addItems(["Single", "Double", "Suite", "Deluxe"])

        self.status_filter = QComboBox()
        filter_layout.addLayout(form_layout)
        form_layout.addRow("Room Type:", self.room_type_filter)
        form_layout.addRow("Status:", self.status_filter)

        layout.addWidget(filter_frame)

        # --- Buttons ---
        button_layout = QHBoxLayout()
        self.load_btn = QPushButton("Load Report")
        self.export_pdf_btn = QPushButton("Export as PDF")
        self.export_xlsx_btn = QPushButton("Export as Excel")

        self.load_btn.clicked.connect(self.load_report_data)
        self.export_pdf_btn.clicked.connect(self.export_pdf)
        self.export_xlsx_btn.clicked.connect(self.export_xlsx)

        button_layout.addWidget(self.load_btn)
        button_layout.addStretch()
        button_layout.addWidget(self.export_pdf_btn)
        button_layout.addWidget(self.export_xlsx_btn)

        layout.addLayout(button_layout)

        # --- Table Preview (Stacked for multiple types) ---
        self.stacked_tables = QStackedWidget()

        # Reservations Table
        self.reservations_table = QTableWidget()
        self.reservations_table.setColumnCount(8)
        self.reservations_table.setHorizontalHeaderLabels([
            "Reservation ID", "Guest Name", "Room Type", "Arrival",
            "Guests", "Deposit", "Status", "Created On"
        ])
        self.reservations_table.setAlternatingRowColors(True)
        self.reservations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.reservations_table.verticalHeader().setDefaultSectionSize(30)
        self.reservations_table.horizontalHeader().setStretchLastSection(True)
        self.reservations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stacked_tables.addWidget(self.reservations_table)

        # Check-ins Table
        self.checkins_table = QTableWidget()
        self.checkins_table.setColumnCount(6)
        self.checkins_table.setHorizontalHeaderLabels([
            "Check-in ID", "Guest Name", "Room", "Arrival", "Departure", "Status"
        ])
        self.checkins_table.setAlternatingRowColors(True)
        self.checkins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.checkins_table.verticalHeader().setDefaultSectionSize(30)
        self.checkins_table.horizontalHeader().setStretchLastSection(True)
        self.checkins_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stacked_tables.addWidget(self.checkins_table)

        layout.addWidget(self.stacked_tables)

    def load_report_data(self):
        from_date = self.date_from.date().toString("yyyy-MM-dd")
        to_date = self.date_to.date().toString("yyyy-MM-dd")
        room_type = self.room_type_filter.currentText()
        status = self.status_filter.currentText()
        report_type = self.report_type.currentText()

        if report_type == "Reservations":
            self.status_filter.clear()
            self.status_filter.addItems(["All", "Confirmed", "Pending", "Cancelled"])
            self.stacked_tables.setCurrentWidget(self.reservations_table)
            self.reservations_table.setRowCount(0)
            reservations = get_filtered_reservations(from_date, to_date, room_type, status)
            for record in reservations:
                row = self.reservations_table.rowCount()
                self.reservations_table.insertRow(row)
                self.reservations_table.setItem(row, 0, QTableWidgetItem(record.get("reservation_id", "")))
                self.reservations_table.setItem(row, 1, QTableWidgetItem(f"{record.get('guest_first_name', '')} {record.get('guest_last_name', '')}"))
                self.reservations_table.setItem(row, 2, QTableWidgetItem(record.get("room_type", "")))
                self.reservations_table.setItem(row, 3, QTableWidgetItem(record.get("arrival_date", "")))
                self.reservations_table.setItem(row, 4, QTableWidgetItem(str(record.get("num_guests", ""))))
                self.reservations_table.setItem(row, 5, QTableWidgetItem(str(record.get("deposit_amount", ""))))
                self.reservations_table.setItem(row, 6, QTableWidgetItem(record.get("status", "")))
                self.reservations_table.setItem(row, 7, QTableWidgetItem(record.get("created_on", "")))

        elif report_type == "Check-ins":
            self.status_filter.clear()
            self.status_filter.addItems(["All", "Checked-in", "Checked-out", "Cancelled"])
            self.stacked_tables.setCurrentWidget(self.checkins_table)
            self.checkins_table.setRowCount(0)
            checkins = get_filtered_checkins(from_date, to_date, room_type)
            for record in checkins:
                row = self.checkins_table.rowCount()
                self.checkins_table.insertRow(row)
                self.checkins_table.setItem(row, 0, QTableWidgetItem(record.get("checkin_id", "")))
                self.checkins_table.setItem(row, 1, QTableWidgetItem(record.get("guest_name", "")))
                self.checkins_table.setItem(row, 2, QTableWidgetItem(record.get("room_number", "")))
                self.checkins_table.setItem(row, 3, QTableWidgetItem(record.get("arrival_date", "")))
                self.checkins_table.setItem(row, 4, QTableWidgetItem(record.get("departure_date", "")))
                self.checkins_table.setItem(row, 5, QTableWidgetItem(record.get("status", "")))
                

        elif report_type == "Check-outs":
            self.status_filter.clear()
            self.stacked_tables.setCurrentWidget(self.checkins_table)
            self.checkins_table.setRowCount(0)
            checkouts = get_filtered_checkins(from_date, to_date, room_type, status="Checked-out")
            for record in checkouts:
                row = self.checkins_table.rowCount()
                self.checkins_table.insertRow(row)
                self.checkins_table.setItem(row, 0, QTableWidgetItem(record.get("checkin_id", "")))
                self.checkins_table.setItem(row, 1, QTableWidgetItem(record.get("guest_name", "")))
                self.checkins_table.setItem(row, 2, QTableWidgetItem(record.get("room_number", "")))
                self.checkins_table.setItem(row, 3, QTableWidgetItem(record.get("arrival_date", "")))
                self.checkins_table.setItem(row, 4, QTableWidgetItem(record.get("departure_date", "")))
                self.checkins_table.setItem(row, 5, QTableWidgetItem(record.get("status", "")))
                self.checkins_table.setItem(row, 6, QTableWidgetItem(record.get("payment_status", "")))

    def export_pdf(self):
        report_type = self.report_type.currentText().replace(" ", "_").lower()
        from_date = self.date_from.date().toString("yyyyMMdd")
        to_date = self.date_to.date().toString("yyyyMMdd")
        default_name = f"{report_type}_{from_date}_to_{to_date}.pdf"
        path, _ = QFileDialog.getSaveFileName(self, "Export PDF", default_name, "PDF Files (*.pdf)")
        if path:
            table = self.stacked_tables.currentWidget()
            export_checkins_pdf(table, path)

    def export_xlsx(self):
        report_type = self.report_type.currentText().replace(" ", "_").lower()
        from_date = self.date_from.date().toString("yyyyMMdd")
        to_date = self.date_to.date().toString("yyyyMMdd")
        default_name = f"{report_type}_{from_date}_to_{to_date}.xlsx"
        path, _ = QFileDialog.getSaveFileName(self, "Export Excel", default_name, "Excel Files (*.xlsx)")
        if path:
            table = self.stacked_tables.currentWidget()
            export_checkins_xlsx(table, path)
