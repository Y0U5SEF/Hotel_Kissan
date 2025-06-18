from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QDateEdit, QComboBox, QFileDialog,
    QFormLayout, QFrame, QStackedWidget, QMessageBox
, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from PyQt6.QtGui import QIcon
from app.core.db import (
    get_filtered_reservations, get_filtered_checkins,
    get_all_guests, get_booking_services, get_services
)
from app.utils.report_exporter import export_checkins_pdf, export_checkins_xlsx
from app.ui.styles import MAIN_STYLESHEET
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
        self.load_btn.setObjectName("actionButton")
        self.export_pdf_btn = QPushButton("Export as PDF")
        self.export_pdf_btn.setObjectName("actionButton")
        self.export_xlsx_btn = QPushButton("Export as Excel")
        self.export_xlsx_btn.setObjectName("actionButton")

        # Set icons for export buttons
        self.export_pdf_btn.setIcon(QIcon(":/icons/pdf_48px.png"))
        self.export_xlsx_btn.setIcon(QIcon(":/icons/google_sheets_48px.png"))

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
        self.checkins_table.setColumnCount(7)
        self.checkins_table.setHorizontalHeaderLabels([
            "Check-in ID", "Guest Name", "ID/Passport", "Room", "Arrival", "Departure", "Status"
        ])
        self.checkins_table.setAlternatingRowColors(True)
        self.checkins_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.checkins_table.verticalHeader().setDefaultSectionSize(30)
        self.checkins_table.horizontalHeader().setStretchLastSection(True)
        self.checkins_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stacked_tables.addWidget(self.checkins_table)

        # Guests Table
        self.guests_table = QTableWidget()
        self.guests_table.setColumnCount(8)
        self.guests_table.setHorizontalHeaderLabels([
            "ID", "Name", "ID Type", "ID Number", "Phone", "Email", "Nationality", "VIP Status"
        ])
        self.guests_table.setAlternatingRowColors(True)
        self.guests_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.guests_table.verticalHeader().setDefaultSectionSize(30)
        self.guests_table.horizontalHeader().setStretchLastSection(True)
        self.guests_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stacked_tables.addWidget(self.guests_table)

        # Revenue Table
        self.revenue_table = QTableWidget()
        self.revenue_table.setColumnCount(7)
        self.revenue_table.setHorizontalHeaderLabels([
            "Booking ID", "Guest Name", "Room Type", "Check-in Date", "Check-out Date", "Room Revenue", "Services Revenue"
        ])
        self.revenue_table.setAlternatingRowColors(True)
        self.revenue_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.revenue_table.verticalHeader().setDefaultSectionSize(30)
        self.revenue_table.horizontalHeader().setStretchLastSection(True)
        self.revenue_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stacked_tables.addWidget(self.revenue_table)

        # Services Table
        self.services_table = QTableWidget()
        self.services_table.setColumnCount(6)
        self.services_table.setHorizontalHeaderLabels([
            "Service ID", "Service Name", "Default Price", "Unit", "Total Usage", "Total Revenue"
        ])
        self.services_table.setAlternatingRowColors(True)
        self.services_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.services_table.verticalHeader().setDefaultSectionSize(30)
        self.services_table.horizontalHeader().setStretchLastSection(True)
        self.services_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.stacked_tables.addWidget(self.services_table)

        layout.addWidget(self.stacked_tables)

    def load_report_data(self):
        try:
            # Show loading cursor
            self.setCursor(Qt.CursorShape.WaitCursor)
            
            # Get filter values
            from_date = self.date_from.date().toString("yyyy-MM-dd")
            to_date = self.date_to.date().toString("yyyy-MM-dd")
            room_type = self.room_type_filter.currentText()
            status = self.status_filter.currentText()
            report_type = self.report_type.currentText()

            # Validate date range
            if self.date_from.date() > self.date_to.date():
                QMessageBox.warning(self, "Invalid Date Range", "From date cannot be after To date")
                return

            # Clear current table
            current_table = self.stacked_tables.currentWidget()
            current_table.setRowCount(0)

            if report_type == "Reservations":
                self.status_filter.clear()
                self.status_filter.addItems(["All", "Confirmed", "Pending", "Cancelled"])
                self.status_filter.setEnabled(True)
                self.stacked_tables.setCurrentWidget(self.reservations_table)
                
                try:
                    reservations = get_filtered_reservations(from_date, to_date, room_type, status)
                    for record in reservations:
                        row = self.reservations_table.rowCount()
                        self.reservations_table.insertRow(row)
                        self.reservations_table.setItem(row, 0, QTableWidgetItem(str(record.get("reservation_id", ""))))
                        self.reservations_table.setItem(row, 1, QTableWidgetItem(f"{record.get('guest_first_name', '')} {record.get('guest_last_name', '')}"))
                        self.reservations_table.setItem(row, 2, QTableWidgetItem(record.get("room_type", "")))
                        self.reservations_table.setItem(row, 3, QTableWidgetItem(record.get("arrival_date", "")))
                        self.reservations_table.setItem(row, 4, QTableWidgetItem(str(record.get("num_guests", 0))))
                        self.reservations_table.setItem(row, 5, QTableWidgetItem(f"${record.get('deposit_amount', 0):.2f}"))
                        self.reservations_table.setItem(row, 6, QTableWidgetItem(record.get("status", "")))
                        self.reservations_table.setItem(row, 7, QTableWidgetItem(record.get("created_on", "")))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load reservations: {str(e)}")

            elif report_type == "Check-ins":
                self.status_filter.clear()
                self.status_filter.addItems(["All", "Checked-in", "Cancelled"])
                self.status_filter.setEnabled(True)
                self.stacked_tables.setCurrentWidget(self.checkins_table)
                
                try:
                    checkins = get_filtered_checkins(from_date, to_date, room_type, status)
                    for record in checkins:
                        row = self.checkins_table.rowCount()
                        self.checkins_table.insertRow(row)
                        self.checkins_table.setItem(row, 0, QTableWidgetItem(str(record.get("checkin_id", ""))))
                        self.checkins_table.setItem(row, 1, QTableWidgetItem(record.get("guest_name", "")))
                        self.checkins_table.setItem(row, 2, QTableWidgetItem(record.get("id_number", "")))
                        self.checkins_table.setItem(row, 3, QTableWidgetItem(record.get("room_number", "")))
                        self.checkins_table.setItem(row, 4, QTableWidgetItem(record.get("arrival_date", "")))
                        self.checkins_table.setItem(row, 5, QTableWidgetItem(record.get("departure_date", "")))
                        self.checkins_table.setItem(row, 6, QTableWidgetItem(record.get("status", "")))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load check-ins: {str(e)}")

            elif report_type == "Check-outs":
                self.status_filter.clear()
                self.status_filter.setEnabled(False)
                self.stacked_tables.setCurrentWidget(self.checkins_table)
                
                try:
                    checkouts = get_filtered_checkins(from_date, to_date, room_type, status="checked_out")
                    for record in checkouts:
                        row = self.checkins_table.rowCount()
                        self.checkins_table.insertRow(row)
                        self.checkins_table.setItem(row, 0, QTableWidgetItem(str(record.get("checkin_id", ""))))
                        self.checkins_table.setItem(row, 1, QTableWidgetItem(record.get("guest_name", "")))
                        self.checkins_table.setItem(row, 2, QTableWidgetItem(record.get("id_number", "")))
                        self.checkins_table.setItem(row, 3, QTableWidgetItem(record.get("room_number", "")))
                        self.checkins_table.setItem(row, 4, QTableWidgetItem(record.get("arrival_date", "")))
                        self.checkins_table.setItem(row, 5, QTableWidgetItem(record.get("departure_date", "")))
                        self.checkins_table.setItem(row, 6, QTableWidgetItem(record.get("status", "")))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load check-outs: {str(e)}")

            elif report_type == "Guests":
                self.status_filter.clear()
                self.status_filter.setEnabled(False)
                self.stacked_tables.setCurrentWidget(self.guests_table)
                
                try:
                    guests = get_all_guests()
                    for guest in guests:
                        row = self.guests_table.rowCount()
                        self.guests_table.insertRow(row)
                        self.guests_table.setItem(row, 0, QTableWidgetItem(str(guest.get("id", ""))))
                        self.guests_table.setItem(row, 1, QTableWidgetItem(f"{guest.get('first_name', '')} {guest.get('last_name', '')}"))
                        self.guests_table.setItem(row, 2, QTableWidgetItem(guest.get("id_type", "")))
                        self.guests_table.setItem(row, 3, QTableWidgetItem(guest.get("id_number", "")))
                        self.guests_table.setItem(row, 4, QTableWidgetItem(f"{guest.get('phone_code', '')} {guest.get('phone_number', '')}"))
                        self.guests_table.setItem(row, 5, QTableWidgetItem(guest.get("email", "")))
                        self.guests_table.setItem(row, 6, QTableWidgetItem(guest.get("nationality", "")))
                        self.guests_table.setItem(row, 7, QTableWidgetItem(guest.get("vip_status", "")))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load guests: {str(e)}")

            elif report_type == "Revenue":
                self.status_filter.clear()
                self.status_filter.setEnabled(False)
                self.stacked_tables.setCurrentWidget(self.revenue_table)
                
                try:
                    checkins = get_filtered_checkins(from_date, to_date, room_type)
                    for record in checkins:
                        row = self.revenue_table.rowCount()
                        self.revenue_table.insertRow(row)
                        self.revenue_table.setItem(row, 0, QTableWidgetItem(str(record.get("checkin_id", ""))))
                        self.revenue_table.setItem(row, 1, QTableWidgetItem(record.get("guest_name", "")))
                        self.revenue_table.setItem(row, 2, QTableWidgetItem(record.get("room_type", "")))
                        self.revenue_table.setItem(row, 3, QTableWidgetItem(record.get("arrival_date", "")))
                        self.revenue_table.setItem(row, 4, QTableWidgetItem(record.get("departure_date", "")))
                        self.revenue_table.setItem(row, 5, QTableWidgetItem(f"${record.get('total_paid', 0):.2f}"))
                        
                        # Get services revenue
                        try:
                            services = get_booking_services(record.get("checkin_id"))
                            services_revenue = sum(service.get("total_charge", 0) for service in services)
                            self.revenue_table.setItem(row, 6, QTableWidgetItem(f"${services_revenue:.2f}"))
                        except Exception as e:
                            self.revenue_table.setItem(row, 6, QTableWidgetItem("$0.00"))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load revenue data: {str(e)}")

            elif report_type == "Services":
                self.status_filter.clear()
                self.status_filter.setEnabled(False)
                self.stacked_tables.setCurrentWidget(self.services_table)
                
                try:
                    services = get_services()
                    for service in services:
                        row = self.services_table.rowCount()
                        self.services_table.insertRow(row)
                        self.services_table.setItem(row, 0, QTableWidgetItem(str(service.get("id", ""))))
                        self.services_table.setItem(row, 1, QTableWidgetItem(service.get("name", "")))
                        self.services_table.setItem(row, 2, QTableWidgetItem(f"${service.get('default_price', 0):.2f}"))
                        self.services_table.setItem(row, 3, QTableWidgetItem(service.get("unit", "")))
                        
                        # Calculate total usage and revenue
                        try:
                            total_usage = 0
                            total_revenue = 0
                            checkins = get_filtered_checkins(from_date, to_date)
                            for checkin in checkins:
                                booking_services = get_booking_services(checkin.get("checkin_id"))
                                for booking_service in booking_services:
                                    if booking_service.get("service_id") == service.get("id"):
                                        total_usage += booking_service.get("quantity", 0)
                                        total_revenue += booking_service.get("total_charge", 0)
                            
                            self.services_table.setItem(row, 4, QTableWidgetItem(str(total_usage)))
                            self.services_table.setItem(row, 5, QTableWidgetItem(f"${total_revenue:.2f}"))
                        except Exception as e:
                            self.services_table.setItem(row, 4, QTableWidgetItem("0"))
                            self.services_table.setItem(row, 5, QTableWidgetItem("$0.00"))
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to load services data: {str(e)}")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {str(e)}")
        finally:
            # Reset cursor
            self.setCursor(Qt.CursorShape.ArrowCursor)

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
