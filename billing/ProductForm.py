from django import forms
from decimal import Decimal
from .models import Product


class ProductForm(forms.ModelForm):
    """
    Formulario centralizado para crear y editar Productos.
    Centraliza widgets, validaciones, estilos, labels y mensajes de error.
    No duplicar configuración en las vistas.
    """

    class Meta:
        model = Product
        fields = [
            'name', 'brand', 'group',
            'unit_price', 'tax_rate', 'stock',
            'suppliers', 'is_active', 'description',
            'photo',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej. Camiseta Sport XL',
                'autocomplete': 'off',
            }),
            'brand': forms.Select(attrs={
                'class': 'form-select',
            }),
            'group': forms.Select(attrs={
                'class': 'form-select',
            }),
            'unit_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
            }),
            'tax_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.0001',
                'min': '0',
                'max': '1',
                'placeholder': '0.1500',
            }),
            'stock': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'placeholder': '0',
            }),
            'suppliers': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '4',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción opcional del producto…',
            }),
            'photo': forms.FileInput(attrs={
                'class': 'd-none',
                'accept': 'image/*',
            }),
        }
        labels = {
            'name':        'Nombre del Producto',
            'brand':       'Marca',
            'group':       'Grupo / Categoría',
            'unit_price':  'Precio Unitario',
            'tax_rate':    'Tasa IVA',
            'stock':       'Stock',
            'suppliers':   'Proveedores',
            'is_active':   'Activo',
            'description': 'Descripción',
            'photo':       'Foto del Producto',
        }
        help_texts = {
            'unit_price': 'Solo se permiten valores mayores que $0.00.',
            'tax_rate':   'Valor entre 0 y 1. Ej: 0.15 = 15%. El sistema calcula IVA por línea.',
            'stock':      'Unidades disponibles en inventario.',
            'suppliers':  'Mantén Ctrl (Cmd en Mac) para seleccionar varios.',
            'is_active':  'Desactiva para ocultar el producto de las consultas.',
        }
        error_messages = {
            'name': {
                'required':   'El nombre del producto es obligatorio.',
                'max_length': 'El nombre no puede superar 200 caracteres.',
            },
            'brand':      {'required': 'Selecciona una marca.'},
            'group':      {'required': 'Selecciona un grupo o categoría.'},
            'unit_price': {
                'required': 'El precio es obligatorio.',
                'invalid':  'Ingresa un valor numérico válido (ej. 12.50).',
            },
        }

    # ── Marcar is-invalid en campos con errores (formulario enviado) ───────
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound:
            for name in self.fields:
                if self.errors.get(name):
                    w = self.fields[name].widget
                    cls = w.attrs.get('class', '')
                    if 'is-invalid' not in cls:
                        w.attrs['class'] = (cls + ' is-invalid').strip()

    # ── Validación servidor: precio estrictamente mayor que cero ──────────
    def clean_unit_price(self):
        price = self.cleaned_data.get('unit_price')
        if price is not None and price <= Decimal('0'):
            raise forms.ValidationError('El precio unitario debe ser mayor que cero.')
        return price
