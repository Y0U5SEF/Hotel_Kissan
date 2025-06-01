from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTabWidget,
    QLineEdit, QFormLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QComboBox, QSpinBox, QFrame,
    QGridLayout, QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QIcon
from app.core.db import (
    get_all_rooms, insert_room, update_room, delete_room,
    get_room_rates, update_room_rate
)

class RoomManagementWidget(QWidget):
    """Widget for managing hotel rooms"""
    
    # Signal for room status changes
    room_status_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Room Management tab
        self.room_management_tab = QWidget()
        self.setup_room_management_tab()
        self.tab_widget.addTab(self.room_management_tab, QIcon(":/icons/rooms.png"), "Room Management")
        
        # Room Rates tab
        self.room_rates_tab = QWidget()
        self.setup_room_rates_tab()
        self.tab_widget.addTab(self.room_rates_tab, QIcon(":/icons/rates.png"), "Room Rates")
        
        layout.addWidget(self.tab_widget)
        
    def setup_room_management_tab(self):
        layout = QVBoxLayout(self.room_management_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Buttons container
        buttons_layout = QHBoxLayout()
        
        # Add Single Room button
        add_btn = QPushButton("Add Single Room")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self.add_room)
        buttons_layout.addWidget(add_btn)
        
        # Add Multiple Rooms button
        add_multiple_btn = QPushButton("Add Multiple Rooms")
        add_multiple_btn.setObjectName("actionButton")
        add_multiple_btn.clicked.connect(self.add_multiple_rooms)
        buttons_layout.addWidget(add_multiple_btn)
        
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        
        # Rooms Table
        self.rooms_table = QTableWidget()
        self.rooms_table.setAlternatingRowColors(True)
        self.rooms_table.setColumnCount(7)
        self.rooms_table.setAlternatingRowColors(True)
        self.rooms_table.setHorizontalHeaderLabels([
            "Room Number", "Type", "Beds", "Floor", "Location", "Status", "Actions"
        ])
        self.rooms_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.rooms_table.setObjectName("dataTable")
        self.rooms_table.verticalHeader().setDefaultSectionSize(50)  # Increase row height
        layout.addWidget(self.rooms_table)
        
        # Load existing rooms
        self.load_rooms()
        
    def setup_room_rates_tab(self):
        layout = QVBoxLayout(self.room_rates_tab)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Room Rates Table
        self.room_rates_table = QTableWidget()
        self.room_rates_table.setAlternatingRowColors(True)
        self.room_rates_table.setColumnCount(3)
        self.room_rates_table.setHorizontalHeaderLabels(["Room Type", "Night Rate", "Actions"])
        self.room_rates_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.room_rates_table.setObjectName("dataTable")
        self.room_rates_table.verticalHeader().setDefaultSectionSize(50)  # Increase row height
        layout.addWidget(self.room_rates_table)
        
        # Add Rate button
        add_btn = QPushButton("Add Room Rate")
        add_btn.setObjectName("actionButton")
        add_btn.clicked.connect(self.add_room_rate)
        layout.addWidget(add_btn)
        
        # Load existing rates
        self.load_room_rates()
        
    def load_rooms(self):
        self.rooms_table.setRowCount(0)
        rooms = get_all_rooms()
        
        for room in rooms:
            row = self.rooms_table.rowCount()
            self.rooms_table.insertRow(row)
            
            self.rooms_table.setItem(row, 0, QTableWidgetItem(room['number']))
            self.rooms_table.setItem(row, 1, QTableWidgetItem(room.get('type', '')))
            self.rooms_table.setItem(row, 2, QTableWidgetItem(str(room.get('beds', ''))))
            self.rooms_table.setItem(row, 3, QTableWidgetItem(room.get('floor', '')))
            self.rooms_table.setItem(row, 4, QTableWidgetItem(room.get('location', '')))
            self.rooms_table.setItem(row, 5, QTableWidgetItem(room.get('status', 'Vacant')))
            
            # Add action buttons
            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(0, 0, 0, 0)
            actions_layout.setSpacing(5)
            
            edit_btn = QPushButton("Edit")
            edit_btn.setObjectName("editButton")
            edit_btn.setFixedWidth(80)
            edit_btn.clicked.connect(lambda _, r=room: self.edit_room(r))
            
            delete_btn = QPushButton("Delete")
            delete_btn.setObjectName("deleteButton")
            delete_btn.setFixedWidth(80)
            delete_btn.clicked.connect(lambda _, r=room: self.delete_room(r))
            
            actions_layout.addWidget(edit_btn)
            actions_layout.addWidget(delete_btn)
            
            self.rooms_table.setCellWidget(row, 6, actions_widget)
            
    def add_room(self):
        dialog = QDialog(self)
        dialog.setMinimumWidth(400)
        dialog.setWindowTitle("Add Room")
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        # Get all existing rooms
        rooms = get_all_rooms()
        
        # Find the last room number for regular rooms and suites
        last_regular_number = 0
        last_suite_number = 0
        
        for room in rooms:
            try:
                if room['type'].lower() == 'suite':
                    # Extract number from "Suite X" format
                    suite_num = int(room['number'].split()[-1])
                    last_suite_number = max(last_suite_number, suite_num)
                else:
                    room_num = int(room['number'])
                    last_regular_number = max(last_regular_number, room_num)
            except (ValueError, IndexError):
                continue
        
        # Next room numbers
        next_regular_number = str(last_regular_number + 1)
        next_suite_number = f"Suite {last_suite_number + 1}"
        
        # Show next room number in a label
        room_number_label = QLabel(f"Room Number: {next_regular_number}")
        room_number_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        form.addRow(room_number_label)
        
        room_type = QComboBox()
        room_type.addItems(["Single", "Double", "Suite", "Deluxe"])
        room_type.setEditable(True)
        
        # Update room number when type changes
        def update_room_number(type_text):
            if type_text.lower() == 'suite':
                room_number_label.setText(f"Room Number: {next_suite_number}")
            else:
                room_number_label.setText(f"Room Number: {next_regular_number}")
        
        room_type.currentTextChanged.connect(update_room_number)
        form.addRow("Room Type:", room_type)
        
        beds = QSpinBox()
        beds.setRange(1, 10)
        form.addRow("Number of Beds:", beds)
        
        floor = QLineEdit()
        form.addRow("Floor:", floor)
        
        location = QLineEdit()
        form.addRow("Location:", location)
        
        status = QComboBox()
        status.addItems(["Vacant", "Occupied", "Dirty", "Clean", "Out of Order"])
        form.addRow("Status:", status)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        ok_button = buttons.button(QDialogButtonBox.StandardButton.Ok)
        ok_button.setObjectName("dialogOkButton")
        cancel_button = buttons.button(QDialogButtonBox.StandardButton.Cancel)
        cancel_button.setObjectName("dialogCancelButton")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Determine room number based on type
            room_number = next_suite_number if room_type.currentText().lower() == 'suite' else next_regular_number
            
            room = {
                'number': room_number,
                'type': room_type.currentText(),
                'beds': beds.value(),
                'floor': floor.text(),
                'location': location.text(),
                'status': status.currentText()
            }
            insert_room(room)
            self.load_rooms()
            # Emit room status changed signal
            self.room_status_changed.emit()
            
    def edit_room(self, room):
        dialog = QDialog(self)
        dialog.setMinimumWidth(400)
        dialog.setWindowTitle("Edit Room")
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        # Show room number in a label instead of QLineEdit
        room_number_label = QLabel(f"Room Number: {room['number']}")
        room_number_label.setStyleSheet("font-weight: bold; color: #2196F3;")
        form.addRow(room_number_label)
        
        room_type = QComboBox()
        room_type.addItems(["Single", "Double", "Suite", "Deluxe"])
        room_type.setEditable(True)
        room_type.setCurrentText(room.get('type', ''))
        form.addRow("Room Type:", room_type)
        
        beds = QSpinBox()
        beds.setRange(1, 10)
        beds.setValue(room.get('beds', 1))
        form.addRow("Number of Beds:", beds)
        
        floor = QLineEdit(room.get('floor', ''))
        form.addRow("Floor:", floor)
        
        location = QLineEdit(room.get('location', ''))
        form.addRow("Location:", location)
        
        status = QComboBox()
        status.addItems(["Vacant", "Occupied", "Dirty", "Clean", "Out of Order"])
        status.setCurrentText(room.get('status', 'Vacant'))
        form.addRow("Status:", status)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get the new room type
            new_type = room_type.currentText()
            old_type = room.get('type', '')
            
            # Handle room number based on type change
            if new_type.lower() == 'suite' and old_type.lower() != 'suite':
                # Converting to suite - get the next suite number
                rooms = get_all_rooms()
                last_suite_number = 0
                for r in rooms:
                    if r['type'].lower() == 'suite':
                        try:
                            suite_num = int(r['number'].split()[-1])
                            last_suite_number = max(last_suite_number, suite_num)
                        except (ValueError, IndexError):
                            continue
                new_number = f"Suite {last_suite_number + 1}"
            elif old_type.lower() == 'suite' and new_type.lower() != 'suite':
                # Converting from suite to regular room - get the next regular number
                rooms = get_all_rooms()
                last_regular_number = 0
                for r in rooms:
                    if r['type'].lower() != 'suite':
                        try:
                            room_num = int(r['number'])
                            last_regular_number = max(last_regular_number, room_num)
                        except ValueError:
                            continue
                new_number = str(last_regular_number + 1)
            else:
                # No type change, keep the same number
                new_number = room['number']
            
            updated_room = {
                'number': new_number,
                'type': new_type,
                'beds': beds.value(),
                'floor': floor.text(),
                'location': location.text(),
                'status': status.currentText()
            }
            update_room(room['id'], updated_room)
            self.load_rooms()
            # Emit room status changed signal
            self.room_status_changed.emit()
            
    def delete_room(self, room):
        reply = QMessageBox.question(
            self, 'Confirm Delete',
            f"Are you sure you want to delete room {room['number']}?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            delete_room(room['id'])
            self.load_rooms()
            
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
        
        room_type = QComboBox()
        room_type.addItems(["Single", "Double", "Suite", "Deluxe"])
        room_type.setEditable(True)
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
            update_room_rate(room_type.currentText(), night_rate.value())
            self.load_room_rates()
            
    def edit_room_rate(self, rate):
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit Room Rate")
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        room_type = QComboBox()
        room_type.addItems(["Single", "Double", "Suite", "Deluxe"])
        room_type.setEditable(True)
        room_type.setCurrentText(rate['room_type'])
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
            update_room_rate(room_type.currentText(), night_rate.value())
            self.load_room_rates()

    def add_multiple_rooms(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Multiple Rooms")
        dialog.setMinimumWidth(500)
        layout = QVBoxLayout(dialog)
        
        form = QFormLayout()
        
        # Room type selection
        room_type = QComboBox()
        room_type.addItems(["Single", "Double", "Suite", "Deluxe"])
        room_type.setEditable(True)
        form.addRow("Room Type:", room_type)
        
        # Number of beds
        beds = QSpinBox()
        beds.setRange(1, 10)
        form.addRow("Number of Beds:", beds)
        
        # Floor
        floor = QLineEdit()
        form.addRow("Floor:", floor)
        
        # Location
        location = QLineEdit()
        form.addRow("Location:", location)
        
        # Number of rooms to add
        num_rooms = QSpinBox()
        num_rooms.setRange(1, 100)
        num_rooms.setValue(1)
        form.addRow("Number of Rooms:", num_rooms)
        
        # Status
        status = QComboBox()
        status.addItems(["Vacant", "Occupied", "Dirty", "Clean", "Out of Order"])
        form.addRow("Status:", status)
        
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        
        layout.addLayout(form)
        layout.addWidget(buttons)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Get all existing rooms
            rooms = get_all_rooms()
            
            # Find the last room number for regular rooms and suites
            last_regular_number = 0
            last_suite_number = 0
            
            for room in rooms:
                try:
                    if room['type'].lower() == 'suite':
                        # Extract number from "Suite X" format
                        suite_num = int(room['number'].split()[-1])
                        last_suite_number = max(last_suite_number, suite_num)
                    else:
                        room_num = int(room['number'])
                        last_regular_number = max(last_regular_number, room_num)
                except (ValueError, IndexError):
                    continue
            
            # Start from the next number after the last room
            start_num = last_regular_number + 1
            start_suite_num = last_suite_number + 1
            
            for i in range(num_rooms.value()):
                if room_type.currentText().lower() == 'suite':
                    room_number = f"Suite {start_suite_num + i}"
                else:
                    room_number = str(start_num + i)
                    
                room = {
                    'number': room_number,
                    'type': room_type.currentText(),
                    'beds': beds.value(),
                    'floor': floor.text(),
                    'location': location.text(),
                    'status': status.currentText()
                }
                insert_room(room)
                
            self.load_rooms()
            QMessageBox.information(
                self,
                "Success",
                f"Successfully added {num_rooms.value()} {room_type.currentText()} rooms"
            ) 