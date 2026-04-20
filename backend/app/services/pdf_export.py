from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.units import cm
import io

def generate_tax_report_pdf(user, transactions, tax_data, audit_data, tds_data, health_data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=20, textColor=colors.HexColor('#1a1a2e'), spaceAfter=6)
    story.append(Paragraph("TaxFlow AI — Tax Summary Report", title_style))
    story.append(Paragraph(f"FY 2025-26 | Generated for {user.get('name', 'User')} | ITR Form: {user.get('itr_form', 'ITR-3')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("1. Income Summary", styles['Heading2']))
    income_data = [
        ['Metric', 'Amount (INR)'],
        ['Total Income', f"Rs {tax_data.get('total_income', 0):,.0f}"],
        ['Total Business Expenses', f"Rs {tax_data.get('total_expenses', 0):,.0f}"],
        ['80C Deductions', f"Rs {tax_data.get('deduction_80c', 0):,.0f}"],
        ['80D Deductions', f"Rs {tax_data.get('deduction_80d', 0):,.0f}"],
    ]
    t = Table(income_data, colWidths=[10*cm, 6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f7fafc'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("2. Tax Optimization — ITR-3 vs ITR-4", styles['Heading2']))
    itr3 = tax_data.get('itr3', {})
    itr4 = tax_data.get('itr4', {})
    tax_opt_data = [
        ['', 'ITR-4 (Presumptive)', 'ITR-3 (Actual)'],
        ['Method', itr4.get('method',''), itr3.get('method','')],
        ['Taxable Income', f"Rs {itr4.get('taxable_income',0):,.0f}", f"Rs {itr3.get('taxable_income',0):,.0f}"],
        ['Tax Amount', f"Rs {itr4.get('tax',0):,.0f}", f"Rs {itr3.get('tax',0):,.0f}"],
        ['Recommendation', '', tax_data.get('recommendation','')],
    ]
    t2 = Table(tax_opt_data, colWidths=[5*cm, 6*cm, 5*cm])
    t2.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 10),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f7fafc'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 6),
    ]))
    story.append(t2)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("3. Audit Risk Report", styles['Heading2']))
    zone = audit_data.get('zone', 'green').upper()
    score = audit_data.get('score', 0)
    story.append(Paragraph(f"Audit Risk Score: {score}/100 — Zone: {zone}", styles['Normal']))
    story.append(Spacer(1, 0.3*cm))
    flagged = audit_data.get('flagged_items', [])
    if flagged:
        story.append(Paragraph("Flagged Items:", styles['Heading3']))
        for item in flagged:
            story.append(Paragraph(f"• {item}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("4. Financial Health Score", styles['Heading2']))
    story.append(Paragraph(f"Score: {health_data.get('score', 0)}/100 — {health_data.get('zone','').upper()}", styles['Normal']))
    story.append(Paragraph(f"Tip: {health_data.get('tip', '')}", styles['Normal']))
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("5. Transaction Summary", styles['Heading2']))
    txn_data = [['Date', 'Narration', 'Amount (Rs)', 'Category', 'Deductible']]
    for t in transactions[:20]:
        txn_data.append([
            str(t.get('date','')),
            str(t.get('narration',''))[:35],
            f"{t.get('amount',0):,.0f}",
            str(t.get('category','')),
            'Yes' if t.get('deductible') else 'No'
        ])
    t3 = Table(txn_data, colWidths=[2.5*cm, 6*cm, 2.5*cm, 3*cm, 2*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2d3748')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#f7fafc'), colors.white]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('PADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t3)

    doc.build(story)
    buffer.seek(0)
    return buffer
