from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
import datetime

def create_invoice(filename, vendor_name, items):
    # Initialize document
    pdf = SimpleDocTemplate(filename, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Header
    elements.append(Paragraph(f"<b>TAX INVOICE</b>", styles['Heading1']))
    
    # Vendor & Date Info
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    meta_info = (
        f"<b>Vendor:</b> {vendor_name}<br/>"
        f"<b>Date:</b> {date_str}<br/>"
        f"<b>Currency:</b> AED"
    )
    elements.append(Paragraph(meta_info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Build Table Rows
    table_data = [["Description", "Qty", "Unit Price (AED)", "Total (AED)"]]
    subtotal = 0.0
    
    for desc, qty, price in items:
        row_total = qty * price
        subtotal += row_total
        table_data.append([desc, str(qty), f"{price:,.2f}", f"{row_total:,.2f}"])
        
    # Calculate Standard UAE VAT (5%)
    tax = subtotal * 0.05
    grand_total = subtotal + tax
    
    # Append Totals
    table_data.append(["", "", "Subtotal:", f"{subtotal:,.2f}"])
    table_data.append(["", "", "VAT (5%):", f"{tax:,.2f}"])
    table_data.append(["", "", "Grand Total:", f"{grand_total:,.2f}"])
    
    # Apply Enterprise Styling
    t = Table(table_data, colWidths=[200, 50, 100, 100])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#2563eb")), # Tailwind blue-600
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 10),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (-2,-3), (-1,-1), colors.HexColor("#f3f4f6")),
        ('FONTNAME', (-2,-3), (-1,-1), 'Helvetica-Bold'),
    ]))
    
    elements.append(t)
    pdf.build(elements)
    print(f"Generated: {filename} -> ({vendor_name})")

if __name__ == "__main__":
    # 1. Valid Invoice: Matches the mock ERP database for automated approval
    create_invoice(
        "mock_valid_dewa.pdf", 
        "DEWA", 
        [
            ("Commercial Electricity Charges", 1, 1450.00), 
            ("Water Utility", 1, 320.00)
        ]
    )
    
    # 2. Invalid Invoice: Unregistered vendor to trigger human review routing
    create_invoice(
        "mock_invalid_apex.pdf", 
        "Apex Global Consulting LLC", 
        [
            ("Security Architecture Review", 1, 15000.00), 
            ("Penetration Testing", 2, 4500.00)
        ]
    )