from decimal import Decimal
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from shared.validators import validate_cedula_ec
from shared.money import round_money

# Create your models here.
class Brand(models.Model):
    """Marcas de productos."""
    name = models.CharField(max_length=100, unique=True, verbose_name='Nombre de Marca')
    description = models.TextField(blank=True, null=True, verbose_name='Descripción')
    is_active = models.BooleanField(default=True, verbose_name='Activo')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        ordering = ['name']
    def __str__(self): return self.name

class ProductGroup(models.Model):
    """Grupos/categorías de productos."""
    name = models.CharField(max_length=100, unique=True, verbose_name='Group Name')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Product Group'
        verbose_name_plural = 'Product Groups'
        ordering = ['name']
    def __str__(self): return self.name

class Supplier(models.Model):
    """Proveedores. M2M con Product."""
    name = models.CharField(max_length=200, verbose_name='Company Name')
    contact_name = models.CharField(max_length=200, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='suppliers/', blank=True, null=True, verbose_name='Logo')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Supplier'
        verbose_name_plural = 'Suppliers'
        ordering = ['name']
    def __str__(self): return self.name

    @property
    def photo_url(self):
        if self.photo and self.photo.name:
            return self.photo.url
        return '/media/suppliers/Supplier%20generico.avif'

class Product(models.Model):
    """Productos. FK a Brand/Group, M2M a Supplier."""
    name = models.CharField(max_length=200, verbose_name='Product Name')
    description = models.TextField(blank=True, null=True)
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name='products')
    group = models.ForeignKey(ProductGroup, on_delete=models.PROTECT, related_name='products')
    suppliers = models.ManyToManyField(Supplier, related_name='products', blank=True)
    photo      = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name='Foto')
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate   = models.DecimalField(
                     max_digits=5, decimal_places=4, default=Decimal('0.15'),
                     verbose_name='Tasa IVA',
                     validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('1'))],
                 )
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['name']
    def __str__(self): return f'{self.name} ({self.brand.name})'

    @property
    def balance(self):
        return self.unit_price * self.stock

    @property
    def photo_url(self):
        if self.photo and self.photo.name:
            return self.photo.url
        return '/media/products/Producto%20generico.jpg'

class Customer(models.Model):
    """Clientes. OneToOne con CustomerProfile."""
    user       = models.OneToOneField(
                     settings.AUTH_USER_MODEL, null=True, blank=True,
                     on_delete=models.SET_NULL, related_name='customer_account',
                     verbose_name='Cuenta de usuario')
    dni        = models.CharField(max_length=13, unique=True, verbose_name='DNI/RUC', validators=[validate_cedula_ec])
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    email      = models.EmailField(blank=True, null=True)
    phone      = models.CharField(max_length=20, blank=True, null=True)
    address    = models.TextField(blank=True, null=True)
    photo      = models.ImageField(upload_to='customer/', blank=True, null=True, verbose_name='Foto')
    is_active  = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['last_name', 'first_name']
    def __str__(self): return f'{self.last_name}, {self.first_name}'

    @property
    def full_name(self): return f'{self.first_name} {self.last_name}'

    @property
    def photo_url(self):
        if self.photo and self.photo.name:
            return self.photo.url
        return '/media/customer/customer%20generico.png'

class CustomerProfile(models.Model):
    """Perfil extendido. OneToOne con Customer."""
    TAXPAYER = [('final','Final Consumer'),('ruc','RUC'),('rise','RISE')]
    PAYMENT = [('cash','Cash'),('credit_15','15 days'),('credit_30','30 days'),('credit_60','60 days')]
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE, related_name='profile')
    taxpayer_type = models.CharField(max_length=10, choices=TAXPAYER, default='final')
    payment_terms = models.CharField(max_length=15, choices=PAYMENT, default='cash')
    credit_limit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    class Meta: verbose_name = 'Customer Profile'
    def __str__(self): return f'Profile: {self.customer}'

class Invoice(models.Model):
    """Cabecera de factura con ciclo de vida: Borrador → Emitida → Anulada."""
    BORRADOR = 0
    EMITIDA  = 1
    ANULADA  = 2
    ESTADO_CHOICES = [
        (BORRADOR, 'Borrador'),
        (EMITIDA,  'Emitida'),
        (ANULADA,  'Anulada'),
    ]

    # Estado de cobro (cuentas por cobrar): independiente del ciclo de vida
    # del documento (estado) — una factura EMITIDA puede estar Pendiente o
    # Pagada según los abonos registrados en creditoventa.CobroFactura.
    PENDIENTE = 'PENDIENTE'
    PAGADA    = 'PAGADA'
    ESTADO_COBRO_CHOICES = [
        (PENDIENTE, 'Pendiente'),
        (PAGADA,    'Pagada'),
    ]

    # Forma de pago elegida al emitir: define si la factura queda saldada
    # de inmediato (Contado) o genera saldo por cobrar (Crédito).
    CONTADO = 'contado'
    CREDITO = 'credito'
    TIPO_PAGO_CHOICES = [
        (CONTADO, 'Contado'),
        (CREDITO, 'Crédito'),
    ]

    customer     = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    invoice_date = models.DateTimeField(auto_now_add=True)
    subtotal     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax          = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total        = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado       = models.PositiveSmallIntegerField(
                       choices=ESTADO_CHOICES, default=BORRADOR, verbose_name='Estado')
    is_active    = models.BooleanField(default=True)
    PAYMENT_CHOICES = [('card', 'Tarjeta'), ('paypal', 'PayPal')]
    payment_method  = models.CharField(
                          max_length=10, choices=PAYMENT_CHOICES, null=True, blank=True,
                          verbose_name='Método de pago')
    paypal_order_id = models.CharField(max_length=64, null=True, blank=True)
    saldo        = models.DecimalField(
                       max_digits=12, decimal_places=2, default=0,
                       verbose_name='Saldo pendiente de cobro')
    estado_cobro = models.CharField(
                       max_length=10, choices=ESTADO_COBRO_CHOICES,
                       default=PENDIENTE, verbose_name='Estado de cobro')
    tipo_pago    = models.CharField(
                       max_length=10, choices=TIPO_PAGO_CHOICES,
                       default=CREDITO, verbose_name='Tipo de pago')

    class Meta:
        ordering = ['-invoice_date']

    def __str__(self):
        return f'Factura #{self.id} - {self.customer}'

    @property
    def can_confirm(self):     return self.estado == self.BORRADOR
    @property
    def can_edit(self):        return self.estado == self.BORRADOR
    @property
    def can_delete(self):      return self.estado == self.BORRADOR
    @property
    def can_cancel(self):      return self.estado == self.EMITIDA
    @property
    def can_substitute(self):  return self.estado == self.EMITIDA
    @property
    def can_credit_note(self): return self.estado == self.EMITIDA

    @property
    def estado_badge_class(self):
        return {
            self.BORRADOR: 'bg-secondary',
            self.EMITIDA:  'bg-success',
            self.ANULADA:  'bg-danger',
        }.get(self.estado, 'bg-secondary')

    @property
    def estado_cobro_badge_class(self):
        return 'bg-success' if self.estado_cobro == self.PAGADA else 'bg-warning text-dark'

    @property
    def pendiente_de_pago(self):
        """True si la factura fue emitida, no está anulada y aún tiene saldo por cobrar."""
        return self.estado == self.EMITIDA and self.saldo > 0

    @property
    def cobrado(self):
        return self.total - self.saldo

    @property
    def tipo_pago_badge_class(self):
        return 'bg-info text-dark' if self.tipo_pago == self.CONTADO else 'bg-primary'


class InvoiceDetail(models.Model):
    """Líneas de factura."""
    invoice      = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='details')
    product      = models.ForeignKey(Product, on_delete=models.PROTECT, related_name='invoice_details')
    quantity     = models.IntegerField(default=1)
    unit_price   = models.DecimalField(max_digits=12, decimal_places=2)
    discount_pct = models.DecimalField(
        max_digits=5, decimal_places=2, default=0,
        verbose_name='Descuento (%)',
        validators=[MinValueValidator(Decimal('0')), MaxValueValidator(Decimal('100'))],
    )
    subtotal     = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_amount   = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='IVA')

    def __str__(self): return f'{self.product.name} x {self.quantity}'

    def save(self, *args, **kwargs):
        base = Decimal(self.quantity) * self.unit_price
        self.subtotal   = round_money(base * (1 - self.discount_pct / Decimal('100')))
        self.tax_amount = round_money(self.subtotal * self.product.tax_rate)
        super().save(*args, **kwargs)


class CreditNote(models.Model):
    """Nota de crédito vinculada a una factura emitida (devolución parcial o total)."""
    TIPO_TOTAL   = 'total'
    TIPO_PARCIAL = 'parcial'
    TIPO_CHOICES = [
        (TIPO_TOTAL,   'Devolución Total'),
        (TIPO_PARCIAL, 'Devolución Parcial'),
    ]

    invoice   = models.ForeignKey(
                    Invoice, on_delete=models.PROTECT,
                    related_name='credit_notes', verbose_name='Factura')
    date      = models.DateField(auto_now_add=True, verbose_name='Fecha')
    tipo      = models.CharField(
                    max_length=10, choices=TIPO_CHOICES,
                    default=TIPO_TOTAL, verbose_name='Tipo')
    amount    = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='Monto')
    reason    = models.CharField(max_length=300, verbose_name='Motivo')
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name        = 'Nota de Crédito'
        verbose_name_plural = 'Notas de Crédito'
        ordering            = ['-date', '-id']

    def __str__(self):
        return f'NC-{self.id} → Factura #{self.invoice_id}'
