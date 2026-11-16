import pytest
from schemas import InvoiceData, LineItem
from validators import validate_vendor_node


@pytest.fixture
def base_mock() -> dict:
    """Fixture generating a compliant DEWA invoice validated through Pydantic."""
    invoice = InvoiceData(
        vendor_name="DEWA (Dubai Electricity and Water Authority)",
        vendor_trn="100123456789012",
        invoice_number="INV-1001",
        subtotal=1000.00,
        tax_amount=50.00,
        total_amount=1050.00,
        line_items=[
            LineItem(description="Water", quantity=1, unit_price=500.00, total=500.00),
            LineItem(description="Power", quantity=1, unit_price=500.00, total=500.00),
        ],
    )
    return {"extracted_data": invoice.model_dump()}


def test_perfect_invoice_passes(base_mock):
    result = validate_vendor_node(base_mock)
    assert result["vendor_verified"] is True
    assert result["needs_review"] is False
    assert "Auto-Approved:" in result["routing_message"]


@pytest.mark.parametrize(
    "approved_vendor",
    [
        "DEWA",
        "Etisalat",
        "Emirates Post",
        "Careem Logistics",
        "Dewan Fraud LLC", 
        "NotEtisalat Ltd", 
        "dewa commercial"
    ],
)
def test_approved_vendor_allowlist_case_insensitive(base_mock, approved_vendor):
    base_mock["extracted_data"]["vendor_name"] = approved_vendor
    result = validate_vendor_node(base_mock)
    assert result["vendor_verified"] is True
    assert result["needs_review"] is False


def test_unregistered_vendor_flagged(base_mock):
    base_mock["extracted_data"]["vendor_name"] = "Apex Gulf Consulting FZ-LLC"
    result = validate_vendor_node(base_mock)
    assert result["vendor_verified"] is False
    assert result["needs_review"] is True
    assert "Unregistered vendor 'Apex Gulf Consulting FZ-LLC'" in result["routing_message"]


@pytest.mark.parametrize(
    "bad_trn",
    [
        "99912345",          # Wrong prefix and too short
        "200123456789012",   # 15 digits, but does not start with 100
        "10012345678901",    # 14 digits (one short)
        "1001234567890123",  # 16 digits (one extra)
        "10012345678901A",   # Contains non-numeric character
        "",                  # Empty TRN
    ],
)
def test_invalid_trn_flagged(base_mock, bad_trn):
    base_mock["extracted_data"]["vendor_trn"] = bad_trn
    result = validate_vendor_node(base_mock)
    assert result["vendor_verified"] is False
    assert result["needs_review"] is True
    assert f"Invalid TRN format '{bad_trn}'" in result["routing_message"]


def test_bad_math_flagged(base_mock):
    # Change unit price so items sum to 1499.00 while subtotal stays 1000.00
    base_mock["extracted_data"]["line_items"][0]["unit_price"] = 999.00
    result = validate_vendor_node(base_mock)
    assert result["vendor_verified"] is False
    assert result["needs_review"] is True
    assert "Math mismatch" in result["routing_message"]


def test_bad_vat_flagged(base_mock):
    # 5% of 1000.00 is 50.00; charging 100.00 (10%) must be flagged
    base_mock["extracted_data"]["tax_amount"] = 100.00
    result = validate_vendor_node(base_mock)
    assert result["vendor_verified"] is False
    assert result["needs_review"] is True
    assert "VAT mismatch" in result["routing_message"]


def test_rounding_tolerance_within_0_05_aed_passes(base_mock):
    # Minor Fils rounding differences <= 0.05 AED should not trigger false positives
    base_mock["extracted_data"]["subtotal"] = 1000.03
    base_mock["extracted_data"]["tax_amount"] = 50.03
    base_mock["extracted_data"]["total_amount"] = 1050.06
    result = validate_vendor_node(base_mock)
    assert result["vendor_verified"] is True
    assert result["needs_review"] is False


def test_multiple_violations_accumulate_all_reasons(base_mock):
    # Should report all 4 violations separated by pipes instead of failing early
    base_mock["extracted_data"]["vendor_name"] = "Unknown Corp"
    base_mock["extracted_data"]["vendor_trn"] = "99988877"
    base_mock["extracted_data"]["subtotal"] = 1500.00
    base_mock["extracted_data"]["tax_amount"] = 150.00

    result = validate_vendor_node(base_mock)
    assert result["vendor_verified"] is False
    assert result["needs_review"] is True
    assert "Unregistered vendor" in result["routing_message"]
    assert "Invalid TRN format" in result["routing_message"]
    assert "Math mismatch" in result["routing_message"]
    assert "VAT mismatch" in result["routing_message"]


@pytest.mark.parametrize(
    "empty_state",
    [
        {},
        {"extracted_data": {}},
        {"extracted_data": {"vendor_name": ""}},
    ],
)
def test_missing_or_empty_extraction_fails_safe(empty_state):
    result = validate_vendor_node(empty_state)
    assert result["vendor_verified"] is False
    assert result["needs_review"] is True
    assert result["routing_message"] == "Extraction failed."