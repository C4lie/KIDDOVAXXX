import io
import qrcode
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

def generate_vaccine_card_pdf(child):
    """
    Generates a PDF bytes buffer containing the digital vaccination card for the child.
    """
    buffer = io.BytesIO()
    
    # Setup document
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )
    
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CardTitle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#2A3E5C'),
        alignment=1, # Centered
        spaceAfter=15
    )
    
    section_style = ParagraphStyle(
        'CardSection',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#2A3E5C'),
        spaceBefore=12,
        spaceAfter=6
    )
    
    normal_style = ParagraphStyle(
        'CardText',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=10,
        textColor=colors.HexColor('#333333'),
        spaceAfter=4
    )
    
    table_header_style = ParagraphStyle(
        'TableHeader',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10,
        textColor=colors.white
    )
    
    table_cell_style = ParagraphStyle(
        'TableCell',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=9,
        textColor=colors.HexColor('#333333')
    )
    
    # 1. Header Section
    story.append(Paragraph("KIDDOVAX DIGITAL VACCINATION CARD", title_style))
    story.append(Spacer(1, 10))
    
    # 2. QR Code Generation
    qr_data = f"Child Name: {child.childname}\nParent Name: {child.patient.name}\nAge: {child.age}\nBlood Group: {child.blood_group or 'N/A'}"
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")
    
    # Save QR to a bytes stream and load into ReportLab Image
    qr_buffer = io.BytesIO()
    qr_img.save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_reportlab_img = Image(qr_buffer, width=1.2*inch, height=1.2*inch)
    
    # 3. Child & Parent Info Table
    info_data = [
        [
            Paragraph(f"<b>Child Name:</b> {child.childname}", normal_style),
            Paragraph(f"<b>Parent/Guardian:</b> {child.patient.name}", normal_style)
        ],
        [
            Paragraph(f"<b>Date of Birth:</b> {child.dob.strftime('%d %B, %Y')}", normal_style),
            Paragraph(f"<b>Contact No:</b> {child.patient.contactNo}", normal_style)
        ],
        [
            Paragraph(f"<b>Gender:</b> {child.gender}", normal_style),
            Paragraph(f"<b>Blood Group:</b> {child.blood_group or 'N/A'}", normal_style)
        ]
    ]
    
    info_table = Table(info_data, colWidths=[240, 240])
    info_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    
    # Layout Header: Info table on left, QR code on right
    layout_data = [
        [info_table, qr_reportlab_img]
    ]
    layout_table = Table(layout_data, colWidths=[400, 120])
    layout_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (1,0), (1,0), 'RIGHT'),
    ]))
    
    story.append(layout_table)
    story.append(Spacer(1, 15))
    
    # 4. Completed Vaccinations Table
    story.append(Paragraph("Completed Vaccinations", section_style))
    records = child.vaccination_records.all().select_related('vaccine', 'appointment__hospitalid')
    
    comp_headers = [Paragraph("Vaccine Name", table_header_style), Paragraph("Hospital", table_header_style), Paragraph("Date Administered", table_header_style)]
    comp_rows = [comp_headers]
    
    if records.exists():
        for r in records:
            comp_rows.append([
                Paragraph(r.vaccine.vaccineName, table_cell_style),
                Paragraph(r.appointment.hospitalid.title, table_cell_style),
                Paragraph(r.appointment.aptdate.strftime('%d %b, %Y') if r.appointment.aptdate else 'N/A', table_cell_style)
            ])
    else:
        comp_rows.append([Paragraph("No completed vaccinations recorded yet.", table_cell_style), "", ""])
        
    comp_table = Table(comp_rows, colWidths=[200, 200, 120])
    comp_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#2A3E5C')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDDDD')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('SPAN', (0,1), (2,1)) if not records.exists() else ('ALIGN', (0,0), (-1,-1), 'LEFT')
    ]))
    story.append(comp_table)
    story.append(Spacer(1, 15))
    
    # 5. Upcoming / Scheduled Vaccinations Table
    story.append(Paragraph("Upcoming / Pending Vaccinations", section_style))
    upcoming_appointments = child.appointments.filter(active__in=[0, 1]).select_related('vaccineid', 'hospitalid').order_by('aptdate')
    
    up_headers = [Paragraph("Vaccine Name", table_header_style), Paragraph("Hospital", table_header_style), Paragraph("Scheduled Date", table_header_style)]
    up_rows = [up_headers]
    
    if upcoming_appointments.exists():
        for apt in upcoming_appointments:
            up_rows.append([
                Paragraph(apt.vaccineid.vaccineName, table_cell_style),
                Paragraph(apt.hospitalid.title, table_cell_style),
                Paragraph(apt.aptdate.strftime('%d %b, %Y') if apt.aptdate else 'N/A', table_cell_style)
            ])
    else:
        up_rows.append([Paragraph("No upcoming appointments scheduled.", table_cell_style), "", ""])
        
    up_table = Table(up_rows, colWidths=[200, 200, 120])
    up_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#4A607A')),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#DDDDDD')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#F9F9F9')]),
        ('TOPPADDING', (0,0), (-1,-1), 6),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('SPAN', (0,1), (2,1)) if not upcoming_appointments.exists() else ('ALIGN', (0,0), (-1,-1), 'LEFT')
    ]))
    story.append(up_table)
    
    # Build Document
    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
