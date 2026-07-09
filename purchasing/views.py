import json
from decimal import Decimal
from io import BytesIO
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.contrib import messages
from django.db import transaction
from django.db.models import F
from .models import Purchase, PurchaseDetail, SupplierCreditNote
from .forms import (PurchaseForm, PurchaseDetailFormSet,
                    PurchaseDetailEditFormSet, SupplierCreditNoteForm)
from billing.models import Supplier, Product
from shared.money import round_money
from shared.mixins import SearchExportMixin, GroupRequiredMixin
from shared.decorators import roles_required
from inventory.models import StockMovement

_PURCHASING_ROLES = ('Administrador', 'Analista de Compras')


# ── Helpers ──────────────────────────────────────────────────────────────

def _recalc_purchase(purchase):
    details = list(purchase.details.all())
    purchase.subtotal = round_money(sum(d.subtotal   for d in details))
    purchase.tax      = round_money(sum(d.tax_amount for d in details))
    purchase.total    = round_money(purchase.subtotal + purchase.tax)
    purchase.save()


def _product_data_json():
    data = {
        str(p['id']): {
            'price':    str(p['unit_price']),
            'stock':    p['stock'],
            'tax_rate': str(p['tax_rate']),
        }
        for p in Product.objects.filter(is_active=True)
                                .values('id', 'unit_price', 'stock', 'tax_rate')
    }
    return json.dumps(data)


# ── Listado ───────────────────────────────────────────────────────────────

class PurchaseListView(LoginRequiredMixin, GroupRequiredMixin, SearchExportMixin, ListView):
    group_required      = list(_PURCHASING_ROLES)
    model               = Purchase
    queryset            = Purchase.objects.select_related('supplier').all()
    template_name       = 'purchasing/purchase_list.html'
    context_object_name = 'items'
    export_filename     = 'compras'
    paginate_by         = 10
    export_fields       = [
        ('#',            'id'),
        ('Proveedor',    lambda p: p.supplier.name),
        ('N° Documento', 'document_number'),
        ('Fecha',        lambda p: str(p.purchase_date)),
        ('Estado',       lambda p: p.get_estado_display()),
        ('Subtotal',     'subtotal'),
        ('IVA',          'tax'),
        ('Total',        'total'),
    ]
    search_fields = [
        {'param': 'q',         'fields': ['document_number__icontains', 'supplier__name__icontains']},
        {'param': 'supplier',  'field':  'supplier_id',       'type': 'number'},
        {'param': 'estado',    'field':  'estado',            'type': 'number'},
        {'param': 'date_from', 'field':  'purchase_date__gte','type': 'date'},
        {'param': 'date_to',   'field':  'purchase_date__lte','type': 'date'},
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['suppliers'] = Supplier.objects.filter(is_active=True)
        return ctx


# ── Crear borrador ────────────────────────────────────────────────────────

@roles_required(*_PURCHASING_ROLES)
def purchase_create(request):
    if request.method == 'POST':
        form    = PurchaseForm(request.POST)
        formset = PurchaseDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            purchase        = form.save(commit=False)
            purchase.estado = Purchase.BORRADOR
            purchase.save()
            formset.instance = purchase
            formset.save()
            _recalc_purchase(purchase)
            messages.info(request,
                f'Borrador #{purchase.id} guardado. Revísalo y pulsa "Confirmar" para actualizar el stock.')
            return redirect('purchasing:purchase_detail', pk=purchase.pk)
    else:
        form    = PurchaseForm()
        formset = PurchaseDetailFormSet()
    return render(request, 'purchasing/purchase_form.html', {
        'form': form, 'formset': formset,
        'title': 'Nueva Compra',
        'product_data_json': _product_data_json(),
    })


# ── Editar borrador ───────────────────────────────────────────────────────

@roles_required(*_PURCHASING_ROLES)
def purchase_update(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if not purchase.can_edit:
        messages.error(request, 'Solo se puede editar una compra en estado Borrador.')
        return redirect('purchasing:purchase_detail', pk=pk)

    if request.method == 'POST':
        form    = PurchaseForm(request.POST, instance=purchase)
        formset = PurchaseDetailEditFormSet(request.POST, instance=purchase)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            _recalc_purchase(purchase)
            messages.success(request, f'Borrador #{purchase.id} actualizado.')
            return redirect('purchasing:purchase_detail', pk=purchase.pk)
    else:
        form    = PurchaseForm(instance=purchase)
        formset = PurchaseDetailEditFormSet(instance=purchase)

    return render(request, 'purchasing/purchase_form.html', {
        'form': form, 'formset': formset,
        'purchase': purchase,
        'title': f'Editar Borrador #{purchase.id}',
        'product_data_json': _product_data_json(),
    })


# ── Confirmar compra (actualiza stock) ───────────────────────────────────

@roles_required(*_PURCHASING_ROLES)
def purchase_confirm(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if not purchase.can_confirm:
        messages.error(request, 'Solo se puede confirmar una compra en estado Borrador.')
        return redirect('purchasing:purchase_detail', pk=pk)

    if request.method == 'POST':
        tipo_pago = request.POST.get('tipo_pago')
        if tipo_pago not in (Purchase.CONTADO, Purchase.CREDITO):
            messages.error(request, 'Selecciona la forma de pago: Contado o Crédito.')
            return redirect('purchasing:purchase_confirm', pk=pk)

        details = list(purchase.details.select_related('product').all())
        with transaction.atomic():
            for detail in details:
                Product.objects.filter(pk=detail.product_id).update(
                    stock=F('stock') + detail.quantity
                )
            StockMovement.objects.bulk_create([
                StockMovement(
                    product_id=detail.product_id,
                    quantity=detail.quantity,
                    movement_type=StockMovement.COMPRA,
                    user=request.user,
                    purchase=purchase,
                )
                for detail in details
            ])
            purchase.estado    = Purchase.CONFIRMADA
            purchase.tipo_pago = tipo_pago
            if tipo_pago == Purchase.CONTADO:
                purchase.saldo       = 0
                purchase.estado_pago = Purchase.PAGADA
            else:
                purchase.saldo       = purchase.total
                purchase.estado_pago = Purchase.PAGADA if purchase.total <= 0 else Purchase.PENDIENTE
            purchase.save()

        if tipo_pago == Purchase.CONTADO:
            messages.success(request, f'Compra #{purchase.id} confirmada y pagada al contado. Stock actualizado.')
        else:
            messages.success(request, f'Compra #{purchase.id} confirmada a crédito. Saldo pendiente: ${purchase.saldo}.')
        return redirect('purchasing:purchase_detail', pk=purchase.pk)

    return render(request, 'purchasing/purchase_confirm.html', {'purchase': purchase})


# ── Anular compra (revierte stock) ───────────────────────────────────────

@roles_required(*_PURCHASING_ROLES)
def purchase_cancel(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if not purchase.can_cancel:
        messages.error(request, 'Solo se puede anular una compra confirmada.')
        return redirect('purchasing:purchase_detail', pk=pk)

    if request.method == 'POST':
        details = list(purchase.details.select_related('product').all())
        with transaction.atomic():
            for detail in details:
                Product.objects.filter(pk=detail.product_id).update(
                    stock=F('stock') - detail.quantity
                )
            StockMovement.objects.bulk_create([
                StockMovement(
                    product_id=detail.product_id,
                    quantity=-detail.quantity,
                    movement_type=StockMovement.DEVOLUCION_COMPRA,
                    user=request.user,
                    purchase=purchase,
                )
                for detail in details
            ])
            purchase.estado    = Purchase.ANULADA
            purchase.is_active = False
            purchase.save()
        messages.success(request, f'Compra #{purchase.id} anulada. Stock revertido.')
        return redirect('purchasing:purchase_list')

    return render(request, 'purchasing/purchase_cancel.html', {'purchase': purchase})


# ── Nota de crédito a proveedor ───────────────────────────────────────────

@roles_required(*_PURCHASING_ROLES)
def supplier_credit_note_create(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if not purchase.can_credit_note:
        messages.error(request, 'Solo se pueden emitir notas de crédito sobre compras confirmadas.')
        return redirect('purchasing:purchase_detail', pk=pk)

    if request.method == 'POST':
        form = SupplierCreditNoteForm(request.POST)
        if form.is_valid():
            note          = form.save(commit=False)
            note.purchase = purchase
            note.save()
            messages.success(request,
                f'Nota de crédito NC-P{note.id} registrada sobre Compra #{purchase.id}.')
            return redirect('purchasing:purchase_detail', pk=purchase.pk)
    else:
        form = SupplierCreditNoteForm(initial={
            'amount': purchase.total,
            'tipo':   SupplierCreditNote.TIPO_TOTAL,
        })

    return render(request, 'purchasing/supplier_credit_note_form.html', {
        'form': form, 'purchase': purchase,
    })


# ── Detalle ───────────────────────────────────────────────────────────────

@roles_required(*_PURCHASING_ROLES)
def purchase_detail(request, pk):
    purchase = get_object_or_404(
        Purchase.objects.select_related('supplier')
                        .prefetch_related('details__product', 'credit_notes'),
        pk=pk
    )
    return render(request, 'purchasing/purchase_detail.html', {'purchase': purchase})


# ── PDF de compra ────────────────────────────────────────────────────────

@roles_required(*_PURCHASING_ROLES)
def purchase_pdf(request, pk):
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.enums import TA_RIGHT

    purchase = get_object_or_404(
        Purchase.objects.select_related('supplier')
                        .prefetch_related('details__product', 'credit_notes'),
        pk=pk,
    )
    buf = BytesIO()
    W   = 170 * mm

    doc = SimpleDocTemplate(buf, pagesize=A4,
                            leftMargin=20*mm, rightMargin=20*mm,
                            topMargin=15*mm, bottomMargin=15*mm)

    PURPLE = colors.HexColor('#6f42c1')
    LIGHT  = colors.HexColor('#f8f9fa')
    GRID   = colors.HexColor('#dee2e6')
    MUTED  = colors.HexColor('#6c757d')
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
         P(f'ORDEN DE COMPRA #{purchase.id}', fontName='Helvetica-Bold', fontSize=16, textColor=colors.white, alignment=TA_RIGHT, leading=20)],
        [P('Sistema de Gestión Comercial', fontSize=9, textColor=colors.HexColor('#dcceff'), leading=12),
         P(purchase.purchase_date.strftime('%d/%m/%Y'), fontSize=9, textColor=colors.HexColor('#dcceff'), alignment=TA_RIGHT, leading=12)],
    ], colWidths=[W * 0.55, W * 0.45],
    style=TableStyle([
        ('BACKGROUND',    (0, 0), (-1, -1), PURPLE),
        ('TOPPADDING',    (0, 0), (-1, -1), 5 * mm),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5 * mm),
        ('LEFTPADDING',   (0, 0), (0, -1),  5 * mm),
        ('RIGHTPADDING',  (-1, 0), (-1, -1), 5 * mm),
    ])))

    ec = ESTADO_C.get(purchase.estado, MUTED)
    elts.append(Table(
        [[purchase.get_estado_display()]],
        colWidths=[W],
        style=TableStyle([
            ('BACKGROUND',    (0, 0), (-1, -1), ec),
            ('TEXTCOLOR',     (0, 0), (-1, -1), colors.white),
            ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE',      (0, 0), (-1, -1), 8),
            ('TOPPADDING',    (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('LEFTPADDING',   (0, 0), (-1, -1), 5 * mm),
        ])
    ))
    elts.append(Spacer(1, 5 * mm))

    # ─ Info proveedor ─
    s = purchase.supplier
    info_rows = [
        ['PROVEEDOR', 'FECHA / DOCUMENTO'],
        [s.name, purchase.purchase_date.strftime('%d/%m/%Y')],
        ['', f'N° Doc: {purchase.document_number}'],
    ]
    if getattr(s, 'contact_name', None): info_rows.append([f'Contacto: {s.contact_name}', ''])
    if getattr(s, 'phone', None):        info_rows.append([f'Tel: {s.phone}', ''])

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

    item_rows = [['Producto', 'Cant.', 'C. Unit.', 'Base', 'IVA']]
    for d in purchase.details.all():
        item_rows.append([
            d.product.name,
            str(d.quantity),
            f'${d.unit_cost}',
            f'${d.subtotal}',
            f'${d.tax_amount}',
        ])

    item_ts = [
        ('BACKGROUND',    (0, 0), (-1, 0), PURPLE),
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
        colWidths=[W * 0.40, W * 0.11, W * 0.17, W * 0.17, W * 0.15],
        style=TableStyle(item_ts)))
    elts.append(Spacer(1, 3 * mm))

    # ─ Totales ─
    elts.append(Table([
        ['', 'Subtotal:', f'${purchase.subtotal}'],
        ['', 'IVA:',      f'${purchase.tax}'],
        ['', 'TOTAL:',    f'${purchase.total}'],
    ], colWidths=[W * 0.55, W * 0.27, W * 0.18],
    style=TableStyle([
        ('FONTNAME',      (1, 2), (-1, 2), 'Helvetica-Bold'),
        ('FONTSIZE',      (1, 2), (-1, 2), 11),
        ('TEXTCOLOR',     (-1, 2), (-1, 2), PURPLE),
        ('FONTSIZE',      (0, 0), (-1, 1), 9),
        ('ALIGN',         (1, 0), (1, -1), 'RIGHT'),
        ('ALIGN',         (2, 0), (2, -1), 'RIGHT'),
        ('BOX',           (1, 0), (-1, -1), 0.5, GRID),
        ('INNERGRID',     (1, 0), (-1, -1), 0.3, GRID),
        ('BACKGROUND',    (1, 2), (-1, 2), LIGHT),
        ('LINEABOVE',     (1, 2), (-1, 2), 1, PURPLE),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('RIGHTPADDING',  (2, 0), (2, -1), 4 * mm),
        ('LEFTPADDING',   (1, 0), (1, -1), 4 * mm),
    ])))

    # ─ Notas de crédito ─
    credit_notes = list(purchase.credit_notes.all())
    if credit_notes:
        elts.append(Spacer(1, 5 * mm))
        elts.append(P('NOTAS DE CRÉDITO A PROVEEDOR', fontName='Helvetica-Bold',
                       textColor=colors.HexColor('#856404')))
        elts.append(Spacer(1, 2 * mm))
        nc_rows = [['NC', 'Fecha', 'Tipo', 'Monto', 'Motivo']]
        for nc in credit_notes:
            nc_rows.append([
                f'NC-P{nc.id}',
                nc.date.strftime('%d/%m/%Y'),
                nc.get_tipo_display(),
                f'${nc.amount}',
                nc.reason[:80],
            ])
        elts.append(Table(nc_rows,
            colWidths=[W * 0.09, W * 0.12, W * 0.12, W * 0.12, W * 0.55],
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
    resp = HttpResponse(buf, content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="compra-{purchase.id}.pdf"'
    return resp


# ── Eliminar borrador ─────────────────────────────────────────────────────

@roles_required(*_PURCHASING_ROLES)
def purchase_delete(request, pk):
    purchase = get_object_or_404(Purchase, pk=pk)
    if not purchase.can_delete:
        messages.error(request,
            'Solo se puede eliminar una compra en estado Borrador. '
            'Para las confirmadas, usa "Anular".')
        return redirect('purchasing:purchase_detail', pk=pk)
    if request.method == 'POST':
        purchase_id = purchase.id
        purchase.delete()
        messages.success(request, f'Borrador #{purchase_id} eliminado.')
        return redirect('purchasing:purchase_list')
    return render(request, 'purchasing/purchase_confirm_delete.html', {'object': purchase})
