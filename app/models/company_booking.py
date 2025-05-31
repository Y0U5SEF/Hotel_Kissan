from datetime import datetime
from typing import List, Dict, Optional
from decimal import Decimal

class CompanyBooking:
    def __init__(
        self,
        company_id: str,
        company_name: str,
        contact_person: str,
        contact_email: str,
        contact_phone: str,
        billing_address: str,
        tax_id: Optional[str] = None,
        payment_terms: str = "Net 30",
        special_instructions: str = "",
        created_at: str = None
    ):
        self.company_id = company_id
        self.company_name = company_name
        self.contact_person = contact_person
        self.contact_email = contact_email
        self.contact_phone = contact_phone
        self.billing_address = billing_address
        self.tax_id = tax_id
        self.payment_terms = payment_terms
        self.special_instructions = special_instructions
        self.created_at = created_at or datetime.now().strftime('%Y-%m-%d %H:%M')
        self.guest_bookings: List[Dict] = []  # List of individual guest bookings
        self.total_amount: Decimal = Decimal('0')
        self.paid_amount: Decimal = Decimal('0')
        self.status: str = "Pending"  # Pending, Confirmed, Checked In, Checked Out, Cancelled

    def add_guest_booking(self, guest_booking: Dict):
        """Add a guest booking to the company booking"""
        self.guest_bookings.append(guest_booking)
        self._update_total_amount()

    def remove_guest_booking(self, guest_booking_id: str):
        """Remove a guest booking from the company booking"""
        self.guest_bookings = [b for b in self.guest_bookings if b['booking_id'] != guest_booking_id]
        self._update_total_amount()

    def _update_total_amount(self):
        """Update the total amount based on all guest bookings"""
        self.total_amount = sum(Decimal(str(b.get('total_amount', 0))) for b in self.guest_bookings)

    def update_payment(self, amount: Decimal):
        """Update the paid amount"""
        self.paid_amount += amount

    def get_balance_due(self) -> Decimal:
        """Get the remaining balance"""
        return self.total_amount - self.paid_amount

    def to_dict(self) -> Dict:
        """Convert the company booking to a dictionary"""
        return {
            'company_id': self.company_id,
            'company_name': self.company_name,
            'contact_person': self.contact_person,
            'contact_email': self.contact_email,
            'contact_phone': self.contact_phone,
            'billing_address': self.billing_address,
            'tax_id': self.tax_id,
            'payment_terms': self.payment_terms,
            'special_instructions': self.special_instructions,
            'created_at': self.created_at,
            'guest_bookings': self.guest_bookings,
            'total_amount': str(self.total_amount),
            'paid_amount': str(self.paid_amount),
            'status': self.status
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'CompanyBooking':
        """Create a CompanyBooking instance from a dictionary"""
        booking = cls(
            company_id=data['company_id'],
            company_name=data['company_name'],
            contact_person=data['contact_person'],
            contact_email=data['contact_email'],
            contact_phone=data['contact_phone'],
            billing_address=data['billing_address'],
            tax_id=data.get('tax_id'),
            payment_terms=data.get('payment_terms', 'Net 30'),
            special_instructions=data.get('special_instructions', ''),
            created_at=data.get('created_at')
        )
        booking.guest_bookings = data.get('guest_bookings', [])
        booking.total_amount = Decimal(str(data.get('total_amount', '0')))
        booking.paid_amount = Decimal(str(data.get('paid_amount', '0')))
        booking.status = data.get('status', 'Pending')
        return booking 