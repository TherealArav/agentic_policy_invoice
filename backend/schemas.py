from pydantic import BaseModel, Field
from typing import List

# Add the nested LineItem schema
class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    total: float

# Define the JSON schema required
class InvoiceData(BaseModel):
    vendor_name: str
    vendor_trn: str = Field(description="The 15-digit Tax Registration Number starting with 100")
    invoice_number: str
    subtotal: float 
    tax_amount: float
    total_amount: float
    line_items: List[LineItem]