from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QHBoxLayout, QSpacerItem, 
    QSizePolicy, QFrame, QMessageBox
)
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtCore import pyqtSignal
from app.core.config_handler import app_config
from app.core.auth import UserAuthenticator


class LoginForm(QWidget):
    login_successful = pyqtSignal(str)
    def __init__(self):
        super().__init__()
        self.authenticator = UserAuthenticator()
        self.setup_ui()
        self.load_styles()
        
    def setup_ui(self):
        hotel_name = app_config.get('Hotel', 'name', 'Hotel Management System')
        self.setWindowTitle(f"{hotel_name} - Login")
        self.setFixedSize(400, 500)
        
        # Set window icon
        icon_path = ":/icons/password.png"
        self.setWindowIcon(QIcon(icon_path))
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)
        
        # Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_path = ":/images/logo.png"
        self.logo_label.setPixmap(QPixmap(logo_path).scaled(120, 120, 
                      Qt.AspectRatioMode.KeepAspectRatio, 
                      Qt.TransformationMode.SmoothTransformation))
        
        # Title
        hotel_name = app_config.get('Hotel', 'name', 'HOTEL MANAGEMENT SYSTEM')
        self.title_label = QLabel(hotel_name.upper())
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setObjectName("titleLabel")
        
        # Form frame
        form_frame = QFrame()
        form_frame.setObjectName("formFrame")
        form_layout = QVBoxLayout(form_frame)
        form_layout.setContentsMargins(20, 25, 20, 25)
        form_layout.setSpacing(15)
        
        # Username field
        self.username_field = QLineEdit()
        self.username_field.setPlaceholderText("Username")
        self.username_field.setObjectName("loginField")
        self.username_field.setMinimumHeight(45)
        
        # Password field
        self.password_field = QLineEdit()
        self.password_field.setPlaceholderText("Password")
        self.password_field.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_field.setObjectName("loginField")
        self.password_field.setMinimumHeight(45)
        
        # Login button
        self.login_button = QPushButton("Login")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.setObjectName("loginButton")
        self.login_button.setMinimumHeight(45)
        self.login_button.setIcon(QIcon(":/icons/login.png"))
        self.login_button.setIconSize(QSize(24, 24))
        
        # Add widgets to form
        form_layout.addWidget(self.username_field)
        form_layout.addWidget(self.password_field)
        form_layout.addWidget(self.login_button)
        
        # Add widgets to main layout
        main_layout.addWidget(self.logo_label)
        main_layout.addSpacing(5)  # Small space after logo
        main_layout.addWidget(self.title_label)
        main_layout.addSpacing(10)  # Space between title and form
        main_layout.addWidget(form_frame)
        main_layout.addItem(QSpacerItem(20, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))
        
        # Connect signals
        self.login_button.clicked.connect(self.handle_login)
        self.password_field.returnPressed.connect(self.handle_login)
        
        self.setLayout(main_layout)
    
    def load_styles(self):
        self.setStyleSheet("""
            #titleLabel {
                font-size: 18px;
                font-weight: bold;
                color: #2c3e50;
                padding-bottom: 5px;
                margin-bottom: 5px;
            }
            
            #formFrame {
                background-color: transparent;
                border-radius: 10px;
            }
            
            /* Style for QLineEdit */
            QLineEdit#loginField {
                font-size: 18px;
                padding: 5px 15px;
                border: 1px solid #a6acaf;
                border-radius: 6px;
                background-color: #f9f9f9;
                color: #333;
                margin-bottom: 5px;
            }
            
            QLineEdit#loginField:focus {
                border-color: #3498db;
                background-color: #fff;
            }
            
            QLineEdit#loginField:hover {
                border-color: #bdc3c7;
            }
            
            /* Style for QPushButton */
            QPushButton#loginButton {
                font-size: 16px;
                font-weight: bold;
                color: white;
                background-color: #3498db;
                border: none;
                border-radius: 6px;
                padding: 5px 20px;
                text-align: center;
                margin-top: 10px;
            }
            
            QPushButton#loginButton:hover {
                background-color: #2980b9;
            }
            
            QPushButton#loginButton:pressed {
                background-color: #1a6ea0;
            }
            
            QPushButton#loginButton::icon {
                padding-left: 10px;
            }
            
            QWidget {
                background-color: #f5f7fa;
            }
        """)
    
    def handle_login(self):
        """Handle login button click"""
        username = self.username_field.text().strip()
        password = self.password_field.text()
        
        if not username or not password:
            QMessageBox.warning(
                self,
                "Login Error",
                "Please enter both username and password.",
                QMessageBox.StandardButton.Ok
            )
            return
        
        if self.authenticator.authenticate(username, password):
            # Get user's full name from authenticator
            full_name = self.authenticator.get_full_name()
            self.login_successful.emit(full_name)
            self.close()  # Close the login form after successful login
        else:
            QMessageBox.warning(
                self,
                "Login Failed",
                "Invalid username or password.",
                QMessageBox.StandardButton.Ok
            )
            self.password_field.clear()
            self.password_field.setFocus()