from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QLineEdit, QComboBox, QDateEdit, QCalendarWidget, QFormLayout, QStackedWidget, QCompleter, QGridLayout, QMessageBox,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QCheckBox, QFrame, QSizePolicy, QSpinBox, QTextEdit
)
from PyQt6.QtCore import Qt, QDate, pyqtSignal, QStringListModel
from PyQt6.QtGui import QIcon, QColor, QTextCharFormat, QFont
from app.core.db import get_all_guests, get_all_rooms, update_room, get_reservations, add_reservation, update_reservation, delete_reservation, get_room_rates
from datetime import datetime
import uuid
from fpdf import FPDF
import os

class ReservationsWidget(QWidget):
    """Widget for managing hotel reservations"""
    
    # Signal for guest deletion
    guest_deleted = pyqtSignal()
    # Signal for room status changes
    room_status_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.reservation_id = str(uuid.uuid4())[:8]  # Initialize reservation ID
        self.setup_ui()
        
        # Connect to the guest deletion signal from the main window
        if parent and hasattr(parent, 'guest_deleted'):
            parent.guest_deleted.connect(self.refresh_guest_lists)

        # Connect to room status changes
        if parent and hasattr(parent, 'room_status_changed'):
            parent.room_status_changed.connect(self.update_room_selection)
            
        # Connect to room status changes
        if parent and hasattr(parent, 'room_status_changed'):
            parent.room_status_changed.connect(self.update_room_selection)

    def refresh_guest_lists(self):
        """Refresh all guest dropdowns and lists"""
        # Refresh the guest dropdown in new reservation tab
        if hasattr(self, 'guest_select_combo'):
            self.populate_guest_combo()
            # If there's search text, reapply the filter
            if hasattr(self, 'guest_search') and self.guest_search.text():
                self.filter_guest_dropdown()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Reservations")
        title_label.setObjectName("pageTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        main_layout.addLayout(header_layout)

        # Tabs for different features
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North)
        self.tab_widget.currentChanged.connect(self.on_tab_changed)  # Connect tab change signal
        
        # Set size policy for tab widget
        self.tab_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        main_layout.addWidget(self.tab_widget)

        # Reservations List Tab
        self.reservations_list_tab = QWidget()
        self.setup_reservations_list_tab()
        self.tab_widget.addTab(self.reservations_list_tab, QIcon(":/icons/list.png"), "Reservations List")
        
        # Load existing reservations
        self.load_reservations()

        # Calendar View Tab
        self.calendar_tab = QWidget()
        self.setup_calendar_tab()
        self.tab_widget.addTab(self.calendar_tab, QIcon(":/icons/calendar.png"), "Calendar View")

        # New Reservation Tab
        self.new_reservation_tab = QWidget()
        self.setup_new_reservation_tab()
        self.tab_widget.addTab(self.new_reservation_tab, QIcon(":/icons/add_booking.png"), "New Reservation")

        # Cancellations Tab
        self.cancel_tab = QWidget()
        self.setup_cancellations_tab()
        self.tab_widget.addTab(self.cancel_tab, QIcon(":/icons/cancel.png"), "Cancellations")

    def on_tab_changed(self, index):
        """Handle tab change events"""
        # Get the tab name
        tab_name = self.tab_widget.tabText(index)
        
        # If switching to New Reservation tab, refresh the guest dropdown
        if tab_name == "New Reservation":
            self.populate_guest_combo()
            # If there's search text, reapply the filter
            if hasattr(self, 'guest_search') and self.guest_search.text():
                self.filter_guest_dropdown()
        # If switching to Reservations List tab, refresh the reservations
        elif tab_name == "Reservations List":
            self.load_reservations()

    def setup_reservations_list_tab(self):
        # Create main layout with proper size policy
        layout = QVBoxLayout(self.reservations_list_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Search and filter bar
        filter_frame = QFrame()
        filter_frame.setObjectName("filterFrame")
        filter_layout = QHBoxLayout(filter_frame)
        filter_layout.setContentsMargins(0, 0, 0, 0)  # Add consistent margins
        filter_layout.setSpacing(10)  # Add consistent spacing
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by guest, reservation #, date...")
        filter_layout.addWidget(self.search_input)
        
        # Arrival date filter
        self.filter_arrival = QDateEdit()
        self.filter_arrival.setCalendarPopup(True)
        self.filter_arrival.setDisplayFormat("yyyy-MM-dd")
        self.filter_arrival.setDate(QDate.currentDate())
        filter_layout.addWidget(QLabel("Arrival:"))
        filter_layout.addWidget(self.filter_arrival)
        
        # Status filter
        self.filter_status = QComboBox()
        self.filter_status.addItems(["All Statuses", "Confirmed", "Pending", "Cancelled"])
        filter_layout.addWidget(QLabel("Status:"))
        filter_layout.addWidget(self.filter_status)
        
        # Clear filters button
        clear_filters_btn = QPushButton("Clear Filters")
        clear_filters_btn.setObjectName("actionButton")
        clear_filters_btn.clicked.connect(self.clear_filters)
        filter_layout.addWidget(clear_filters_btn)
        
        layout.addWidget(filter_frame)
        
        # ===== KEY FIXES FOR TABLE SHRINKING =====
        
        # Reservations table - Direct addition to main layout
        self.reservations_table = QTableWidget()
        self.reservations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.reservations_table.setAlternatingRowColors(True)
        self.reservations_table.setColumnCount(7)  # Reduced from 8 to 7 columns
        self.reservations_table.verticalHeader().setDefaultSectionSize(50)
        self.reservations_table.setHorizontalHeaderLabels([
            "Reservation #", "Guest Name", "Arrival", "Room Type", "Status", "Created On", "Actions"
        ])
        
        # CRITICAL FIX: Set proper size policies and constraints
        self.reservations_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.reservations_table.setMinimumHeight(400)  # Set minimum height
        self.reservations_table.setMinimumWidth(800)   # Set minimum width
        
        # CRITICAL FIX: Use Stretch mode for consistent column sizing
        self.reservations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        # CRITICAL FIX: Add table directly to main layout with stretch factor
        layout.addWidget(self.reservations_table, 1)  # Stretch factor = 1
        
        # Connect filter signals
        self.search_input.textChanged.connect(self.filter_reservations)
        self.filter_arrival.dateChanged.connect(self.filter_reservations)
        self.filter_status.currentIndexChanged.connect(self.filter_reservations)

    def clear_filters(self):
        """Clear all filters and show all reservations"""
        # Clear search text
        self.search_input.clear()
        
        # Reset date filters to current date
        current_date = QDate.currentDate()
        self.filter_arrival.setDate(current_date)
        
        # Reset combo boxes to first item
        self.filter_status.setCurrentIndex(0)
        
        # Show all rows
        for row in range(self.reservations_table.rowCount()):
            self.reservations_table.setRowHidden(row, False)
        
        # Reload all reservations to ensure we have the complete dataset
        self.load_reservations()

    def load_reservations(self):
        """Load reservations from database and display in table"""
        # Clear existing rows
        self.reservations_table.setRowCount(0)
        
        # Get reservations from database
        reservations = get_reservations()
        rooms = {str(room['id']): room for room in get_all_rooms()}
        
        # Add each reservation to the table
        for row, reservation in enumerate(reservations):
            self.reservations_table.insertRow(row)
            
            # Reservation ID
            self.reservations_table.setItem(row, 0, QTableWidgetItem(reservation['reservation_id']))
            
            # Guest Name
            guest_name = f"{reservation['guest_first_name']} {reservation['guest_last_name']}"
            self.reservations_table.setItem(row, 1, QTableWidgetItem(guest_name))
            
            # Arrival Date
            self.reservations_table.setItem(row, 2, QTableWidgetItem(reservation['arrival_date']))
            
            # Room Type (from room record)
            room_type = rooms.get(str(reservation.get('room_id')), {}).get('type', '')
            self.reservations_table.setItem(row, 3, QTableWidgetItem(room_type))
            
            # Status
            self.reservations_table.setItem(row, 4, QTableWidgetItem(reservation['status']))
            
            # Created On
            self.reservations_table.setItem(row, 5, QTableWidgetItem(reservation['created_on']))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(10)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("tableActionButton")
            edit_btn.setProperty("action", "edit")
            edit_btn.setFixedWidth(80)
            edit_btn.clicked.connect(lambda _, r=reservation: self.edit_reservation(r))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("tableActionButton")
            delete_btn.setProperty("action", "delete")
            delete_btn.setFixedWidth(80)
            delete_btn.clicked.connect(lambda _, r=reservation: self.delete_reservation(r))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            actions_layout.addStretch()
            
            self.reservations_table.setCellWidget(row, 6, actions_widget)
        
        # Connect search and filter signals if not already connected
        if not hasattr(self, 'search_connected'):
            self.search_input.textChanged.connect(self.filter_reservations)
            self.filter_arrival.dateChanged.connect(self.filter_reservations)
            self.filter_status.currentIndexChanged.connect(self.filter_reservations)
            self.search_connected = True

    def filter_reservations(self):
        """Filter reservations based on search text and filters"""
        search_text = self.search_input.text().lower()
        arrival_date = self.filter_arrival.date().toString('yyyy-MM-dd')
        status = self.filter_status.currentText()
        
        for row in range(self.reservations_table.rowCount()):
            show_row = True
            
            # Check search text
            if search_text:
                search_match = False
                for col in range(self.reservations_table.columnCount() - 1):  # Exclude actions column
                    item = self.reservations_table.item(row, col)
                    if item and search_text in item.text().lower():
                        search_match = True
                        break
                if not search_match:
                    show_row = False
            
            # Check arrival date
            if arrival_date and show_row:
                item = self.reservations_table.item(row, 2)  # Arrival date column
                if item:
                    item_date = item.text()
                    if item_date < arrival_date:
                        show_row = False
            
            # Check status
            if status != "All Statuses" and show_row:
                item = self.reservations_table.item(row, 4)  # Status column
                if item and item.text() != status:
                    show_row = False
            
            self.reservations_table.setRowHidden(row, not show_row)
        
        # Update the table view
        self.reservations_table.viewport().update()

    def setup_calendar_tab(self):
        layout = QVBoxLayout(self.calendar_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Calendar controls
        controls_layout = QHBoxLayout()
        
        # Status filter
        self.calendar_status = QComboBox()
        self.calendar_status.addItems(["All Statuses", "Confirmed", "Pending", "Cancelled", "Checked-in"])
        self.calendar_status.currentTextChanged.connect(self.update_calendar_view)
        controls_layout.addWidget(QLabel("Status:"))
        controls_layout.addWidget(self.calendar_status)
        
        # Guest filter
        self.guest_filter = QLineEdit()
        self.guest_filter.setPlaceholderText("Filter by guest name...")
        
        # Add completer for guest names
        self.guest_completer = QCompleter()
        self.guest_completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.guest_completer.setFilterMode(Qt.MatchFlag.MatchContains)
        self.guest_filter.setCompleter(self.guest_completer)
        
        # Update completer list when text changes
        self.guest_filter.textChanged.connect(self.update_guest_completer)
        self.guest_filter.textChanged.connect(self.update_calendar_view)
        controls_layout.addWidget(QLabel("Guest:"))
        controls_layout.addWidget(self.guest_filter)
        
        # Today button
        today_btn = QPushButton("Today")
        today_btn.setObjectName("actionButton")
        today_btn.clicked.connect(lambda: self.calendar.setSelectedDate(QDate.currentDate()))
        controls_layout.addWidget(today_btn)
        
        # Clear filters button
        clear_filters_btn = QPushButton("Clear Filters")
        clear_filters_btn.setObjectName("actionButton")
        clear_filters_btn.clicked.connect(self.clear_calendar_filters)
        controls_layout.addWidget(clear_filters_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)

        # Calendar widget (top)
        calendar_container = QFrame()
        calendar_container.setObjectName("calendarFrame")
        calendar_container_layout = QVBoxLayout(calendar_container)
        
        self.calendar = QCalendarWidget()
        self.calendar.setGridVisible(True)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.VerticalHeaderFormat.ISOWeekNumbers)
        self.calendar.setHorizontalHeaderFormat(QCalendarWidget.HorizontalHeaderFormat.LongDayNames)
        
        # Customize calendar appearance
        self.calendar.setStyleSheet("""
            QCalendarWidget QToolButton {
                height: 30px;
                width: 100px;
                color: #2c3e50;
                font-size: 14px;
                icon-size: 20px, 20px;
                background-color: #ecf0f1;
            }
            QCalendarWidget QMenu {
                width: 150px;
                left: 20px;
                color: #2c3e50;
            }
            QCalendarWidget QSpinBox {
                width: 60px;
                font-size: 14px;
                color: #2c3e50;
                background-color: #ecf0f1;
                selection-background-color: #3498db;
                selection-color: white;
            }
            QCalendarWidget QAbstractItemView:enabled {
                font-size: 18px;
                color: #2c3e50;
                background-color: white;
                selection-background-color: #3498db;
                selection-color: white;
            }
        """)
        
        # Connect signals
        self.calendar.clicked.connect(self.show_reservation_details)
        self.calendar.currentPageChanged.connect(self.update_calendar_highlights)
        
        calendar_container_layout.addWidget(self.calendar)
        layout.addWidget(calendar_container)  # Calendar takes full width

        # Room availability grid (bottom)
        availability_container = QFrame()
        availability_container.setVisible(False)
        availability_container.setObjectName("availabilityFrame")
        availability_layout = QVBoxLayout(availability_container)
        
        availability_label = QLabel("Room Availability")
        availability_label.setObjectName("sectionTitle")
        availability_layout.addWidget(availability_label)
        
        # Room availability table
        self.availability_table = QTableWidget()
        self.availability_table.verticalHeader().setDefaultAlignment(Qt.AlignmentFlag.AlignCenter)
        self.availability_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)  # Make cells read-only
        self.availability_table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)  # Disable selection
        self.availability_table.setColumnCount(0)  # Will be set dynamically
        self.availability_table.setRowCount(0)     # Will be set dynamically
        self.availability_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.availability_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Fixed)
        self.availability_table.verticalHeader().setDefaultSectionSize(30)
        self.availability_table.setAlternatingRowColors(False)
        self.availability_table.cellClicked.connect(self.on_availability_cell_clicked)
        self.availability_table.setStyleSheet("""
            QTableWidget {
                padding: 0px;
            }
            QTableWidget QHeaderView::section:vertical {
                padding: 0px;
                text-align: center;
                font-size: 10pt;
            }   
        """)
        availability_layout.addWidget(self.availability_table)
        
        layout.addWidget(availability_container)  # Room availability grid takes full width
        
        # Legend
        legend_frame = QFrame()
        legend_frame.setObjectName("legendFrame")
        legend_layout = QHBoxLayout(legend_frame)
        
        status_colors = {
            "Vacant": "#27ae60",   # Green
            "Reserved": "#8e44ad",    # Purple
            "Occupied": "#c0392b",    # Red
            "Not Available": "#95a5a6", # Gray
            "Needs Cleaning": "#f1c40f" # Yellow
        }
        
        for status, color in status_colors.items():
            legend_item = QWidget()
            legend_item_layout = QHBoxLayout(legend_item)
            legend_item_layout.setSpacing(5)
            
            color_box = QLabel()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            
            status_label = QLabel(status)
            status_label.setStyleSheet("color: #2c3e50;")
            
            legend_item_layout.addWidget(color_box)
            legend_item_layout.addWidget(status_label)
            legend_layout.addWidget(legend_item)
        
        legend_layout.addStretch()
        layout.addWidget(legend_frame)
        
        # Initial update
        self.update_calendar_view()
        self.update_calendar_highlights()
        self.update_availability_grid()

    def on_availability_cell_clicked(self, row, column):
        """Handle clicks on the availability grid cells"""
        room_item = self.availability_table.verticalHeaderItem(row)
        date_item = self.availability_table.horizontalHeaderItem(column)
        
        if not room_item or not date_item:
            return
            
        room_number = room_item.text().split()[1]  # Extract room number from "Room XXX"
        date = QDate(self.calendar.yearShown(), self.calendar.monthShown(), int(date_item.text()))
        
        # Get all reservations
        reservations = get_reservations()
        
        # Find reservations for this room and date
        room_reservations = [
            r for r in reservations 
            if r['room_id'] == room_number and 
            datetime.strptime(r['arrival_date'], '%Y-%m-%d').date() <= date.toPyDate() <= 
            datetime.strptime(r['departure_date'], '%Y-%m-%d').date()
        ]
        
        if room_reservations:
            # Create and show a dialog with reservation details
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Reservations for Room {room_number} on {date.toString('yyyy-MM-dd')}")
            dialog.setMinimumWidth(400)
            
            layout = QVBoxLayout(dialog)
            
            for reservation in room_reservations:
                reservation_frame = QFrame()
                reservation_frame.setObjectName("reservationFrame")
                reservation_layout = QVBoxLayout(reservation_frame)
                
                # Guest name
                guest_name = f"{reservation['guest_first_name']} {reservation['guest_last_name']}"
                name_label = QLabel(guest_name)
                name_label.setObjectName("guestName")
                reservation_layout.addWidget(name_label)
                
                # Room and status
                room_label = QLabel(f"Room: {reservation['room_type']}")
                status_label = QLabel(f"Status: {reservation['status']}")
                reservation_layout.addWidget(room_label)
                reservation_layout.addWidget(status_label)
                
                # Dates
                dates_label = QLabel(
                    f"Arrival: {reservation['arrival_date']}\n"
                    f"Departure: {reservation['departure_date']}"
                )
                reservation_layout.addWidget(dates_label)
                
                # Action buttons
                buttons_layout = QHBoxLayout()
                edit_btn = QPushButton("Edit")
                edit_btn.clicked.connect(lambda _, r=reservation: self.edit_reservation(r))
                delete_btn = QPushButton("Delete")
                delete_btn.clicked.connect(lambda _, r=reservation: self.delete_reservation(r))
                buttons_layout.addWidget(edit_btn)
                buttons_layout.addWidget(delete_btn)
                reservation_layout.addLayout(buttons_layout)
                
                layout.addWidget(reservation_frame)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.close)
            layout.addWidget(close_btn)
            
            dialog.exec()

    def update_availability_grid(self):
        """Update the room availability grid based on filters"""
        rooms = get_all_rooms()
        reservations = get_reservations()
        
        # Apply filters
        status = self.calendar_status.currentText()
        guest_filter = self.guest_filter.text().lower()
        
        current_date = self.calendar.selectedDate()
        year = current_date.year()
        month = current_date.month()
        days_in_month = QDate(year, month, 1).daysInMonth()
        
        self.availability_table.clear()
        self.availability_table.setRowCount(len(rooms))
        self.availability_table.setColumnCount(days_in_month)
        
        # Set headers
        for day in range(days_in_month):
            self.availability_table.setHorizontalHeaderItem(day, QTableWidgetItem(str(day + 1)))
            # Set column width to 30 pixels
            self.availability_table.setColumnWidth(day, 30)
        for i, room in enumerate(rooms):
            self.availability_table.setVerticalHeaderItem(i, QTableWidgetItem(f"Room {room['number']}"))
        
        # Convert rooms list to a dictionary keyed by room_id
        rooms_dict = {str(room['id']): room for room in rooms}
        
        # Fill grid
        for i, room in enumerate(rooms):
            for day in range(days_in_month):
                date = QDate(year, month, day + 1).toString('yyyy-MM-dd')
                
                # Find reservation for this room and date
                room_reservation = next(
                    (r for r in reservations 
                    if str(r['room_id']) == str(room['id']) and 
                    r['arrival_date'] == date),
                    None
                )
                
                if room_reservation:
                    # Apply status filter
                    if status != "All Statuses" and room_reservation['status'] != status:
                        continue
                        
                    # Apply guest filter
                    guest_name = f"{room_reservation['guest_first_name']} {room_reservation['guest_last_name']}".lower()
                    if guest_filter and guest_filter not in guest_name:
                        continue
                        
                    color = self._get_status_color(room_reservation['status'])
                    cell = QTableWidgetItem()
                    cell.setBackground(QColor(color))
                    initials = f"{room_reservation['guest_first_name'][0]}{room_reservation['guest_last_name'][0]}"
                    cell.setText(initials.upper())
                    cell.setForeground(QColor("white"))
                    cell.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    
                    # Tooltip with reservation details
                    cell.setToolTip(
                        f"Reservation: {room_reservation['reservation_id']}\n"
                        f"Guest: {room_reservation['guest_first_name']} {room_reservation['guest_last_name']}\n"
                        f"Status: {room_reservation['status']}\n"
                        f"Room: {rooms_dict.get(str(room_reservation.get('room_id')), {}).get('type', '')}"
                    )
                    self.availability_table.setItem(i, day, cell)
                else:
                    # Available room
                    cell = QTableWidgetItem()
                    cell.setBackground(QColor("#ecf0f1"))  # Light gray
                    self.availability_table.setItem(i, day, cell)

    def update_calendar_view(self):
        """Update calendar view based on selected filters"""
        status = self.calendar_status.currentText()
        guest_filter = self.guest_filter.text().lower()
        
        # Update guest completer when filters change
        self.update_guest_completer()
        
        # Update calendar highlights
        self.update_calendar_highlights()
        
        # Update availability grid
        self.update_availability_grid()

    def update_calendar_highlights(self):
        """Highlight calendar dates with reservations based on filters"""
        reservations = get_reservations()
        
        # Apply filters
        status = self.calendar_status.currentText()
        guest_filter = self.guest_filter.text().lower()
        
        filtered_reservations = []
        for reservation in reservations:
            # Filter by status
            if status != "All Statuses" and reservation['status'] != status:
                continue
                
            # Filter by guest name
            guest_name = f"{reservation['guest_first_name']} {reservation['guest_last_name']}".lower()
            if guest_filter and guest_filter not in guest_name:
                continue
                
            filtered_reservations.append(reservation)
        
        # Create text formats
        status_formats = {
            "Confirmed": QTextCharFormat(),
            "Pending": QTextCharFormat(),
            "Cancelled": QTextCharFormat(),
            "Checked-in": QTextCharFormat()
        }
        status_formats["Confirmed"].setBackground(QColor("#27ae60"))
        status_formats["Confirmed"].setForeground(QColor("white"))
        status_formats["Pending"].setBackground(QColor("#f1c40f"))
        status_formats["Pending"].setForeground(QColor("white"))
        status_formats["Cancelled"].setBackground(QColor("#e74c3c"))
        status_formats["Cancelled"].setForeground(QColor("white"))
        status_formats["Checked-in"].setBackground(QColor("#3498db"))
        status_formats["Checked-in"].setForeground(QColor("white"))
        
        # Clear existing formats
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())
        
        # Make current date bold
        current_date = QDate.currentDate()
        current_format = QTextCharFormat()
        current_format.setFontWeight(QFont.Weight.Bold)
        self.calendar.setDateTextFormat(current_date, current_format)
        
        # Apply formats to filtered reservation dates
        for reservation in filtered_reservations:
            try:
                date = QDate.fromString(reservation['arrival_date'], 'yyyy-MM-dd')
                if date.isValid():
                    status = reservation['status']
                    self.calendar.setDateTextFormat(date, status_formats.get(status, QTextCharFormat()))
            except Exception as e:
                print(f"Error processing reservation {reservation['reservation_id']}: {e}")

    def show_reservation_details(self, date):
        """Show reservations for the selected date"""
        selected_date = date.toString('yyyy-MM-dd')
        reservations = [
            r for r in get_reservations() 
            if r['arrival_date'] == selected_date
        ]
        
        if not reservations:
            QMessageBox.information(self, "No Reservations", 
                                f"No reservations found for {selected_date}")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Reservations for {selected_date}")
        layout = QVBoxLayout(dialog)
        
        for res in reservations:
            frame = QFrame()
            frame_layout = QVBoxLayout(frame)
            
            name = QLabel(f"{res['guest_first_name']} {res['guest_last_name']}")
            room = QLabel(f"Room: {res['room_type']} (ID: {res['room_id']})")
            status = QLabel(f"Status: {res['status']}")
            
            frame_layout.addWidget(name)
            frame_layout.addWidget(room)
            frame_layout.addWidget(status)
            layout.addWidget(frame)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec()

    def show_agenda_view(self):
        """Show agenda view of reservations"""
        # Get all reservations
        reservations = get_reservations()
        
        # Sort reservations by arrival date
        reservations.sort(key=lambda x: datetime.strptime(x['arrival_date'], '%Y-%m-%d'))
        
        # Create a new widget for agenda view
        agenda_widget = QWidget()
        layout = QVBoxLayout(agenda_widget)
        
        # Add each reservation as a card
        for reservation in reservations:
            card = QFrame()
            card.setObjectName("agendaCard")
            card_layout = QVBoxLayout(card)
            
            # Guest name and room
            header = QLabel(f"{reservation['guest_first_name']} {reservation['guest_last_name']} - {reservation['room_type']}")
            header.setObjectName("agendaHeader")
            card_layout.addWidget(header)
            
            # Dates
            dates = QLabel(
                f"Arrival: {reservation['arrival_date']}"
            )
            card_layout.addWidget(dates)
            
            # Status
            status = QLabel(f"Status: {reservation['status']}")
            status.setStyleSheet(f"color: {self._get_status_color(reservation['status'])}")
            card_layout.addWidget(status)
            
            layout.addWidget(card)
        
        # Replace the calendar widget with the agenda view
        self.calendar.setParent(None)
        self.calendar_tab.layout().insertWidget(1, agenda_widget)
        self.current_agenda_widget = agenda_widget

    def show_week_view(self):
        """Show week view of the calendar"""
        # Get the current date
        current_date = self.calendar.selectedDate()
        
        # Calculate the start of the week (Monday)
        start_of_week = current_date.addDays(-(current_date.dayOfWeek() - 1))
        
        # Set the calendar to show the week
        self.calendar.setSelectedDate(start_of_week)
        
        # Update the calendar view
        self.update_calendar_highlights()

    def show_month_view(self):
        """Show month view of the calendar"""
        # Get the current date
        current_date = self.calendar.selectedDate()
        
        # Set the calendar to show the month
        self.calendar.setSelectedDate(current_date)
        
        # Update the calendar view
        self.update_calendar_highlights()

    def _get_status_color(self, status):
        """Get the color for a reservation status"""
        return {
            "Vacant": "#27ae60",      # Green
            "Reserved": "#8e44ad",
            "Occupied": "#c0392b",
            "Not Available": "#95a5a6",
            "Needs Cleaning": "#f1c40f"
        }.get(status, "#bdc3c7")

    def setup_new_reservation_tab(self):
        layout = QVBoxLayout(self.new_reservation_tab)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(0)

        # Progress indicator
        progress_frame = QFrame()
        progress_frame.setObjectName("progressFrame")
        progress_layout = QHBoxLayout(progress_frame)
        steps = ["Guest Details", "Stay Details", "Room Selection", "Payment", "Confirmation"]
        self.progress_labels = []
        for i, step in enumerate(steps):
            step_widget = QWidget()
            step_layout = QVBoxLayout(step_widget)
            number_label = QLabel(str(i + 1))
            number_label.setObjectName("stepNumber")
            number_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            name_label = QLabel(step)
            name_label.setObjectName("stepName")
            name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            step_layout.addWidget(number_label)
            step_layout.addWidget(name_label)
            progress_layout.addWidget(step_widget)
            self.progress_labels.append((number_label, name_label))
            if i < len(steps) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setObjectName("progressLine")
                progress_layout.addWidget(line)
        layout.addWidget(progress_frame)

        # Wizard steps
        self.wizard = QStackedWidget()
        layout.addWidget(self.wizard)

        # Step 1: Guest Details
        step1 = QWidget()
        s1_layout = QVBoxLayout(step1)
        s1_layout.setContentsMargins(40, 20, 40, 20)
        search_label = QLabel("Select Guest")
        search_label.setObjectName("sectionTitle")
        s1_layout.addWidget(search_label)
        
        # Create a container for the search and dropdown
        search_container = QWidget()
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(0, 0, 0, 0)
        search_container_layout.setSpacing(10)  # Add some spacing between the widgets
        
        # Guest select combo
        self.guest_select_combo = QComboBox()
        self.guest_select_combo.setObjectName("guestDropdown")
        self.guest_select_combo.setMinimumWidth(200)
        self.populate_guest_combo()  # Populate the dropdown
        self.guest_select_combo.currentIndexChanged.connect(self.on_guest_selected)
        self.guest_select_combo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        search_container_layout.addWidget(self.guest_select_combo, 1)  # Stretch factor of 1
        
        # Search input
        self.guest_search = QLineEdit()
        self.guest_search.setPlaceholderText("Search guest...")
        self.guest_search.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.guest_search.textChanged.connect(self.filter_guest_dropdown)  # Connect search to filter
        search_container_layout.addWidget(self.guest_search, 1)  # Stretch factor of 1
        
        s1_layout.addWidget(search_container)
        
        # Guest details form
        self.guest_first_name = QLineEdit()
        self.guest_last_name = QLineEdit()
        self.guest_email = QLineEdit()
        self.guest_phone = QLineEdit()
        s1_layout.addWidget(QLabel("First Name:"))
        s1_layout.addWidget(self.guest_first_name)
        s1_layout.addWidget(QLabel("Last Name:"))
        s1_layout.addWidget(self.guest_last_name)
        s1_layout.addWidget(QLabel("Email:"))
        s1_layout.addWidget(self.guest_email)
        s1_layout.addWidget(QLabel("Phone:"))
        s1_layout.addWidget(self.guest_phone)
        self.wizard.addWidget(step1)

        # Step 2: Stay Details
        step2 = QWidget()
        s2_layout = QVBoxLayout(step2)
        s2_layout.setContentsMargins(40, 20, 40, 20)

        # Date selection with calendar widget directly shown
        date_frame = QFrame()
        date_frame.setObjectName("dateFrame")
        date_layout = QHBoxLayout(date_frame)
        date_layout.setSpacing(40)

        # Arrival date with calendar
        arrival_widget = QWidget()
        arrival_layout = QVBoxLayout(arrival_widget)
        arrival_label = QLabel("Arrival Date")
        arrival_label.setObjectName("sectionTitle")
        arrival_layout.addWidget(arrival_label)

        self.arrival_date = QCalendarWidget()
        self.arrival_date.setMinimumDate(QDate.currentDate())
        self.arrival_date.setMinimumWidth(350)
        self.arrival_date.setMinimumHeight(250)
        self.arrival_date.clicked.connect(self.update_room_selection)
        arrival_layout.addWidget(self.arrival_date)

        date_layout.addWidget(arrival_widget, 1)
        s2_layout.addWidget(date_frame)

        # Number of guests
        guests_frame = QFrame()
        guests_frame.setObjectName("guestsFrame")
        guests_layout = QHBoxLayout(guests_frame)

        guests_label = QLabel("Number of Guests")
        guests_label.setObjectName("sectionTitle")
        guests_layout.addWidget(guests_label)

        self.num_guests = QSpinBox()
        self.num_guests.setMinimum(1)
        self.num_guests.setMaximum(10)
        self.num_guests.setValue(1)
        self.num_guests.setButtonSymbols(QSpinBox.ButtonSymbols.UpDownArrows)
        self.num_guests.setMinimumWidth(120)
        guests_layout.addWidget(self.num_guests)
        guests_layout.addStretch()

        s2_layout.addWidget(guests_frame)

        # Special requests
        self.special_requests = QTextEdit()
        self.special_requests.setPlaceholderText("Enter any special requests...")
        self.special_requests.setMaximumHeight(100)
        s2_layout.addWidget(QLabel("Special Requests:"))
        s2_layout.addWidget(self.special_requests)

        self.wizard.addWidget(step2)

        # Step 3: Room Selection
        step3 = QWidget()
        s3_layout = QVBoxLayout(step3)
        s3_layout.setContentsMargins(40, 20, 40, 20)
        rooms_label = QLabel("Select Room")
        rooms_label.setObjectName("sectionTitle")
        s3_layout.addWidget(rooms_label)
        self.room_grid_widget = QWidget()
        self.room_grid_layout = QGridLayout(self.room_grid_widget)
        self.room_grid_layout.setSpacing(10)
        s3_layout.addWidget(self.room_grid_widget)
        # Legend
        legend_frame = QFrame()
        legend_frame.setObjectName("legendFrame")
        legend_layout = QHBoxLayout(legend_frame)
        status_colors = {
            "Vacant": "#27ae60",   # Green
            "Reserved": "#8e44ad",    # Purple
            "Occupied": "#c0392b",    # Red
            "Not Available": "#95a5a6", # Gray
            "Needs Cleaning": "#f1c40f" # Yellow
        }
        for status, color in status_colors.items():
            legend_item = QWidget()
            legend_item_layout = QHBoxLayout(legend_item)
            legend_item_layout.setSpacing(5)
            color_box = QLabel()
            color_box.setFixedSize(20, 20)
            color_box.setStyleSheet(f"background-color: {color}; border-radius: 4px;")
            status_label = QLabel(status)
            status_label.setStyleSheet("color: #2c3e50;")
            legend_item_layout.addWidget(color_box)
            legend_item_layout.addWidget(status_label)
            legend_layout.addWidget(legend_item)
        s3_layout.addWidget(legend_frame)
        self.wizard.addWidget(step3)

        # Step 4: Payment
        step4 = QWidget()
        s4_layout = QVBoxLayout(step4)
        s4_layout.setContentsMargins(40, 20, 40, 20)
        self.payment_method = QComboBox()
        self.payment_method.addItems(["None", "Credit Card", "Debit Card", "Cash", "Bank Transfer"])
        self.deposit_amount = QLineEdit()
        self.deposit_amount.setPlaceholderText("0.00")
        s4_layout.addWidget(QLabel("Payment Method:"))
        s4_layout.addWidget(self.payment_method)
        s4_layout.addWidget(QLabel("Deposit Amount:"))
        s4_layout.addWidget(self.deposit_amount)
        # Amount Due (calculated)
        self.amount_due = QLineEdit()
        self.amount_due.setReadOnly(True)
        self.amount_due.setPlaceholderText("0.00")
        s4_layout.addWidget(QLabel("Amount Due:"))
        s4_layout.addWidget(self.amount_due)
        self.wizard.addWidget(step4)

        # Step 5: Confirmation
        step5 = QWidget()
        s5_layout = QVBoxLayout(step5)
        s5_layout.setContentsMargins(40, 20, 40, 20)
        self.confirmation_label = QLabel()
        self.confirmation_label.setWordWrap(True)
        s5_layout.addWidget(self.confirmation_label)
        self.wizard.addWidget(step5)

        # Navigation buttons
        nav_frame = QFrame()
        nav_frame.setObjectName("navFrame")
        nav_layout = QHBoxLayout(nav_frame)
        self.back_btn = QPushButton("Back")
        self.next_btn = QPushButton("Next")
        self.cancel_btn = QPushButton("Cancel")
        self.finish_btn = QPushButton("Finish")
        self.back_btn.setObjectName("navButton")
        self.next_btn.setObjectName("navButton")
        self.cancel_btn.setObjectName("navButton")
        self.finish_btn.setObjectName("navButton")
        nav_layout.addWidget(self.cancel_btn)
        nav_layout.addStretch()
        nav_layout.addWidget(self.back_btn)
        nav_layout.addWidget(self.next_btn)
        nav_layout.addWidget(self.finish_btn)
        layout.addWidget(nav_frame)

        # Connect signals
        self.back_btn.clicked.connect(self.prev_step)
        self.next_btn.clicked.connect(self.next_step)
        self.cancel_btn.clicked.connect(self.cancel_wizard)
        self.finish_btn.clicked.connect(self.finish_wizard)
        self.arrival_date.clicked.connect(self.update_room_selection)
        # Update amount due when relevant fields change
        self.arrival_date.clicked.connect(self.update_amount_due)
        # Also update when room is selected
        self.selected_room_id = None
        self.update_wizard_ui()
        self.update_room_selection()

    def update_room_selection(self):
        """Update room selection when rooms change"""
        if hasattr(self, 'room_grid_widget'):
            self.load_room_grid()

    def load_room_grid(self):
        # Remove old buttons
        for i in reversed(range(self.room_grid_layout.count())):
            widget = self.room_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        rooms = get_all_rooms()  # Fetch the latest room list from the database
        cols = 5
        for idx, room in enumerate(rooms):
            btn = QPushButton(f"{room['number']}\n{room.get('type','')}\n{room.get('status','')}")
            btn.setCheckable(True)
            btn.setMinimumSize(100, 60)
            color = self._room_color(room.get('status',''))
            highlight = hasattr(self, 'selected_room_id') and self.selected_room_id == room['id']
            style = f"background:{color};color:white;font-weight:bold;border-radius:8px;"
            if highlight:
                style += "border: 3px solid #f1c40f;"
                btn.setChecked(True)
            else:
                style += "border: none;"
                btn.setChecked(False)
            btn.setStyleSheet(style)
            if room.get('status') != "Vacant":
                btn.setEnabled(False)
            btn.clicked.connect(lambda _, rid=room['id']: self.select_room(rid))
            self.room_grid_layout.addWidget(btn, idx // cols, idx % cols)

    def select_room(self, room_id):
        self.selected_room_id = room_id
        self.load_room_grid()
        self.update_amount_due()

    def next_step(self):
        step = self.wizard.currentIndex()
        if step == 0:
            if not self.guest_first_name.text().strip() or not self.guest_last_name.text().strip():
                QMessageBox.warning(self, "Guest Required", "Please enter guest's first and last name before proceeding.")
                return
        if step == 2:
            if not hasattr(self, 'selected_room_id') or not self.selected_room_id:
                QMessageBox.warning(self, "Room Required", "Please select a room before proceeding.")
                return
        if step < self.wizard.count() - 1:
            self.wizard.setCurrentIndex(step + 1)
            if self.wizard.currentIndex() == 1:
                # Show calendar popup immediately when entering Stay Details step
                self.arrival_date.setFocus() # Set focus to the QDateEdit
            if self.wizard.currentIndex() == 4:
                self.show_confirmation_details()
            self.update_wizard_ui()

    def prev_step(self):
        if self.wizard.currentIndex() > 0:
            current_step = self.wizard.currentIndex()
            self.wizard.setCurrentIndex(current_step - 1)
            # If going back to room selection step (step 2), reload the room grid with current selection
            if current_step - 1 == 2:
                self.load_room_grid()
            self.update_wizard_ui()

    def cancel_wizard(self):
        self.wizard.setCurrentIndex(0)
        self.update_wizard_ui()

    def finish_wizard(self):
        # Mark room as reserved and save reservation
        from app.core.db import update_room, add_reservation, get_all_rooms
        room_id = getattr(self, 'selected_room_id', None)
        rooms = get_all_rooms()
        room_info = next((r for r in rooms if r['id'] == room_id), None)
        if room_info:
            room_info = dict(room_info)
            room_info['status'] = 'Reserved'
            update_room(room_id, room_info)
            # Emit room status changed signal
            self.room_status_changed.emit()
        
        # Generate receipt
        self.generate_receipt()
        
        # Handle empty deposit amount
        deposit_amount = self.deposit_amount.text().strip()
        if not deposit_amount:
            deposit_amount = "0.0"
        
        # Ensure we have valid room info
        if not room_info:
            QMessageBox.critical(self, "Error", "No room selected. Please select a room before proceeding.")
            return
            
        reservation = {
            'reservation_id': self.reservation_id,
            'guest_first_name': self.guest_first_name.text(),
            'guest_last_name': self.guest_last_name.text(),
            'guest_email': self.guest_email.text(),
            'guest_phone': self.guest_phone.text(),
            'arrival_date': self.arrival_date.selectedDate().toString('yyyy-MM-dd'),
            'num_guests': str(self.num_guests.value()),
            'room_id': room_id,
            'room_type': room_info.get('type', ''),  # Ensure room_type is set
            'special_requests': self.special_requests.toPlainText(),
            'payment_method': self.payment_method.currentText(),
            'deposit_amount': deposit_amount,
            'amount_due': self.amount_due.text(),
            'status': 'Confirmed',
            'created_on': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
        
        try:
            add_reservation(reservation)
            
            # Reset wizard and return to step 1
            self.reset_wizard_fields()
            self.wizard.setCurrentIndex(0)
            self.update_wizard_ui()
            
            # Refresh reservations list
            self.load_reservations()
            
            # Update calendar view
            self.update_calendar_view()
            
            # Show success message
            QMessageBox.information(self, "Success", "Reservation has been created successfully!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create reservation: {str(e)}")

    def reset_wizard_fields(self):
        """Reset all fields in the wizard for a new reservation"""
        self.guest_select_combo.setCurrentIndex(0)
        self.guest_search.clear()
        self.guest_first_name.clear()
        self.guest_last_name.clear()
        self.guest_email.clear()
        self.guest_phone.clear()
        self.arrival_date.setSelectedDate(QDate.currentDate())
        self.num_guests.setValue(1)
        self.special_requests.clear()
        self.payment_method.setCurrentIndex(0)
        self.deposit_amount.clear()
        self.amount_due.clear()
        self.selected_room_id = None
        self.load_room_grid()
        if hasattr(self, 'print_receipt_btn'):
            self.print_receipt_btn.setVisible(False)
        self.reservation_id = str(uuid.uuid4())[:8]  # Generate new reservation ID

    def generate_receipt(self):
        """Generate PDF receipt for the reservation"""
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add header
        pdf.cell(200, 10, txt="Hotel Reservation Receipt", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Reservation #: {self.reservation_id}", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        
        # Add guest details
        guest_name = f"{self.guest_first_name.text()} {self.guest_last_name.text()}"
        pdf.cell(200, 10, txt=f"Guest: {guest_name}", ln=True)
        pdf.cell(200, 10, txt=f"Email: {self.guest_email.text()}", ln=True)
        pdf.cell(200, 10, txt=f"Phone: {self.guest_phone.text()}", ln=True)
        
        # Add stay details
        rooms = get_all_rooms()
        room_info = next((r for r in rooms if r['id'] == self.selected_room_id), None)
        room_text = f"{room_info['type']} #{room_info['number']}" if room_info else "No room selected"
        
        pdf.cell(200, 10, txt=f"Room: {room_text}", ln=True)
        pdf.cell(200, 10, txt=f"Arrival: {self.arrival_date.selectedDate().toString('yyyy-MM-dd')}", ln=True)
        pdf.cell(200, 10, txt=f"Number of Guests: {str(self.num_guests.value())}", ln=True)
        
        # Add payment details
        pdf.cell(200, 10, txt=f"Payment Method: {self.payment_method.currentText()}", ln=True)
        pdf.cell(200, 10, txt=f"Deposit Amount: {self.deposit_amount.text()}", ln=True)
        pdf.cell(200, 10, txt=f"Amount Due: {self.amount_due.text()}", ln=True)
        
        # Save the PDF
        pdf.output("reservation_receipt.pdf")

    def print_receipt(self):
        """Open the generated PDF receipt"""
        os.startfile("reservation_receipt.pdf")

    def show_confirmation_details(self):
        guest = f"{self.guest_first_name.text()} {self.guest_last_name.text()}"
        arrival = self.arrival_date.selectedDate().toString('yyyy-MM-dd')
        
        # Get room info from database
        rooms = get_all_rooms()
        room_info = next((r for r in rooms if r['id'] == self.selected_room_id), None)
        room_text = f"{room_info['type']} #{room_info['number']}" if room_info else "No room selected"
        
        payment = self.payment_method.currentText()
        deposit = self.deposit_amount.text()
        amount_due = self.amount_due.text()
        
        self.confirmation_label.setText(f"""
        <b>Reservation Confirmed!</b><br><br>
        <b>Reservation #:</b> {self.reservation_id}<br>
        <b>Date:</b> {datetime.now().strftime('%Y-%m-%d %H:%M')}<br><br>
        <b>Guest:</b> {guest}<br>
        <b>Arrival:</b> {arrival}<br>
        <b>Room:</b> {room_text}<br>
        <b>Payment Method:</b> {payment}<br>
        <b>Deposit:</b> {deposit}<br>
        <b>Amount Due:</b> {amount_due}<br>
        <b>Number of Guests:</b> {str(self.num_guests.value())}
        """)
        
        # Add Print Receipt button if not already added
        if not hasattr(self, 'print_receipt_btn'):
            self.print_receipt_btn = QPushButton("Print Receipt")
            self.print_receipt_btn.setObjectName("actionButton")
            self.print_receipt_btn.clicked.connect(self.print_receipt)
            self.confirmation_label.parentWidget().layout().addWidget(self.print_receipt_btn)
        self.print_receipt_btn.setVisible(True)

    def update_amount_due(self):
        """Calculate amount due based on selected room's night rate"""
        if not hasattr(self, 'selected_room_id') or not self.selected_room_id:
            self.amount_due.setText("0.00")
            return
        rooms = get_all_rooms()
        room_info = next((r for r in rooms if r['id'] == self.selected_room_id), None)
        if not room_info or not room_info.get('type'):
            self.amount_due.setText("0.00")
            return
        rates = get_room_rates()
        room_rate = next((r['night_rate'] for r in rates if r['room_type'] == room_info['type']), None)
        if not room_rate:
            self.amount_due.setText("0.00")
            return
        self.amount_due.setText(f"{room_rate:.2f}")

    def update_wizard_ui(self):
        """Update wizard UI based on current step"""
        current_step = self.wizard.currentIndex()
        
        # Update progress indicators
        for i, (number_label, name_label) in enumerate(self.progress_labels):
            if i < current_step:  # Completed steps
                number_label.setProperty("active", "true")
                number_label.setProperty("completed", "true")
                name_label.setProperty("active", "true")
                name_label.setProperty("completed", "true")
            elif i == current_step:  # Current step
                number_label.setProperty("active", "true")
                number_label.setProperty("completed", "false")
                name_label.setProperty("active", "true")
                name_label.setProperty("completed", "false")
            else:  # Future steps
                number_label.setProperty("active", "false")
                number_label.setProperty("completed", "false")
                name_label.setProperty("active", "false")
                name_label.setProperty("completed", "false")
            
            # Force style update
            number_label.style().unpolish(number_label)
            number_label.style().polish(number_label)
            name_label.style().unpolish(name_label)
            name_label.style().polish(name_label)
        
        # Update navigation buttons
        self.back_btn.setVisible(current_step > 0)
        self.next_btn.setVisible(current_step < self.wizard.count() - 1)
        self.finish_btn.setVisible(current_step == self.wizard.count() - 1)

    def populate_guest_combo(self):
        """Populate the guest dropdown with all guests"""
        if not hasattr(self, 'guest_select_combo'):
            return
            
        self.guest_select_combo.clear()
        guests = get_all_guests()
        self.guest_select_combo.addItem("-- Select Guest --", None)
        for g in guests:
            name = f"{g['first_name']} {g['last_name']}"
            self.guest_select_combo.addItem(name, g)
            
        # If there's search text, reapply the filter
        if hasattr(self, 'guest_search') and self.guest_search.text():
            self.filter_guest_dropdown()

    def filter_guest_dropdown(self):
        """Filter the guest dropdown based on search text"""
        search_text = self.guest_search.text().lower()
        self.guest_select_combo.clear()
        self.guest_select_combo.addItem("-- Select Guest --", None)
        
        guests = get_all_guests()
        for g in guests:
            name = f"{g['first_name']} {g['last_name']}"
            if search_text in name.lower():
                self.guest_select_combo.addItem(name, g)

    def on_guest_selected(self, index):
        """Handle guest selection from dropdown"""
        if index >= 0:
            guest = self.guest_select_combo.currentData()
            if guest:
                self.guest_first_name.setText(guest['first_name'])
                self.guest_last_name.setText(guest['last_name'])
                self.guest_email.setText(guest.get('email') or "")
                phone = f"{guest.get('phone_code') or ''} {guest.get('phone_number') or ''}".strip()
                self.guest_phone.setText(phone)

    def _room_color(self, status):
        return {
            "Vacant": "#27ae60",      # Green
            "Reserved": "#8e44ad",
            "Occupied": "#c0392b",
            "Not Available": "#95a5a6",
            "Needs Cleaning": "#f1c40f"
        }.get(status, "#bdc3c7")

    def setup_cancellations_tab(self):
        layout = QVBoxLayout(self.cancel_tab)
        
        # Search for reservation to cancel
        search_layout = QHBoxLayout()
        self.cancel_search = QLineEdit()
        self.cancel_search.setPlaceholderText("Enter reservation number or guest name")
        search_layout.addWidget(self.cancel_search)
        
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self.search_reservations_to_cancel)
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Cancellations table
        self.cancellations_table = QTableWidget()
        self.cancellations_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.cancellations_table.setAlternatingRowColors(True)
        self.cancellations_table.setColumnCount(7)
        self.cancellations_table.verticalHeader().setDefaultSectionSize(50)  # Make rows thick
        self.cancellations_table.setHorizontalHeaderLabels([
            "Reservation #", "Guest Name", "Arrival", "Departure", "Room Type", "Status", "Actions"
        ])
        self.cancellations_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.cancellations_table)
        
        # Cancellation details form
        details_layout = QFormLayout()
        self.cancel_reason = QComboBox()
        self.cancel_reason.addItems([
            "Guest Request", "No-Show", "Payment Issue", "Overbooking", "Maintenance", "Other"
        ])
        details_layout.addRow("Cancellation Reason:", self.cancel_reason)
        
        self.refund_amount = QLineEdit()
        self.refund_amount.setPlaceholderText("0.00")
        details_layout.addRow("Refund Amount:", self.refund_amount)
        
        self.cancel_notes = QLineEdit()
        details_layout.addRow("Notes:", self.cancel_notes)
        
        layout.addLayout(details_layout)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        self.process_cancellation_button = QPushButton("Process Cancellation")
        self.process_cancellation_button.clicked.connect(self.process_cancellation)
        buttons_layout.addWidget(self.process_cancellation_button)
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout)
        
        # Load initial data
        self.load_cancellations_table()

    def search_reservations_to_cancel(self):
        """Search for reservations to cancel"""
        search_text = self.cancel_search.text().lower()
        if not search_text:
            self.load_cancellations_table()
            return
            
        # Get all reservations
        reservations = get_reservations()
        
        # Filter reservations
        filtered_reservations = []
        for reservation in reservations:
            if (search_text in reservation['reservation_id'].lower() or
                search_text in f"{reservation['guest_first_name']} {reservation['guest_last_name']}".lower()):
                filtered_reservations.append(reservation)
        
        # Update table
        self.update_cancellations_table(filtered_reservations)

    def load_cancellations_table(self):
        """Load all active reservations into the cancellations table"""
        reservations = get_reservations()
        # Filter out already cancelled reservations
        active_reservations = [r for r in reservations if r['status'] != 'Cancelled']
        self.update_cancellations_table(active_reservations)

    def update_cancellations_table(self, reservations):
        """Update the cancellations table with the given reservations"""
        self.cancellations_table.setRowCount(0)
        
        for row, reservation in enumerate(reservations):
            self.cancellations_table.insertRow(row)
            
            # Reservation ID
            self.cancellations_table.setItem(row, 0, QTableWidgetItem(reservation['reservation_id']))
            
            # Guest Name
            guest_name = f"{reservation['guest_first_name']} {reservation['guest_last_name']}"
            self.cancellations_table.setItem(row, 1, QTableWidgetItem(guest_name))
            
            # Arrival Date
            self.cancellations_table.setItem(row, 2, QTableWidgetItem(reservation['arrival_date']))
            
            # Departure Date (if available)
            departure_date = reservation.get('departure_date', 'N/A')
            self.cancellations_table.setItem(row, 3, QTableWidgetItem(departure_date))
            
            # Room Type
            self.cancellations_table.setItem(row, 4, QTableWidgetItem(reservation.get('room_type', 'N/A')))
            
            # Status
            self.cancellations_table.setItem(row, 5, QTableWidgetItem(reservation['status']))
            
            # Actions
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(5, 0, 5, 0)
            actions_layout.setSpacing(10)
            
            cancel_btn = QPushButton("Cancel")
            cancel_btn.setObjectName("tableActionButton")
            cancel_btn.setProperty("action", "cancel")
            cancel_btn.setFixedWidth(80)
            cancel_btn.clicked.connect(lambda _, r=reservation: self.select_reservation_for_cancellation(r))
            
            actions_layout.addWidget(cancel_btn)
            actions_layout.addStretch()
            
            self.cancellations_table.setCellWidget(row, 6, actions_widget)

    def select_reservation_for_cancellation(self, reservation):
        """Select a reservation for cancellation"""
        # Store the selected reservation
        self.selected_reservation = reservation
        
        # Pre-fill refund amount with deposit amount
        self.refund_amount.setText(str(reservation.get('deposit_amount', '0.00')))
        
        # Enable process button
        self.process_cancellation_button.setEnabled(True)
        
        # Show confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Cancellation",
            f"Are you sure you want to cancel reservation #{reservation['reservation_id']}?\n"
            f"Guest: {reservation['guest_first_name']} {reservation['guest_last_name']}\n"
            f"Room: {reservation.get('room_type', 'N/A')}\n"
            f"Arrival: {reservation['arrival_date']}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.No:
            self.selected_reservation = None
            self.process_cancellation_button.setEnabled(False)
            self.refund_amount.clear()

    def process_cancellation(self):
        """Process the cancellation of the selected reservation"""
        if not hasattr(self, 'selected_reservation'):
            QMessageBox.warning(self, "Error", "No reservation selected for cancellation.")
            return
            
        # Validate refund amount
        try:
            refund_amount = float(self.refund_amount.text())
        except ValueError:
            QMessageBox.warning(self, "Error", "Please enter a valid refund amount.")
            return
            
        # Prepare cancellation data
        cancellation_data = {
            'reason': self.cancel_reason.currentText(),
            'refund_amount': refund_amount,
            'notes': self.cancel_notes.text(),
            'cancelled_by': 'Admin'  # You might want to get this from the logged-in user
        }
        
        # Process cancellation
        from app.core.db import cancel_reservation
        if cancel_reservation(self.selected_reservation['reservation_id'], cancellation_data):
            # Show success message
            QMessageBox.information(
                self,
                "Success",
                f"Reservation #{self.selected_reservation['reservation_id']} has been cancelled successfully."
            )
            
            # Clear form
            self.cancel_reason.setCurrentIndex(0)
            self.refund_amount.clear()
            self.cancel_notes.clear()
            self.selected_reservation = None
            self.process_cancellation_button.setEnabled(False)
            
            # Refresh tables
            self.load_cancellations_table()
            self.load_reservations()
            self.update_calendar_view()
            
            # Emit room status changed signal
            self.room_status_changed.emit()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to cancel reservation. Please try again."
            )

    def clear_calendar_filters(self):
        """Clear all calendar filters"""
        self.calendar_status.setCurrentIndex(0)
        self.guest_filter.clear()
        self.update_calendar_view()

    def update_guest_completer(self):
        """Update the guest completer list based on current filters"""
        reservations = get_reservations()
        
        # Apply status filters to get relevant guest names
        status = self.calendar_status.currentText()
        
        guest_names = set()
        for reservation in reservations:
            # Filter by status
            if status != "All Statuses" and reservation['status'] != status:
                continue
                
            guest_name = f"{reservation['guest_first_name']} {reservation['guest_last_name']}"
            guest_names.add(guest_name)
        
        # Update completer model
        self.guest_completer.setModel(QStringListModel(sorted(guest_names)))
        
        # Show completer if there's text in the filter
        if self.guest_filter.text():
            self.guest_completer.complete()

    def edit_reservation(self, reservation):
        """Edit an existing reservation"""
        # Create and show edit dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Reservation")
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout(dialog)
        
        # Guest details
        guest_frame = QFrame()
        guest_frame.setObjectName("reservationFrame")
        guest_layout = QFormLayout(guest_frame)
        
        first_name = QLineEdit(reservation['guest_first_name'])
        last_name = QLineEdit(reservation['guest_last_name'])
        email = QLineEdit(reservation.get('guest_email', ''))
        phone = QLineEdit(reservation.get('guest_phone', ''))
        
        guest_layout.addRow("First Name:", first_name)
        guest_layout.addRow("Last Name:", last_name)
        guest_layout.addRow("Email:", email)
        guest_layout.addRow("Phone:", phone)
        
        layout.addWidget(guest_frame)
        
        # Stay details
        stay_frame = QFrame()
        stay_frame.setObjectName("reservationFrame")
        stay_layout = QFormLayout(stay_frame)
        
        arrival_date = QDateEdit()
        arrival_date.setCalendarPopup(True)
        arrival_date.setDate(QDate.fromString(reservation['arrival_date'], 'yyyy-MM-dd'))
        
        num_guests = QComboBox()
        num_guests.addItems([str(i) for i in range(1, 7)])
        num_guests.setCurrentText(str(reservation.get('num_guests', '1')))
        
        status = QComboBox()
        status.addItems(["Confirmed", "Pending", "Cancelled", "Checked-in"])
        status.setCurrentText(reservation['status'])
        
        special_requests = QLineEdit(reservation.get('special_requests', ''))
        
        stay_layout.addRow("Arrival Date:", arrival_date)
        stay_layout.addRow("Number of Guests:", num_guests)
        stay_layout.addRow("Status:", status)
        stay_layout.addRow("Special Requests:", special_requests)
        
        layout.addWidget(stay_frame)
        
        # Payment details
        payment_frame = QFrame()
        payment_frame.setObjectName("reservationFrame")
        payment_layout = QFormLayout(payment_frame)
        
        payment_method = QComboBox()
        payment_method.addItems(["None", "Credit Card", "Debit Card", "Cash", "Bank Transfer"])
        payment_method.setCurrentText(reservation.get('payment_method', 'None'))
        
        deposit_amount = QLineEdit(str(reservation.get('deposit_amount', '0.00')))
        amount_due = QLineEdit(str(reservation.get('amount_due', '0.00')))
        
        payment_layout.addRow("Payment Method:", payment_method)
        payment_layout.addRow("Deposit Amount:", deposit_amount)
        payment_layout.addRow("Amount Due:", amount_due)
        
        layout.addWidget(payment_frame)
        
        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update reservation
            updated_reservation = {
                'reservation_id': reservation['reservation_id'],
                'guest_first_name': first_name.text(),
                'guest_last_name': last_name.text(),
                'guest_email': email.text(),
                'guest_phone': phone.text(),
                'arrival_date': arrival_date.date().toString('yyyy-MM-dd'),
                'num_guests': num_guests.currentText(),
                'room_id': reservation['room_id'],
                'room_type': reservation['room_type'],
                'special_requests': special_requests.text(),
                'payment_method': payment_method.currentText(),
                'deposit_amount': deposit_amount.text(),
                'amount_due': amount_due.text(),
                'status': status.currentText(),
                'created_on': reservation['created_on']
            }
            
            # Save to database
            update_reservation(reservation['reservation_id'], updated_reservation)
            
            # Refresh views
            self.load_reservations()
            self.update_calendar_view()
            
            # Show success message
            QMessageBox.information(self, "Success", "Reservation has been updated successfully!")

    def delete_reservation(self, reservation):
        reply = QMessageBox.question(self, "Delete Reservation", f"Are you sure you want to delete reservation #{reservation['reservation_id']}?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            from app.core.db import delete_reservation
            delete_reservation(reservation['reservation_id'])
            self.load_reservations()
            self.update_calendar_view()
            QMessageBox.information(self, "Deleted", "Reservation has been deleted.")
