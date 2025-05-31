import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Optional
from jinja2 import Environment, FileSystemLoader
from fpdf import FPDF
import logging
from app.models.company_booking import CompanyBooking

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CompanyBookingService:
    def __init__(self):
        self.template_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'resources', 'templates')
        self.env = Environment(loader=FileSystemLoader(self.template_dir))
        self.receipts_dir = os.path.join(os.getcwd(), "receipts")
        os.makedirs(self.receipts_dir, exist_ok=True)

    def generate_company_invoice(self, company_booking: CompanyBooking) -> str:
        """Generate a PDF invoice for a company booking"""
        try:
            # Calculate due date based on payment terms
            invoice_date = datetime.now()
            due_date = invoice_date + timedelta(days=30)  # Default to Net 30

            # Prepare template data
            template_data = {
                'invoice_number': f"INV-{company_booking.company_id}-{datetime.now().strftime('%Y%m%d')}",
                'invoice_date': invoice_date.strftime('%Y-%m-%d'),
                'due_date': due_date.strftime('%Y-%m-%d'),
                'company_name': company_booking.company_name,
                'contact_person': company_booking.contact_person,
                'contact_email': company_booking.contact_email,
                'contact_phone': company_booking.contact_phone,
                'billing_address': company_booking.billing_address,
                'tax_id': company_booking.tax_id,
                'payment_terms': company_booking.payment_terms,
                'special_instructions': company_booking.special_instructions,
                'guest_bookings': self._prepare_guest_bookings_data(company_booking.guest_bookings),
                'subtotal': f"{float(company_booking.total_amount):.2f}",
                'tax_amount': "0.00",  # Calculate based on your tax rules
                'total_amount': f"{float(company_booking.total_amount):.2f}",
                'amount_paid': f"{float(company_booking.paid_amount):.2f}",
                'balance_due': f"{float(company_booking.get_balance_due()):.2f}"
            }

            # Render HTML template
            template = self.env.get_template('company_invoice_template.html')
            html_content = template.render(**template_data)

            # Convert HTML to PDF
            pdf_path = os.path.join(self.receipts_dir, f"company_invoice_{company_booking.company_id}.pdf")
            self._html_to_pdf(html_content, pdf_path)

            return pdf_path

        except Exception as e:
            logger.error(f"Error generating company invoice: {str(e)}")
            raise

    def _prepare_guest_bookings_data(self, guest_bookings: List[Dict]) -> List[Dict]:
        """Prepare guest booking data for the invoice template"""
        prepared_bookings = []
        for booking in guest_bookings:
            prepared_booking = {
                'guest_name': f"{booking.get('guest_first_name', '')} {booking.get('guest_last_name', '')}",
                'room_number': booking.get('room_number', ''),
                'check_in': booking.get('arrival_date', ''),
                'check_out': booking.get('departure_date', ''),
                'nights': booking.get('nights', 0),
                'rate_per_night': f"{float(booking.get('rate_per_night', 0)):.2f}",
                'room_total': f"{float(booking.get('room_total', 0)):.2f}",
                'additional_charges': f"{float(booking.get('additional_charges', 0)):.2f}",
                'subtotal': f"{float(booking.get('total_amount', 0)):.2f}"
            }
            prepared_bookings.append(prepared_booking)
        return prepared_bookings

    def _html_to_pdf(self, html_content: str, output_path: str):
        """Convert HTML content to PDF using FPDF"""
        # This is a placeholder for HTML to PDF conversion
        # You might want to use a more robust solution like WeasyPrint or pdfkit
        # For now, we'll create a simple PDF with the essential information
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add basic information
        pdf.cell(200, 10, txt="Company Invoice", ln=True, align="C")
        pdf.cell(200, 10, txt=f"Date: {datetime.now().strftime('%Y-%m-%d')}", ln=True)
        
        # Add company information
        pdf.cell(200, 10, txt=f"Company: {html_content}", ln=True)
        
        # Save the PDF
        pdf.output(output_path)

    def calculate_tax(self, amount: Decimal, tax_rate: Decimal) -> Decimal:
        """Calculate tax amount based on the total and tax rate"""
        return amount * tax_rate

    def validate_company_booking(self, company_booking: CompanyBooking) -> bool:
        """Validate a company booking"""
        try:
            # Check required fields
            if not all([
                company_booking.company_name,
                company_booking.contact_person,
                company_booking.contact_email,
                company_booking.contact_phone,
                company_booking.billing_address
            ]):
                return False

            # Validate email format
            if '@' not in company_booking.contact_email:
                return False

            # Validate phone number (basic check)
            if not company_booking.contact_phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                return False

            # Check if there are any guest bookings
            if not company_booking.guest_bookings:
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating company booking: {str(e)}")
            return False 