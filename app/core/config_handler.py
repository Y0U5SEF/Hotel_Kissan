import os
import configparser
from pathlib import Path
from PyQt6.QtCore import QStandardPaths
import sys

class ConfigManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.init_config()
        return cls._instance
    
    def init_config(self):
        self.config = configparser.ConfigParser(interpolation=None)
        
        # Get the base directory - works for both development and packaged environments
        if getattr(sys, 'frozen', False):
            # If the application is run as a bundle
            base_dir = Path(sys._MEIPASS)
        else:
            # If the application is run from a Python interpreter
            base_dir = Path(__file__).parent.parent
        
        # Create config directory in the appropriate location
        if getattr(sys, 'frozen', False):
            # For packaged app, use APPDATA
            config_dir = Path(self.get_appdata_path()) / 'config'
        else:
            # For development, use project directory
            config_dir = base_dir / 'config'
        
        # Create config directory if it doesn't exist
        config_dir.mkdir(parents=True, exist_ok=True)
        
        self.config_path = config_dir / 'config.ini'
        
        # Create default config if doesn't exist
        if not self.config_path.exists():
            self.create_default_config()
        
        self.config.read(self.config_path)
        self.expand_path_variables()
    
    def expand_path_variables(self):
        """Expand environment variables in paths"""
        appdata = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        
        if 'Database' in self.config:
            self.config['Database']['path'] = os.path.expandvars(
                self.config['Database']['path'].replace(
                    '%APPDATA%', 
                    str(Path(appdata) / 'KISSAN')
                )
            )
            self.config['Database']['backup_path'] = os.path.expandvars(
                self.config['Database']['backup_path'].replace(
                    '%APPDATA%', 
                    str(Path(appdata) / 'KISSAN')
                )
            )
    
    def create_default_config(self):
        """Create default configuration file"""
        self.config['Hotel'] = {
            'name': 'Grand Plaza Hotel',
            'address': '123 Hospitality Avenue, Cityville',
            'phone': '+1 (555) 123-4567',
            'email': 'info@grandplazahotel.com',
            'website': 'www.grandplazahotel.com',
            'tax_id': 'US-123-456-789',
            'logo_path': 'resources/logo.png',
            'default_check_in_time': '14:00',
            'default_check_out_time': '12:00',
            'currency': 'USD',
            'tax_rate': '8.5'
        }
        
        # Add Database section
        self.config['Database'] = {
            'path': '%APPDATA%/kissan.db',
            'backup_path': '%APPDATA%/backups'
        }
        
        # Add Security section
        self.config['Security'] = {
            'machine_authorization': 'yes',
            'allowed_machines': ''
        }
        
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
    
    def get(self, section, key, default=None):
        """Get a configuration value"""
        try:
            return self.config.get(section, key)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
    
    def set(self, section, key, value):
        """Set a configuration value"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = str(value)
        self.save_config()
    
    def save_config(self):
        """Save configuration to file"""
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)
    
    def get_hotel_info(self):
        """Get all hotel information as a dictionary"""
        return dict(self.config['Hotel'])
    
    def get_database_path(self):
        """Get the database path with expanded variables"""
        return self.config['Database']['path']
    
    def add_authorized_machine(self, machine_id):
        """Add a new authorized machine"""
        current = self.get('Security', 'allowed_machines', '')
        machines = [m.strip() for m in current.split(',') if m.strip()]
        if machine_id not in machines:
            machines.append(machine_id)
            self.set('Security', 'allowed_machines', ','.join(machines))
    
    def get_appdata_path(self):
        if sys.platform == 'win32':
            return os.path.join(os.environ['APPDATA'], 'KISSAN')
        else:
            return os.path.expanduser('~/.kissan')
    
    def get_db_path(self):
        appdata = self.get_appdata_path()
        if not os.path.exists(appdata):
            os.makedirs(appdata)
        return os.path.join(appdata, 'kissan.db')

# Singleton instance
app_config = ConfigManager()