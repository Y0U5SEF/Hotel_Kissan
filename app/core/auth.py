import uuid
import platform
from app.core.config_handler import app_config

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
