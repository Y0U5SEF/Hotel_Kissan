from app.core.auth import UserAuthenticator
from app.core.db import init_db

def create_admin_user():
    """Create the initial admin user"""
    # Initialize database
    init_db()
    
    # Create authenticator
    auth = UserAuthenticator()
    
    # Create admin user
    success = auth.create_new_user(
        username="admin",
        password="admin123",  # Change this password in production!
        first_name="System",
        last_name="Administrator",
        role="admin"
    )
    
    if success:
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: admin123")
        print("\nIMPORTANT: Please change the admin password after first login!")
    else:
        print("Failed to create admin user. The user might already exist.")

if __name__ == "__main__":
    create_admin_user() 