from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models, transaction

from billing.models import Invoice
from shared.money import round_money


class CobroFactura(models.Model):
    """Abono registrado sobre una factura de venta a crédito (Invoice)."""
    factura     = models.ForeignKey(
                      Invoice, on_delete=models.PROTECT, related_name='cobros',
                      verbose_name='Factura')
    fecha       = models.DateField(verbose_name='Fecha de pago')
    valor       = models.DecimalField(
                      max_digits=10, decimal_places=2,
                      validators=[MinValueValidator(Decimal('0.01'))],
                      verbose_name='Valor abonado')
    observacion = models.TextField(blank=True, verbose_name='Observación')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Cobro de Factura'
        verbose_name_plural  = 'Cobros de Facturas'
        ordering             = ['-fecha', '-id']

    def __str__(self):
        return f'Abono ${self.valor} → Factura #{self.factura_id}'


def recalcular_saldo(factura):
    """Recalcula saldo y estado_cobro de una factura a partir de sus cobros.

    Se recalcula siempre desde cero (SUM de cobros) en vez de sumar/restar
    incrementalmente, para que el saldo nunca quede desincronizado sin
    importar si el cobro se creó, editó o eliminó.
    """
    total_cobrado = factura.cobros.aggregate(t=models.Sum('valor'))['t'] or Decimal('0')
    factura.saldo = round_money(factura.total - total_cobrado)
    factura.estado_cobro = Invoice.PAGADA if factura.saldo <= 0 else Invoice.PENDIENTE
    factura.save(update_fields=['saldo', 'estado_cobro'])
    return factura


@transaction.atomic
def registrar_cobro(factura_id, fecha, valor, observacion=''):
    """Crea un CobroFactura y recalcula el saldo/estado de la factura, de forma atómica."""
    factura = Invoice.objects.select_for_update().get(pk=factura_id)
    cobro = CobroFactura.objects.create(
        factura=factura, fecha=fecha, valor=valor, observacion=observacion,
    )
    recalcular_saldo(factura)
    return cobro


@transaction.atomic
def actualizar_cobro(cobro, fecha, valor, observacion=''):
    """Actualiza un CobroFactura existente y recalcula el saldo/estado de su factura."""
    factura = Invoice.objects.select_for_update().get(pk=cobro.factura_id)
    cobro.fecha = fecha
    cobro.valor = valor
    cobro.observacion = observacion
    cobro.save()
    recalcular_saldo(factura)
    return cobro


@transaction.atomic
def eliminar_cobro(cobro):
    """Elimina un CobroFactura y recalcula el saldo/estado de su factura."""
    factura = Invoice.objects.select_for_update().get(pk=cobro.factura_id)
    cobro.delete()
    recalcular_saldo(factura)
