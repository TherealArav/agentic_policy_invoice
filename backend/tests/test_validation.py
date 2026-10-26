import pytest
from schemas import InvoiceData, LineItem
from validators import validate_vendor_node


def get_base_mock():
    """Helper to generate a valid DEWA invoice dictionary."""
    return {
        "extracted_data": {
            "vendor_name": "DEWA",
            "vendor_trn": "100123456789012",
            "invoice_number": "INV-1001",
            "subtotal": 1000.00,
            "tax_amount": 50.00,
            "total_amount": 1050.00,
            "line_items": [
                {"description": "Water", "quantity": 1, "unit_price": 500.00, "total": 500.00},
                {"description": "Power", "quantity": 1, "unit_price": 500.00, "total": 500.00}
            ]
        }
    }

def test_perfect_invoice_passes():
    result = validate_vendor_node(get_base_mock())
    assert result["needs_review"] is False

def test_invalid_trn_flagged():
    mock = get_base_mock()
    mock["extracted_data"]["vendor_trn"] = "99912345" # Bad prefix and length
    result = validate_vendor_node(mock)
    assert result["needs_review"] is True
    assert "Invalid TRN format" in result["routing_message"]

def test_bad_math_flagged():
    mock = get_base_mock()
    # Change unit price so it doesn't match the subtotal
    mock["extracted_data"]["line_items"][0]["unit_price"] = 999.00
    result = validate_vendor_node(mock)
    assert result["needs_review"] is True
    assert "Math mismatch" in result["routing_message"]

def test_bad_vat_flagged():
    mock = get_base_mock()
    # 5% of 1000 is 50, let's charge 100
    mock["extracted_data"]["tax_amount"] = 100.00
    result = validate_vendor_node(mock)
    assert result["needs_review"] is True
    assert "VAT mismatch" in result["routing_message"]