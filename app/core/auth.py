import uuid
import platform
import bcrypt
import secrets
from app.core.config_handler import app_config
from app.core.db import get_user_by_username, create_user

class MachineAuthorizer:
    def __init__(self, check_enabled=True):
        self.check_enabled = check_enabled
        self.machine_id = self._get_machine_id()
    
    def _get_machine_id(self):
        """Get a unique identifier for this machine"""
        # Get system information
        system_info = platform.uname()
        # Create a unique ID based on hardware info
        machine_id = uuid.uuid5(uuid.NAMESPACE_DNS, 
                               f"{system_info.node}-{system_info.machine}-{system_info.processor}")
        return str(machine_id)
    
    def is_authorized(self):
        """Check if this machine is authorized to run the application"""
        # If checking is disabled, always return True
        if not self.check_enabled:
            return True
            
        # Get allowed machines from config
        allowed_machines = app_config.get('Security', 'allowed_machines', '')
        if not allowed_machines:
            # If no machines are specified, authorize this one and add it
            app_config.add_authorized_machine(self.machine_id)
            return True
            
        # Check if this machine is in the allowed list
        machine_list = [m.strip() for m in allowed_machines.split(',')]
        return self.machine_id in machine_list
    
    def get_machine_id(self):
        """Return the machine ID"""
        return self.machine_id

class UserAuthenticator:
    def __init__(self):
        self.current_user = None
    
    def hash_password(self, password, salt=None):
        """Hash a password using bcrypt"""
        # Convert password to bytes if it's a string
        if isinstance(password, str):
            password = password.encode('utf-8')
        
        # Generate salt if not provided
        if salt is None:
            salt = bcrypt.gensalt()
        elif isinstance(salt, str):
            salt = salt.encode('utf-8')
            
        # Hash the password
        hashed = bcrypt.hashpw(password, salt)
        return hashed.decode('utf-8')
    
    def verify_password(self, password, stored_hash):
        """Verify a password against its bcrypt hash"""
        # Convert inputs to bytes
        if isinstance(password, str):
            password = password.encode('utf-8')
        if isinstance(stored_hash, str):
            stored_hash = stored_hash.encode('utf-8')
            
        return bcrypt.checkpw(password, stored_hash)
    
    def authenticate(self, username, password):
        """Authenticate a user"""
        user = get_user_by_username(username)
        if not user:
            return False
        
        if not user['is_active']:
            return False
        
        if not self.verify_password(password, user['password_hash']):
            return False
        
        self.current_user = user
        return True
    
    def create_new_user(self, username, password, first_name, last_name, role):
        """Create a new user account"""
        password_hash = self.hash_password(password)
        return create_user(username, password_hash, first_name, last_name, role)
    
    def get_current_user(self):
        """Get the currently authenticated user"""
        return self.current_user
    
    def get_full_name(self):
        """Get the full name of the current user"""
        if self.current_user:
            return f"{self.current_user['first_name']} {self.current_user['last_name']}"
        return None
    
    def logout(self):
        """Log out the current user"""
        self.current_user = None
