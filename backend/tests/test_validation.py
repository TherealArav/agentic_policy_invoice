import pytest
from main import validate_vendor_node, InvoiceData, LineItem

def test_approved_uae_vendor_passes():
    """Approved ERP vendors (e.g., DEWA) should set needs_review to False."""
    mock_state = {
        "file_path": "dummy.pdf",
        "markdown_content": "# DEWA Invoice",
        "extracted_data": dict(
            vendor_name="DEWA",
            invoice_number="INV-1001",
            total_amount=1500.00,
            line_items=[
                LineItem(description="Water & Electricity", quantity=1, unit_price=1500.00, total=1500.00)
            ]
        ),
        "needs_review": None
    }

    result = validate_vendor_node(mock_state)
    assert result["needs_review"] is False

def test_unregistered_vendor_flagged_for_review():
    """Unregistered vendors (e.g., Apex Gulf Consulting) must trigger human review."""
    mock_state = {
        "file_path": "dummy.pdf",
        "markdown_content": "# Apex Invoice",
        "extracted_data": dict(
            vendor_name="Apex Gulf Consulting FZ-LLC",
            invoice_number="INV-2026-8841",
            total_amount=21105.00,
            line_items=[
                LineItem(description="Security Audit", quantity=1, unit_price=21105.00, total=21105.00)
            ]
        ),
        "needs_review": False
    }

    result = validate_vendor_node(mock_state)
    assert result["needs_review"] is True

def test_missing_extraction_fails_closed():
    """Zero-trust check: If extracted_data is None/missing, system must default to needs_review=True."""
    mock_state = {
        "file_path": "dummy.pdf",
        "markdown_content": "",
        "extracted_data": None,
        "needs_review": False
    }

    result = validate_vendor_node(mock_state)
    assert result["needs_review"] is True