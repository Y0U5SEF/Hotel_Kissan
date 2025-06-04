from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSizePolicy, QGridLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QDialog, QDialogButtonBox,
    QCheckBox
)
from PyQt6.QtCore import Qt, QDateTime, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QColor, QPainter, QIcon
from PyQt6.QtCharts import QChart, QChartView, QLineSeries, QPieSeries
from app.core.db import get_all_rooms, get_available_rooms_count, get_reservations, get_all_checkins, update_room
from datetime import datetime

class KPIWidget(QFrame):
    """Widget for displaying KPI metrics"""
    def __init__(self, title, value, suffix="", icon_path=None, parent=None):
        super().__init__(parent)
        self.setObjectName("kpiWidget")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setFrameShadow(QFrame.Shadow.Raised)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(140)  # Increased height to accommodate spacing
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(12)  # Increased spacing between elements
        
        # Icon
        if icon_path:
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon_path).pixmap(48, 48))
            icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_label.setMinimumSize(48, 48)
            icon_label.setContentsMargins(0, 0, 0, 8)  # Add bottom margin to icon
            layout.addWidget(icon_label)
            
        # Title
        title_label = QLabel(title)
        title_label.setObjectName("kpiTitle")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setContentsMargins(0, 4, 0, 4)  # Add vertical margins to title
        layout.addWidget(title_label)
        
        # Value
        value_label = QLabel(f"{value}{suffix}")
        value_label.setObjectName("kpiValue")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setContentsMargins(0, 4, 0, 0)  # Add top margin to value
        
        # Make value text bold, bigger and blue
        font = QFont()
        font.setBold(True)
        font.setPointSize(18)
        value_label.setFont(font)
        value_label.setStyleSheet("color: #2196F3;")
        layout.addWidget(value_label)
        
        self.title_label = title_label
        self.value_label = value_label
    def update_value(self, value, suffix=""):
        """Update the KPI value"""
        self.value_label.setText(f"{value}{suffix}")


class QuickActionButton(QPushButton):
    """Styled button for quick actions"""
    def __init__(self, text, icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setObjectName("quickActionButton")
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumHeight(50)
        if icon_path:
            self.setIcon(QIcon(icon_path))


class ActivityItem(QFrame):
    """Widget for displaying a single activity item"""
    def __init__(self, title, description, time, is_notification=False, parent=None):
        super().__init__(parent)
        self.setObjectName("activityItem")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header with title and time
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        
        title_label = QLabel(title)
        title_label.setObjectName("activityTitle")
        title_label.setWordWrap(True)
        header_layout.addWidget(title_label)
        
        time_label = QLabel(time)
        time_label.setObjectName("activityTime")
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header_layout.addWidget(time_label)
        
        layout.addLayout(header_layout)
        
        # Description
        desc_label = QLabel(description)
        desc_label.setObjectName("activityDescription")
        desc_label.setWordWrap(True)
        layout.addWidget(desc_label)
        
        # Set special style for notifications
        if is_notification:
            self.setObjectName("notificationItem")


class ReservationCard(QFrame):
    """Widget for displaying a single reservation card"""
    def __init__(self, guest_name, arrival_date, room_number, parent=None):
        super().__init__(parent)
        self.setObjectName("reservationCard")
        self.setFrameShape(QFrame.Shape.StyledPanel)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Guest name with icon
        name_layout = QHBoxLayout()
        name_icon = QLabel()
        name_icon.setPixmap(QIcon(":/icons/person_96px.png").pixmap(16, 16))
        name_layout.addWidget(name_icon)
        name_label = QLabel(guest_name)
        name_label.setObjectName("reservationGuestName")
        name_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        name_layout.addWidget(name_label)
        name_layout.addStretch()
        layout.addLayout(name_layout)
        
        # Arrival date with icon
        date_layout = QHBoxLayout()
        date_icon = QLabel()
        date_icon.setPixmap(QIcon(":/icons/calendar_96px.png").pixmap(16, 16))
        date_layout.addWidget(date_icon)
        date_label = QLabel(f"Arrival: {arrival_date}")
        date_label.setObjectName("reservationDate")
        date_layout.addWidget(date_label)
        date_layout.addStretch()
        layout.addLayout(date_layout)
        
        # Room number with icon
        room_layout = QHBoxLayout()
        room_icon = QLabel()
        room_icon.setPixmap(QIcon(":/icons/room_96px.png").pixmap(16, 16))
        room_layout.addWidget(room_icon)
        room_label = QLabel(f"Room: {room_number}")
        room_label.setObjectName("reservationRoom")
        room_layout.addWidget(room_label)
        room_layout.addStretch()
        layout.addLayout(room_layout)


class DashboardWidget(QWidget):
    """Main dashboard widget"""
    
    # Signals
    new_reservation_clicked = pyqtSignal()
    check_in_clicked = pyqtSignal()
    check_out_clicked = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
        # Update time every second
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)
        
        # Initial time update
        self.update_time()
        
        # Load sample data
        self.load_sample_data()
        
    def setup_ui(self):
        """Set up the dashboard UI"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Dashboard header
        header_layout = QHBoxLayout()
        
        # Dashboard title
        title_label = QLabel("Dashboard")
        title_label.setObjectName("dashboardTitle")
        header_layout.addWidget(title_label)
        
        # Current date and time
        self.datetime_label = QLabel()
        self.datetime_label.setObjectName("datetimeLabel")
        self.datetime_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        font = QFont()
        font.setBold(True)  # Make it bold
        self.datetime_label.setFont(font)
        header_layout.addWidget(self.datetime_label)
        
        main_layout.addLayout(header_layout)
        
        # KPI section
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        self.occupancy_kpi = KPIWidget("Occupancy Rate", "0", "%", ":/icons/occupancy.png")
        kpi_layout.addWidget(self.occupancy_kpi)
        self.available_rooms_kpi = KPIWidget("Available Rooms", str(get_available_rooms_count()), "", ":/icons/available_rooms.png")
        kpi_layout.addWidget(self.available_rooms_kpi)
        self.arrivals_kpi = KPIWidget("Arrivals Today", "0", "", ":/icons/arrivals.png")
        kpi_layout.addWidget(self.arrivals_kpi)
        self.departures_kpi = KPIWidget("Departures Today", "0", "", ":/icons/departures.png")
        kpi_layout.addWidget(self.departures_kpi)
        
        main_layout.addLayout(kpi_layout)

        # Horizontal row for main dashboard sections
        dashboard_row = QHBoxLayout()
        dashboard_row.setSpacing(15)

        # Quick Actions and Recent Reservations (40% combined)
        left_sidebar_frame = QFrame()
        left_sidebar_frame.setObjectName("leftSidebarFrame")
        left_sidebar_layout = QVBoxLayout(left_sidebar_frame)
        left_sidebar_layout.setSpacing(20)  # Add spacing between sections
        
        # Quick Actions Section
        quick_actions_frame = QFrame()
        quick_actions_frame.setObjectName("quickActionsFrame")
        quick_actions_frame.setFrameShape(QFrame.Shape.StyledPanel)
        quick_actions_layout = QVBoxLayout(quick_actions_frame)
        quick_actions_layout.setContentsMargins(10, 10, 10, 10)
        
        quick_actions_title = QLabel("Quick Actions")
        quick_actions_title.setObjectName("sectionTitle")
        quick_actions_layout.addWidget(quick_actions_title)
        
        check_in_btn = QuickActionButton("Check-In", ":/icons/checkin.png")
        check_in_btn.clicked.connect(self.check_in_clicked)
        quick_actions_layout.addWidget(check_in_btn)
        
        check_out_btn = QuickActionButton("Check-Out", ":/icons/checkout.png")
        check_out_btn.clicked.connect(self.check_out_clicked)
        quick_actions_layout.addWidget(check_out_btn)
        
        new_reservation_btn = QuickActionButton("New Reservation", ":/icons/reservation.png")
        new_reservation_btn.clicked.connect(self.new_reservation_clicked)
        quick_actions_layout.addWidget(new_reservation_btn)

        # Add Update Room Status button
        update_room_status_btn = QuickActionButton("Update Room Status", ":/icons/room_96px.png")
        update_room_status_btn.clicked.connect(self.show_update_room_status_dialog)
        quick_actions_layout.addWidget(update_room_status_btn)
        
        left_sidebar_layout.addWidget(quick_actions_frame)
        
        # Recent Reservations Section
        reservations_frame = QFrame()
        reservations_frame.setObjectName("reservationsFrame")
        reservations_frame.setFrameShape(QFrame.Shape.StyledPanel)
        reservations_layout = QVBoxLayout(reservations_frame)
        reservations_layout.setContentsMargins(10, 10, 10, 10)
        
        reservations_title = QLabel("Recent Reservations")
        reservations_title.setObjectName("sectionTitle")
        reservations_title.setContentsMargins(0, 0, 0, 0)  # Remove margins from title
        reservations_layout.addWidget(reservations_title)
        
        # Create scroll area for reservations
        reservations_scroll = QScrollArea()
        reservations_scroll.setWidgetResizable(True)
        reservations_scroll.setFrameShape(QFrame.Shape.NoFrame)
        reservations_scroll.setContentsMargins(0, 0, 0, 0)  # Remove margins from scroll area
        
        # Create container for reservation cards
        reservations_container = QWidget()
        self.reservations_container_layout = QVBoxLayout(reservations_container)
        self.reservations_container_layout.setSpacing(10)
        self.reservations_container_layout.setContentsMargins(0, 0, 0, 0)  # Remove margins from container layout
        reservations_scroll.setWidget(reservations_container)
        reservations_layout.addWidget(reservations_scroll)
        
        left_sidebar_layout.addWidget(reservations_frame)
        
        # Add stretch at the end to push everything up
        left_sidebar_layout.addStretch()
        
        # Add the combined frame to the dashboard row
        dashboard_row.addWidget(left_sidebar_frame, 2)  # Takes 40% of the width

        # Room Occupancy Status (30%)
        room_grid_frame = QFrame()
        room_grid_frame.setObjectName("roomGridFrame")
        room_grid_frame.setFrameShape(QFrame.Shape.StyledPanel)
        room_grid_layout = QVBoxLayout(room_grid_frame)
        
        room_grid_title = QLabel("Room Occupancy Status")
        room_grid_title.setObjectName("sectionTitle")
        room_grid_layout.addWidget(room_grid_title)
        
        # Add legend
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(20)
        
        # Available (Green)
        available_legend = QWidget()
        available_layout = QHBoxLayout(available_legend)
        available_layout.setContentsMargins(0, 0, 0, 0)
        available_layout.setSpacing(5)
        available_color = QLabel()
        available_color.setFixedSize(16, 16)
        available_color.setStyleSheet("background-color: #27ae60; border: 1px solid #ccc;")
        available_text = QLabel("Available")
        available_layout.addWidget(available_color)
        available_layout.addWidget(available_text)
        legend_layout.addWidget(available_legend)
        
        # Reserved (Purple)
        reserved_legend = QWidget()
        reserved_layout = QHBoxLayout(reserved_legend)
        reserved_layout.setContentsMargins(0, 0, 0, 0)
        reserved_layout.setSpacing(5)
        reserved_color = QLabel()
        reserved_color.setFixedSize(16, 16)
        reserved_color.setStyleSheet("background-color: #8e44ad; border: 1px solid #ccc;")
        reserved_text = QLabel("Reserved")
        reserved_layout.addWidget(reserved_color)
        reserved_layout.addWidget(reserved_text)
        legend_layout.addWidget(reserved_legend)
        
        # Occupied (Red)
        occupied_legend = QWidget()
        occupied_layout = QHBoxLayout(occupied_legend)
        occupied_layout.setContentsMargins(0, 0, 0, 0)
        occupied_layout.setSpacing(5)
        occupied_color = QLabel()
        occupied_color.setFixedSize(16, 16)
        occupied_color.setStyleSheet("background-color: #c0392b; border: 1px solid #ccc;")
        occupied_text = QLabel("Occupied")
        occupied_layout.addWidget(occupied_color)
        occupied_layout.addWidget(occupied_text)
        legend_layout.addWidget(occupied_legend)

        # Not Available (Gray)
        not_available_legend = QWidget()
        not_available_layout = QHBoxLayout(not_available_legend)
        not_available_layout.setContentsMargins(0, 0, 0, 0)
        not_available_layout.setSpacing(5)
        not_available_color = QLabel()
        not_available_color.setFixedSize(16, 16)
        not_available_color.setStyleSheet("background-color: #95a5a6; border: 1px solid #ccc;")
        not_available_text = QLabel("Not Available")
        not_available_layout.addWidget(not_available_color)
        not_available_layout.addWidget(not_available_text)
        legend_layout.addWidget(not_available_legend)

        # Needs Cleaning (Yellow)
        needs_cleaning_legend = QWidget()
        needs_cleaning_layout = QHBoxLayout(needs_cleaning_legend)
        needs_cleaning_layout.setContentsMargins(0, 0, 0, 0)
        needs_cleaning_layout.setSpacing(5)
        needs_cleaning_color = QLabel()
        needs_cleaning_color.setFixedSize(16, 16)
        needs_cleaning_color.setStyleSheet("background-color: #f1c40f; border: 1px solid #ccc;")
        needs_cleaning_text = QLabel("Needs Cleaning")
        needs_cleaning_layout.addWidget(needs_cleaning_color)
        needs_cleaning_layout.addWidget(needs_cleaning_text)
        legend_layout.addWidget(needs_cleaning_legend)
        
        legend_layout.addStretch()
        room_grid_layout.addLayout(legend_layout)
        
        # Create scroll area for the grid
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        # Create a container widget for the grid
        grid_container = QWidget()
        grid_container.setStyleSheet("background: transparent;")
        grid_container_layout = QVBoxLayout(grid_container)
        grid_container_layout.setContentsMargins(0, 0, 0, 0)
        grid_container_layout.setSpacing(0)
        
        self.room_grid = QGridLayout()
        self.room_grid.setSpacing(10)
        grid_container_layout.addLayout(self.room_grid)
        grid_container_layout.addStretch()
        
        # Set the grid container as the scroll area's widget
        scroll_area.setWidget(grid_container)
        room_grid_layout.addWidget(scroll_area)
        dashboard_row.addWidget(room_grid_frame, 4) # Room grid keeps 30% of remaining space

        # Occupancy Rate Trend (30%)
        charts_frame = QFrame()
        charts_frame.setVisible(False)
        charts_frame.setObjectName("chartsFrame")
        charts_frame.setFrameShape(QFrame.Shape.StyledPanel)
        charts_layout = QVBoxLayout(charts_frame)
        charts_title = QLabel("Occupancy Rate Trend")
        charts_title.setObjectName("sectionTitle")
        charts_layout.addWidget(charts_title)
        self.occupancy_chart = self.create_occupancy_chart()
        occupancy_chart_view = QChartView(self.occupancy_chart)
        occupancy_chart_view.setRenderHint(QPainter.RenderHint.Antialiasing)
        charts_layout.addWidget(occupancy_chart_view)
        dashboard_row.addWidget(charts_frame, 3) # Occupancy trend keeps 30% of remaining space

        # Recent Activity (20%)
        activity_frame = QFrame()
        activity_frame.setObjectName("activityFrame")
        activity_frame.setFrameShape(QFrame.Shape.StyledPanel)
        activity_layout = QVBoxLayout(activity_frame)
        activity_title = QLabel("Recent Activity")
        activity_title.setObjectName("sectionTitle")
        activity_layout.addWidget(activity_title)
        activity_scroll = QScrollArea()
        activity_scroll.setWidgetResizable(True)
        activity_scroll.setFrameShape(QFrame.Shape.NoFrame)
        activity_container = QWidget()
        self.activity_container_layout = QVBoxLayout(activity_container)
        activity_scroll.setWidget(activity_container)
        activity_layout.addWidget(activity_scroll)
        dashboard_row.addWidget(activity_frame, 1) # Recent activity keeps 20% of remaining space

        main_layout.addLayout(dashboard_row)
        self.load_room_grid()
        self.load_recent_reservations()
        
    def update_time(self):
        """Update the current date and time display"""
        current_datetime = QDateTime.currentDateTime()
        formatted_datetime = current_datetime.toString("dddd, MMMM d, yyyy - hh:mm:ss AP")
        self.datetime_label.setText(formatted_datetime)
        
    def create_occupancy_chart(self):
        """Create the occupancy rate line chart"""
        chart = QChart()
        chart.setTitle("Occupancy Rate (Last 7 Days)")
        chart.setAnimationOptions(QChart.AnimationOption.SeriesAnimations)
        
        series = QLineSeries()
        
        # Sample data will be loaded later
        
        chart.addSeries(series)
        chart.createDefaultAxes()
        chart.legend().setVisible(False)
        
        return chart
        
    def load_sample_data(self):
        """Load sample data for the dashboard"""
        # Occupancy rate data for the last 7 days
        occupancy_data = [65, 70, 68, 72, 75, 78, 75]
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        occupancy_series = QLineSeries()
        for i, value in enumerate(occupancy_data):
            occupancy_series.append(i, value)
        self.occupancy_chart.removeAllSeries()
        self.occupancy_chart.addSeries(occupancy_series)
        self.occupancy_chart.createDefaultAxes()
        
        # Recent activity data
        activities = [
            {
                "title": "Check-in",
                "description": "John Smith checked in to room 301",
                "time": "15:05",
                "is_notification": False
            },
            {
                "title": "Check-out",
                "description": "Sarah Johnson checked out from room 205",
                "time": "14:30",
                "is_notification": False
            },
            {
                "title": "New Reservation",
                "description": "Michael Brown made a reservation for next week",
                "time": "13:45",
                "is_notification": False
            },
            {
                "title": "Low Stock Alert",
                "description": "Bathroom amenities running low",
                "time": "12:20",
                "is_notification": True
            },
            {
                "title": "Room Service Request",
                "description": "Room 402 requested extra towels",
                "time": "11:55",
                "is_notification": True
            }
        ]
        
        # Clear existing activities
        for i in reversed(range(self.activity_container_layout.count())):
            self.activity_container_layout.itemAt(i).widget().deleteLater()
            
        # Add new activities
        for activity in activities:
            activity_item = ActivityItem(
                activity["title"],
                activity["description"],
                activity["time"],
                activity["is_notification"]
            )
            self.activity_container_layout.addWidget(activity_item)
            
        # Add stretch at the end
        self.activity_container_layout.addStretch()

    def load_room_grid(self):
        rooms = get_all_rooms()
        cols = 3 if len(rooms) < 12 else 8
        for i in reversed(range(self.room_grid.count())):
            widget = self.room_grid.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Get all check-ins to find guest information for occupied rooms
        checkins = get_all_checkins()
        
        for idx, room in enumerate(rooms):
            btn = QPushButton(f"{room['number']}\n{room.get('type','')}")
            btn.setMinimumSize(80, 60)
            status = room.get('status', 'Vacant')
            
            # Set different colors based on room status
            if status == "Vacant":
                btn.setStyleSheet("""
                    QPushButton {
                        min-height:50px;
                        background: #27ae60;
                        color: white;
                        font-weight: bold;
                        border-radius: 0px;
                    }
                    QPushButton:hover {
                        background: #2ecc71;
                    }
                """)
            elif status == "Reserved":
                btn.setStyleSheet("""
                    QPushButton {
                        min-height:50px;
                        background: #8e44ad;
                        color: white;
                        font-weight: bold;
                        border-radius: 0px;
                    }
                    QPushButton:hover {
                        background: #9b59b6;
                    }
                """)
            elif status == "Not Available":
                btn.setStyleSheet("""
                    QPushButton {
                        min-height:50px;
                        background: #95a5a6;
                        color: white;
                        font-weight: bold;
                        border-radius: 0px;
                    }
                    QPushButton:hover {
                        background: #7f8c8d;
                    }
                """)
            elif status == "Needs Cleaning":
                btn.setStyleSheet("""
                    QPushButton {
                        min-height:50px;
                        background: #f1c40f;
                        color: white;
                        font-weight: bold;
                        border-radius: 0px;
                    }
                    QPushButton:hover {
                        background: #f39c12;
                    }
                """)
            else:  # Occupied or other statuses
                btn.setStyleSheet("""
                    QPushButton {
                        min-height:50px;
                        background: #c0392b;
                        color: white;
                        font-weight: bold;
                        border-radius: 0px;
                    }
                    QPushButton:hover {
                        background: #e74c3c;
                    }
                """)
            
            # Build tooltip with room and guest information
            tooltip = f"Room {room['number']}\nType: {room.get('type','')}\nStatus: {status}"
            
            # Add guest information for occupied rooms
            if status == "Occupied":
                # Find the active check-in for this room
                active_checkin = next(
                    (c for c in checkins 
                     if c['room_id'] == room['id'] 
                     and c['status'] == 'checked_in'),
                    None
                )
                if active_checkin:
                    guest_name = f"{active_checkin['first_name']} {active_checkin['last_name']}"
                    tooltip += f"\nGuest: {guest_name}"
            
            btn.setToolTip(tooltip)
            btn.setStyleSheet(btn.styleSheet() + """
                QToolTip {
                    background-color: #ffffff;
                    color: #2c3e50;
                    border: 1px solid #bdc3c7;
                    padding: 5px;
                    border-radius: 4px;
                }
            """)
            btn.setEnabled(False)  # Disable clicking
            self.room_grid.addWidget(btn, idx // cols, idx % cols)

    def update_occupancy_kpi(self):
        rooms = get_all_rooms()
        total_rooms = len(rooms)
        occupied_rooms = sum(1 for r in rooms if r.get('status') != 'Vacant')
        occupancy_rate = int((occupied_rooms / total_rooms) * 100) if total_rooms > 0 else 0
        self.occupancy_kpi.update_value(str(occupancy_rate), "%")

    def update_arrivals_departures(self):
        """Update arrivals and departures counts based on today's check-ins and check-outs"""
        today = datetime.now().strftime('%Y-%m-%d')
        arrivals_count = 0
        departures_count = 0
        
        # Get all check-ins
        checkins = get_all_checkins()
        
        for checkin in checkins:
            # Count arrivals (check-ins) for today
            if checkin['arrival_date'] == today:
                arrivals_count += 1
                
            # Count departures (check-outs) for today
            if checkin['departure_date'] == today:
                departures_count += 1
        
        # Update KPI widgets
        self.arrivals_kpi.update_value(str(arrivals_count))
        self.departures_kpi.update_value(str(departures_count))

    def load_recent_reservations(self):
        """Load and display recent reservations"""
        # Get all reservations
        reservations = get_reservations()
        
        # Sort reservations by arrival date (most recent first)
        reservations.sort(key=lambda x: datetime.strptime(x['arrival_date'], '%Y-%m-%d'), reverse=True)
        
        # Clear existing reservations
        while self.reservations_container_layout.count():
            item = self.reservations_container_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        if not reservations:
            # Create a label for no reservations
            no_reservations_label = QLabel("No Reservations")
            no_reservations_label.setObjectName("noReservationsLabel")
            no_reservations_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_reservations_label.setStyleSheet("""
                QLabel {
                    color: #7f8c8d;
                    font-size: 16px;
                    padding: 20px;
                }
            """)
            self.reservations_container_layout.addWidget(no_reservations_label)
        else:
            # Add new reservation cards (limit to 5 most recent)
            for reservation in reservations[:5]:
                guest_name = f"{reservation['guest_first_name']} {reservation['guest_last_name']}"
                arrival_date = reservation['arrival_date']
                room_number = reservation['room_id']
                
                card = ReservationCard(guest_name, arrival_date, room_number)
                self.reservations_container_layout.addWidget(card)
        
        # Add stretch at the end
        self.reservations_container_layout.addStretch()

    def showEvent(self, event):
        """Handle show event"""
        super().showEvent(event)
        self.load_room_grid()
        self.update_occupancy_kpi()
        self.update_available_rooms()
        self.update_arrivals_departures()
        self.load_recent_reservations()
        
    def update_available_rooms(self):
        """Update the available rooms count"""
        available_count = get_available_rooms_count()
        self.available_rooms_kpi.update_value(str(available_count))

    def show_update_room_status_dialog(self):
        """Show dialog to update room status from needs cleaning to vacant"""
        # Get all rooms that need cleaning
        rooms = get_all_rooms()
        rooms_needing_cleaning = [room for room in rooms if room.get('status') == 'Needs Cleaning']
        
        if not rooms_needing_cleaning:
            QMessageBox.information(self, "No Rooms Need Cleaning", 
                                  "There are no rooms that need cleaning at the moment.")
            return
        
        # Create dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Update Room Status")
        dialog.setMinimumWidth(400)
        layout = QVBoxLayout(dialog)
        
        # Add explanation label
        explanation = QLabel("Select rooms to mark as Vacant after cleaning:")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)
        
        # Create scroll area for room list
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(300)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # Add checkboxes for each room
        room_checkboxes = {}
        for room in rooms_needing_cleaning:
            room_widget = QWidget()
            room_layout = QHBoxLayout(room_widget)
            
            checkbox = QCheckBox(f"Room {room['number']} - {room.get('type', '')}")
            room_checkboxes[room['id']] = checkbox
            room_layout.addWidget(checkbox)
            
            scroll_layout.addWidget(room_widget)
        
        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Add buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | 
            QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Update selected rooms
            updated_count = 0
            for room_id, checkbox in room_checkboxes.items():
                if checkbox.isChecked():
                    room = next((r for r in rooms if r['id'] == room_id), None)
                    if room:
                        updated_room = dict(room)
                        updated_room['status'] = 'Vacant'
                        update_room(room_id, updated_room)
                        updated_count += 1
            
            # Show success message
            if updated_count > 0:
                QMessageBox.information(self, "Success", 
                                      f"Successfully updated {updated_count} room(s) to Vacant status.")
                # Refresh room grid and KPIs
                self.load_room_grid()
                self.update_available_rooms()
            else:
                QMessageBox.information(self, "No Changes", 
                                      "No rooms were selected for status update.")