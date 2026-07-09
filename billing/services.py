from django.db import transaction
from django.db.models import F

from inventory.models import StockMovement
from shared.money import round_money


def recalc_invoice(invoice):
    """Recalcula subtotal/IVA/total de una factura a partir de sus líneas."""
    details          = list(invoice.details.all())
    invoice.subtotal = round_money(sum(d.subtotal   for d in details))
    invoice.tax      = round_money(sum(d.tax_amount for d in details))
    invoice.total    = round_money(invoice.subtotal + invoice.tax)
    invoice.save()


def check_stock(invoice):
    """Devuelve la lista de errores de stock insuficiente (vacía si hay stock para todo)."""
    details = list(invoice.details.select_related('product').all())
    return [
        f'{d.product.name}: disponible {d.product.stock}, requerido {d.quantity}'
        for d in details if d.product.stock < d.quantity
    ]


def emit_invoice(invoice, user, tipo_pago=None):
    """Emite una factura en Borrador: descuenta stock y registra StockMovement.

    Usado tanto por billing.views.invoice_confirm (emisión manual por el
    Vendedor, que elige Contado/Crédito) como por el checkout de la tienda
    (store.views, siempre Contado porque se paga online al instante), para
    no duplicar la lógica de descuento de stock y auditoría.

    Si tipo_pago es CONTADO la factura queda saldada de inmediato (saldo=0,
    estado_cobro=PAGADA). Si es CREDITO, queda con saldo pendiente por
    cobrar a través del módulo creditoventa.
    """
    from .models import Invoice, Product

    if tipo_pago is None:
        tipo_pago = Invoice.CONTADO

    details = list(invoice.details.select_related('product').all())
    with transaction.atomic():
        for detail in details:
            Product.objects.filter(pk=detail.product_id).update(
                stock=F('stock') - detail.quantity
            )
        StockMovement.objects.bulk_create([
            StockMovement(
                product_id=detail.product_id,
                quantity=-detail.quantity,
                movement_type=StockMovement.VENTA,
                user=user,
                invoice=invoice,
            )
            for detail in details
        ])
        invoice.estado    = Invoice.EMITIDA
        invoice.tipo_pago = tipo_pago
        if tipo_pago == Invoice.CONTADO:
            invoice.saldo        = 0
            invoice.estado_cobro = Invoice.PAGADA
        else:
            invoice.saldo        = invoice.total
            invoice.estado_cobro = Invoice.PAGADA if invoice.total <= 0 else Invoice.PENDIENTE
        invoice.save()
