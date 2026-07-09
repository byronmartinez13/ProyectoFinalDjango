from django import forms
from django.forms import inlineformset_factory
from .models import Purchase, PurchaseDetail, SupplierCreditNote


class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['supplier', 'document_number']
        widgets = {
            'supplier': forms.Select(attrs={'class': 'form-select'}),
            'document_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. FAC-001',
                'autocomplete': 'off',
            }),
        }
        labels = {
            'supplier': 'Proveedor',
            'document_number': 'N° Documento',
        }
        error_messages = {
            'supplier': {'required': 'Seleccione un proveedor.'},
            'document_number': {
                'required': 'El número de documento es obligatorio.',
                'unique': 'Ya existe una compra con ese documento para este proveedor.',
            },
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.is_bound:
            for name in self.fields:
                if self.errors.get(name):
                    w = self.fields[name].widget
                    cls = w.attrs.get('class', '')
                    if 'is-invalid' not in cls:
                        w.attrs['class'] = (cls + ' is-invalid').strip()


class PurchaseDetailForm(forms.ModelForm):
    class Meta:
        model = PurchaseDetail
        fields = ['product', 'quantity', 'unit_cost']
        widgets = {
            'product': forms.Select(attrs={'class': 'form-select pd-product'}),
            'quantity': forms.NumberInput(attrs={
                'class': 'form-control pd-qty',
                'min': '1',
                'placeholder': '1',
            }),
            'unit_cost': forms.NumberInput(attrs={
                'class': 'form-control pd-cost',
                'step': '0.01',
                'min': '0.01',
                'placeholder': '0.00',
            }),
        }
        labels = {
            'product': 'Producto',
            'quantity': 'Cantidad',
            'unit_cost': 'Costo Unit.',
        }


_PURCHASE_DETAIL_COMMON = dict(
    form=PurchaseDetailForm,
    min_num=1, validate_min=True, can_delete=True,
)

PurchaseDetailFormSet = inlineformset_factory(
    Purchase, PurchaseDetail, extra=1, **_PURCHASE_DETAIL_COMMON
)

PurchaseDetailEditFormSet = inlineformset_factory(
    Purchase, PurchaseDetail, extra=0, **_PURCHASE_DETAIL_COMMON
)


class SupplierCreditNoteForm(forms.ModelForm):
    class Meta:
        model  = SupplierCreditNote
        fields = ['tipo', 'amount', 'reason']
        labels = {
            'tipo':   'Tipo de Nota',
            'amount': 'Monto',
            'reason': 'Motivo',
        }
        widgets = {
            'tipo':   forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={
                          'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'reason': forms.Textarea(attrs={
                          'class': 'form-control', 'rows': 3,
                          'placeholder': 'Describa el motivo de la devolución o descuento…'}),
        }
