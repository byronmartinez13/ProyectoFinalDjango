from django.conf import settings
from django.db import models


class StockMovement(models.Model):
    VENTA             = 'VENTA'
    DEVOLUCION_VENTA  = 'DEV_VENTA'
    COMPRA            = 'COMPRA'
    DEVOLUCION_COMPRA = 'DEV_COMPRA'
    ENTRADA_MANUAL    = 'ENT_MANUAL'
    SALIDA_MANUAL     = 'SAL_MANUAL'

    MOVEMENT_CHOICES = [
        (VENTA,             'Venta (Factura)'),
        (DEVOLUCION_VENTA,  'Devolución de Venta'),
        (COMPRA,            'Compra'),
        (DEVOLUCION_COMPRA, 'Devolución de Compra'),
        (ENTRADA_MANUAL,    'Entrada Manual'),
        (SALIDA_MANUAL,     'Salida Manual'),
    ]

    product       = models.ForeignKey(
                        'billing.Product', on_delete=models.PROTECT,
                        related_name='movements', verbose_name='Producto')
    quantity      = models.IntegerField(verbose_name='Cantidad')  # + entrada / - salida
    movement_type = models.CharField(
                        max_length=20, choices=MOVEMENT_CHOICES, verbose_name='Tipo')
    date          = models.DateTimeField(auto_now_add=True, verbose_name='Fecha')
    user          = models.ForeignKey(
                        settings.AUTH_USER_MODEL, null=True, blank=True,
                        on_delete=models.SET_NULL, verbose_name='Usuario')
    invoice       = models.ForeignKey(
                        'billing.Invoice', null=True, blank=True,
                        on_delete=models.SET_NULL,
                        related_name='stock_movements', verbose_name='Factura')
    purchase      = models.ForeignKey(
                        'purchasing.Purchase', null=True, blank=True,
                        on_delete=models.SET_NULL,
                        related_name='stock_movements', verbose_name='Compra')
    notes         = models.TextField(blank=True, verbose_name='Notas')

    class Meta:
        ordering = ['-date']
        verbose_name        = 'Movimiento de Stock'
        verbose_name_plural = 'Movimientos de Stock'

    def __str__(self):
        sign = '+' if self.quantity > 0 else ''
        return f'{self.get_movement_type_display()} — {self.product.name} ({sign}{self.quantity})'
