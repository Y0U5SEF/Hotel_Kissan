from app.core.database import Base, engine
from app.models.customer import Customer
from app.models.drinks_consumption import DrinksConsumption

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    init_db()
    print("Database tables created successfully!") 