import re

def validate_vendor_node(state):
    """Validates the extracted dictionary against UAE ERP and VAT rules."""

    data = state.get("extracted_data", {})
    vendor = data.get("vendor_name", "")
    
    if not vendor:
        return {"vendor_verified": False, "needs_review": True, "routing_message": "Extraction failed."}

    messages = []
    needs_review = False
    
    # ERP Vendor Allowlist
    approved_vendors = ["dewa", "etisalat", "emirates post", "careem logistics"] # In future, data will be extracted from approved vendor's database
    if not any(approved in vendor.lower() for approved in approved_vendors):
        needs_review = True
        messages.append(f"Unregistered vendor '{vendor}'")

    # UAE TRN Format Check (15 digits, starts with 100)
    trn = data.get("vendor_trn", "")
    if not re.match(r"^100\d{12}$", str(trn)):
        needs_review = True
        messages.append(f"Invalid TRN format '{trn}'")

    # Line-Item Math Check
    subtotal = data.get("subtotal", 0.0)
    calculated_subtotal = sum(
        item.get("quantity", 0) * item.get("unit_price", 0) 
        for item in data.get("line_items", [])
    )
    if abs(subtotal - calculated_subtotal) > 0.05:
        needs_review = True
        messages.append(f"Math mismatch (Items sum: {calculated_subtotal}, Subtotal: {subtotal})")

    # UAE 5% VAT Check
    tax_amount = data.get("tax_amount", 0.0)
    expected_tax = subtotal * 0.05
    if abs(tax_amount - expected_tax) > 0.05:
        needs_review = True
        messages.append(f"VAT mismatch (Expected 5%: {expected_tax}, Got: {tax_amount})")

    # Routing Output
    if needs_review:
        return {
            "vendor_verified": False,
            "needs_review": True,
            "routing_message": "Flagged: " + " | ".join(messages)
        }
    
    return {
        "vendor_verified": True,
        "needs_review": False,
        "routing_message": f"Auto-Approved: '{vendor}' passed all ERP, TRN, and VAT checks."
    }