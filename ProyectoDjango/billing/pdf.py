"""Generación del PDF de factura (ReportLab).

Extraído de billing.views.invoice_pdf para poder reutilizar exactamente el
mismo layout tanto en la descarga manual (botón "PDF" en el detalle de
factura) como en el envío automático de facturación electrónica
(shared.emails.send_invoice_email), sin duplicar el código.
"""
from io import BytesIO


def build_invoice_pdf(invoice):
    """Genera el PDF de una factura y devuelve los bytes del documento."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT

    buf = BytesIO()
    W   = 170 * mm

    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    BLUE  = colors.HexColor('#0d6efd')
    LIGHT = colors.HexColor('#f8f9fa')
    GRID  = colors.HexColor('#dee2e6')
    MUTED = colors.HexColor('#6c757d')
    ESTADO_C = {
        0: colors.HexColor('#6c757d'),
        1: colors.HexColor('#198754'),
        2: colors.HexColor('#dc3545'),
    }

    def P(text, **kw):
        kw.setdefault('fontName', 'Helvetica')
        kw.setdefault('fontSize', 9)
        kw.setdefault('leading', 13)
        return Paragraph(str(text), ParagraphStyle('_', **kw))

    elts = []

    # ─ Encabezado ─
    elts.append(Table([
        [P('TecnoStock S.A.', fontName='Helvetica-Bold', fontSize=16, textColor=colors.white, leading=20),
         P(f'FACTURA #{invoice.id}', fontName='Helvetica-Bold', fontSize=20, textColor=colors.white, alignment=TA_RIGHT, leading=24)],
        [P('Sistema de Gestión Comercial', fontSize=9, textColor=colors.HexColor('#cce0ff'), leading=12),
         P(invoice.invoice_date.strftime('%d/%m/%Y'), fontSize=9, textColor=colors.HexColor('#cce0ff'), alignment=TA_RIGHT, leading=12)],
    ], colWidths=[W * 0.55, W * 0.45],
    style=TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BLUE),
        ('TOPPADDING', (0, 0), (-1, -1), 5 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('LEFTPADDING', (0, 0), (0, -1), 5 * mm),
        ('RIGHTPADDING', (-1, 0), (-1, -1), 5 * mm),
    ])))

    ec = ESTADO_C.get(invoice.estado, MUTED)
    elts.append(Table(
        [[invoice.get_estado_display()]],
        colWidths=[W],
        style=TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), ec),
            ('TEXTCOLOR',  (0, 0), (-1, -1), colors.white),
            ('FONTNAME',   (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE',   (0, 0), (-1, -1), 8),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING', (0, 0), (-1, -1), 5 * mm),
        ])
    ))
    elts.append(Spacer(1, 5 * mm))

    # ─ Info cliente ─
    c = invoice.customer
    info_rows = [
        ['CLIENTE', 'FECHA DE EMISIÓN'],
        [c.full_name, invoice.invoice_date.strftime('%d/%m/%Y %H:%M')],
        [f'DNI/RUC: {c.dni}', f'N° Factura: #{invoice.id}'],
    ]
    if getattr(c, 'email', None): info_rows.append([f'Email: {c.email}', ''])
    if getattr(c, 'phone', None): info_rows.append([f'Tel: {c.phone}', ''])

    elts.append(Table(info_rows, colWidths=[W * 0.6, W * 0.4],
        style=TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), LIGHT),
            ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, 0), 7),
            ('TEXTCOLOR',     (0, 0), (-1, 0), MUTED),
            ('FONTNAME',      (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 1), (-1, 1), 10),
            ('FONTSIZE',      (0, 2), (-1, -1), 8),
            ('BOX',           (0, 0), (-1, -1), 0.5, GRID),
            ('INNERGRID',     (0, 0), (-1, -1), 0.3, GRID),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING',   (0, 0), (-1, -1), 4 * mm),
            ('RIGHTPADDING',  (0, 0), (-1, -1), 4 * mm),
        ])))
    elts.append(Spacer(1, 5 * mm))

    # ─ Tabla de ítems ─
    elts.append(P('DETALLE DE PRODUCTOS', fontName='Helvetica-Bold', textColor=MUTED))
    elts.append(Spacer(1, 2 * mm))

    item_rows = [['Producto', 'Cant.', 'P. Unit.', 'Dto.%', 'Base', 'IVA']]
    for d in invoice.details.all():
        item_rows.append([
            d.product.name,
            str(d.quantity),
            f'${d.unit_price}',
            f'{d.discount_pct}%',
            f'${d.subtotal}',
            f'${d.tax_amount}',
        ])

    item_ts = [
        ('BACKGROUND',    (0, 0), (-1, 0), BLUE),
        ('TEXTCOLOR',     (0, 0), (-1, 0), colors.white),
        ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('ALIGN',         (1, 0), (1, -1), 'CENTER'),
        ('ALIGN',         (2, 0), (-1, -1), 'RIGHT'),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('BOX',           (0, 0), (-1, -1), 0.5, GRID),
        ('INNERGRID',     (0, 0), (-1, -1), 0.3, GRID),
        ('LEFTPADDING',   (0, 0), (-1, -1), 3 * mm),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 3 * mm),
    ]
    for i in range(2, len(item_rows), 2):
        item_ts.append(('BACKGROUND', (0, i), (-1, i), LIGHT))

    elts.append(Table(item_rows,
        colWidths=[W * 0.33, W * 0.09, W * 0.14, W * 0.10, W * 0.17, W * 0.17],
        style=TableStyle(item_ts)))
    elts.append(Spacer(1, 3 * mm))

    # ─ Totales ─
    elts.append(Table([
        ['', 'Subtotal:', f'${invoice.subtotal}'],
        ['', 'IVA:',      f'${invoice.tax}'],
        ['', 'TOTAL:',    f'${invoice.total}'],
    ], colWidths=[W * 0.55, W * 0.27, W * 0.18],
    style=TableStyle([
        ('FONTNAME',      (1, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE',      (1, 2), (-1, 2), 11),
        ('TEXTCOLOR',     (-1, 2), (-1, 2), BLUE),
        ('FONTSIZE',      (0, 0), (-1, 1), 9),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN',         (2, 0), (2, -1), 'RIGHT'),
        ('BOX',           (1, 0), (-1, -1), 0.5, GRID),
        ('INNERGRID',     (1, 0), (-1, -1), 0.3, GRID),
        ('BACKGROUND',    (1, 2), (-1, 2), LIGHT),
        ('LINEABOVE',     (1, 2), (-1, 2), 1, BLUE),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (2, 0), (2, -1), 4 * mm),
        ('LEFTPADDING',   (1, 0), (1, -1), 4 * mm),
    ])))

    # ─ Notas de crédito ─
    credit_notes = list(invoice.credit_notes.all())
    if credit_notes:
        elts.append(Spacer(1, 5 * mm))
        elts.append(P('NOTAS DE CRÉDITO', fontName='Helvetica-Bold',
                       textColor=colors.HexColor('#856404')))
        elts.append(Spacer(1, 2 * mm))
        nc_rows = [['NC', 'Fecha', 'Tipo', 'Monto', 'Motivo']]
        for nc in credit_notes:
            nc_rows.append([
                f'NC-{nc.id}',
                nc.date.strftime('%d/%m/%Y'),
                nc.get_tipo_display(),
                f'${nc.amount}',
                nc.reason[:80],
            ])
        elts.append(Table(nc_rows,
            colWidths=[W * 0.08, W * 0.12, W * 0.12, W * 0.12, W * 0.56],
            style=TableStyle([
                ('BACKGROUND',    (0, 0), (-1, 0), colors.HexColor('#ffc107')),
                ('FONTNAME',      (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE',      (0, 0), (-1, -1), 8),
                ('TOPPADDING',    (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('BOX',           (0, 0), (-1, -1), 0.5, GRID),
                ('INNERGRID',     (0, 0), (-1, -1), 0.3, GRID),
                ('LEFTPADDING',   (0, 0), (-1, -1), 3 * mm),
                ('RIGHTPADDING',  (0, 0), (-1, -1), 3 * mm),
                ('ALIGN',         (3, 0), (3, -1), 'RIGHT'),
            ])))

    doc.build(elts)
    buf.seek(0)
    return buf.getvalue()
