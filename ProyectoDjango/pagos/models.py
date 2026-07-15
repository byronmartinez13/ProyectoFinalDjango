from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models, transaction

from purchasing.models import Purchase
from shared.money import round_money


class PagoCompra(models.Model):
    """Abono registrado sobre una compra a crédito (Purchase)."""
    compra      = models.ForeignKey(
                      Purchase, on_delete=models.PROTECT, related_name='pagos',
                      verbose_name='Compra')
    fecha       = models.DateField(verbose_name='Fecha de pago')
    valor       = models.DecimalField(
                      max_digits=10, decimal_places=2,
                      validators=[MinValueValidator(Decimal('0.01'))],
                      verbose_name='Valor abonado')
    observacion = models.TextField(blank=True, verbose_name='Observación')
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name        = 'Pago de Compra'
        verbose_name_plural  = 'Pagos de Compras'
        ordering             = ['-fecha', '-id']

    def __str__(self):
        return f'Abono ${self.valor} → Compra #{self.compra_id}'


def recalcular_saldo(compra):
    """Recalcula saldo y estado_pago de una compra a partir de sus pagos.

    Se recalcula siempre desde cero (SUM de pagos) en vez de sumar/restar
    incrementalmente, para que el saldo nunca quede desincronizado sin
    importar si el pago se creó, editó o eliminó.
    """
    total_pagado = compra.pagos.aggregate(t=models.Sum('valor'))['t'] or Decimal('0')
    compra.saldo = round_money(compra.total - total_pagado)
    compra.estado_pago = Purchase.PAGADA if compra.saldo <= 0 else Purchase.PENDIENTE
    compra.save(update_fields=['saldo', 'estado_pago'])
    return compra


@transaction.atomic
def registrar_pago(compra_id, fecha, valor, observacion=''):
    """Crea un PagoCompra y recalcula el saldo/estado de la compra, de forma atómica."""
    compra = Purchase.objects.select_for_update().get(pk=compra_id)
    pago = PagoCompra.objects.create(
        compra=compra, fecha=fecha, valor=valor, observacion=observacion,
    )
    recalcular_saldo(compra)
    return pago


@transaction.atomic
def actualizar_pago(pago, fecha, valor, observacion=''):
    """Actualiza un PagoCompra existente y recalcula el saldo/estado de su compra."""
    compra = Purchase.objects.select_for_update().get(pk=pago.compra_id)
    pago.fecha = fecha
    pago.valor = valor
    pago.observacion = observacion
    pago.save()
    recalcular_saldo(compra)
    return pago


@transaction.atomic
def eliminar_pago(pago):
    """Elimina un PagoCompra y recalcula el saldo/estado de su compra."""
    compra = Purchase.objects.select_for_update().get(pk=pago.compra_id)
    pago.delete()
    recalcular_saldo(compra)
