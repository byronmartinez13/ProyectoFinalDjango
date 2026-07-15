from decimal import Decimal

from django.db import models

from billing.models import Customer, Product
from shared.money import round_money


class Cart(models.Model):
    """Carrito de compras de un Cliente. Uno por cliente."""
    customer   = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Carrito de {self.customer}'

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def subtotal(self):
        items = self.items.select_related('product').all()
        return round_money(sum((item.subtotal for item in items), Decimal('0')))

    @property
    def tax(self):
        items = self.items.select_related('product').all()
        return round_money(sum((item.tax_amount for item in items), Decimal('0')))

    @property
    def total(self):
        return round_money(self.subtotal + self.tax)


class CartItem(models.Model):
    """Línea del carrito: un producto y su cantidad."""
    cart     = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product  = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ('cart', 'product')

    def __str__(self):
        return f'{self.product.name} x {self.quantity}'

    @property
    def subtotal(self):
        return self.product.unit_price * self.quantity

    @property
    def tax_amount(self):
        return self.subtotal * self.product.tax_rate
