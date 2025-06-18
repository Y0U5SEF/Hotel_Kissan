from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class DrinksConsumption(Base):
    __tablename__ = 'drinks_consumption'

    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    drink_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    consumption_date = Column(DateTime, default=datetime.now)
    notes = Column(String(255))

    # Relationships
    customer = relationship("Customer", back_populates="drinks_consumptions")

    def __init__(self, customer_id, drink_name, quantity, price_per_unit, consumption_date=None, notes=None):
        self.customer_id = customer_id
        self.drink_name = drink_name
        self.quantity = quantity
        self.price_per_unit = price_per_unit
        self.consumption_date = consumption_date or datetime.now()
        self.notes = notes

    @property
    def total_price(self):
        return self.quantity * self.price_per_unit

    def to_dict(self):
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'drink_name': self.drink_name,
            'quantity': self.quantity,
            'price_per_unit': self.price_per_unit,
            'total_price': self.total_price,
            'consumption_date': self.consumption_date.isoformat() if self.consumption_date else None,
            'notes': self.notes
        } 