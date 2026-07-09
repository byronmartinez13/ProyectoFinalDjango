from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group
from django.forms import inlineformset_factory
from .models import Brand, Invoice, InvoiceDetail, CreditNote, Customer, Supplier


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class':'form-control'}))
    first_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}))
    last_name = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class':'form-control'}))
    role = forms.ModelChoiceField(
        queryset=Group.objects.all().order_by('name'),
        required=False,
        label='Rol',
        empty_label='-- Selecciona un rol --',
    )

    class Meta:
        model = User
        fields = ['username','first_name','last_name','email','password1','password2','role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields: self.fields[f].widget.attrs['class'] = 'form-control'
        # El rol solo es obligatorio si el administrador ya configuró roles
        # en el sistema (python manage.py setup_roles). Antes de eso, el
        # registro sigue funcionando sin pedir un rol.
        self.fields['role'].required = self.fields['role'].queryset.exists()

    def save(self, commit=True):
        user = super().save(commit)
        if commit:
            role = self.cleaned_data.get('role')
            if role:
                user.groups.add(role)
        return user

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name', 'description', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control','rows':3}),
            'is_active': forms.CheckboxInput(attrs={'class':'form-check-input'}),
        }

class InvoiceForm(forms.ModelForm):
    """Formulario para cabecera de factura."""
    class Meta:
        model = Invoice
        fields = ['customer']
        labels = {'customer': 'Cliente'}
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-select'}),
        }


_DETAIL_WIDGETS = {
    'product':      forms.Select(attrs={'class': 'form-select id-product'}),
    'quantity':     forms.NumberInput(attrs={'class': 'form-control id-qty', 'min': 1}),
    'unit_price':   forms.NumberInput(attrs={
                        'class': 'form-control id-price price-readonly',
                        'step': '0.01', 'min': '0.01',
                        'readonly': 'readonly',
                        'title': 'Precio unitario (se completa automáticamente al elegir el producto)',
                        'placeholder': '0.00',
                    }),
    'discount_pct': forms.NumberInput(attrs={
                        'class': 'form-control id-discount',
                        'step': '0.01', 'min': '0', 'max': '100',
                        'placeholder': '0',
                    }),
}

_DETAIL_COMMON = dict(
    fields=['product', 'quantity', 'unit_price', 'discount_pct'],
    min_num=1, validate_min=True, can_delete=True,
    widgets=_DETAIL_WIDGETS,
)

# extra=1 para nueva factura (da una fila vacía inicial al usuario)
InvoiceDetailFormSet = inlineformset_factory(
    Invoice, InvoiceDetail, extra=1, **_DETAIL_COMMON
)

# extra=0 para editar borrador existente (solo muestra las líneas ya guardadas)
InvoiceDetailEditFormSet = inlineformset_factory(
    Invoice, InvoiceDetail, extra=0, **_DETAIL_COMMON
)


class CustomerQuickForm(forms.ModelForm):
    class Meta:
        model  = Customer
        fields = ['dni', 'first_name', 'last_name']
        labels = {'dni': 'DNI / RUC', 'first_name': 'Nombres', 'last_name': 'Apellidos'}
        widgets = {
            'dni':        forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 0912345678', 'maxlength': '13'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name':  forms.TextInput(attrs={'class': 'form-control'}),
        }


class SupplierQuickForm(forms.ModelForm):
    class Meta:
        model  = Supplier
        fields = ['name']
        labels = {'name': 'Nombre de la empresa'}
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Distribuidora XYZ S.A.'}),
        }


class CreditNoteForm(forms.ModelForm):
    """Formulario para crear una Nota de Crédito sobre una factura emitida."""
    class Meta:
        model  = CreditNote
        fields = ['tipo', 'amount', 'reason']
        labels = {
            'tipo':   'Tipo de Nota',
            'amount': 'Monto',
            'reason': 'Motivo',
        }
        widgets = {
            'tipo':   forms.Select(attrs={'class': 'form-select'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 3,
                                            'placeholder': 'Describa el motivo de la devolución o descuento…'}),
        }
