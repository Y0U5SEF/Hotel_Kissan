from datetime import datetime
from sqlalchemy.orm import Session
from app.models.drinks_consumption import DrinksConsumption
from app.models.customer import Customer

class DrinksService:
    def __init__(self, db_session: Session):
        self.db = db_session

    def add_drink_consumption(self, customer_id: int, drink_name: str, quantity: int, 
                            price_per_unit: float, consumption_date: datetime = None, notes: str = None) -> DrinksConsumption:
        consumption = DrinksConsumption(
            customer_id=customer_id,
            drink_name=drink_name,
            quantity=quantity,
            price_per_unit=price_per_unit,
            consumption_date=consumption_date,
            notes=notes
        )
        self.db.add(consumption)
        self.db.commit()
        self.db.refresh(consumption)
        return consumption

    def get_customer_consumptions(self, customer_id: int) -> list[DrinksConsumption]:
        return self.db.query(DrinksConsumption).filter(
            DrinksConsumption.customer_id == customer_id
        ).all()

    def get_all_consumptions(self) -> list[DrinksConsumption]:
        return self.db.query(DrinksConsumption).all()

    def generate_customer_bill(self, customer_id: int) -> dict:
        consumptions = self.get_customer_consumptions(customer_id)
        customer = self.db.query(Customer).get(customer_id)
        
        if not customer:
            raise ValueError("Customer not found")

        total_amount = sum(cons.total_price for cons in consumptions)
        
        return {
            'customer': customer.to_dict(),
            'consumptions': [cons.to_dict() for cons in consumptions],
            'total_amount': total_amount,
            'generated_at': datetime.now().isoformat()
        }

    def generate_global_invoice(self) -> dict:
        all_consumptions = self.get_all_consumptions()
        customers = {}
        
        for consumption in all_consumptions:
            if consumption.customer_id not in customers:
                customers[consumption.customer_id] = {
                    'customer': consumption.customer.to_dict(),
                    'consumptions': [],
                    'total_amount': 0
                }
            
            customers[consumption.customer_id]['consumptions'].append(consumption.to_dict())
            customers[consumption.customer_id]['total_amount'] += consumption.total_price

        return {
            'customers': list(customers.values()),
            'total_amount': sum(cust['total_amount'] for cust in customers.values()),
            'generated_at': datetime.now().isoformat()
        } 