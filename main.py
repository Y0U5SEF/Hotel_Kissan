import sys
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtGui import QIcon
from app.core.config_handler import app_config
from app.ui.login_form import LoginForm
from app.ui.main_window import MainWindow
from app.core.auth import MachineAuthorizer
from app.resources.resources import register_resources, unregister_resources
from app.core.db import init_db
import resources_rc  # type: ignore # noqa: F401 (registers Qt resources)
from app.core.dev_config import DEV_MODE  # <-- moved here


# Development mode flag - Set to False for production
DEV_MODE = False  # <-- removed

class HotelManagementApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.login_window = None
        self.main_window = None
        
        # Initialize application
        self.setup_application()
        
    def setup_application(self):
        """Initialize application components"""
        # Check machine authorization if not in dev mode
        if not DEV_MODE and not self.check_authorization():
            QMessageBox.critical(
                None,
                "Authorization Failed",
                "This machine is not authorized to run the application."
            )
            sys.exit(1)
            
        # Show appropriate window based on DEV_MODE
        if DEV_MODE:
            self.show_main_window()
        else:
            self.show_login_window()
    
    def check_authorization(self):
        """Check if machine is authorized"""
        authorizer = MachineAuthorizer(app_config.get('Security', 'machine_authorization', 'yes') == 'yes')
        return authorizer.is_authorized()
    
    def show_login_window(self):
        """Show login window"""
        self.login_window = LoginForm()
        self.login_window.show()
        self.login_window.login_successful.connect(self.on_login_success)
        
    def show_main_window(self):
        """Show main application window"""
        self.main_window = MainWindow()
        self.main_window.show()
        
    def on_login_success(self, full_name):
        """Handle successful login"""
        if self.login_window:
            self.login_window.close()
        self.show_main_window()
        if self.main_window:
            self.main_window.on_login_successful(full_name)
    
    def run(self):
        """Run application event loop"""
        sys.exit(self.app.exec())

if __name__ == "__main__":
    # Register application resources
    register_resources()
    # Initialize the database
    init_db()
    # Initialize and run application
    application = HotelManagementApp()
    application.run()
    # Clean up resources when application exits
    unregister_resources()