from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User, Group

from billing.models import Customer

_CUSTOMER_WIDGETS = {
    'dni':     forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 0912345678', 'maxlength': '13'}),
    'phone':   forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. 0991234567'}),
    'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
}


class CustomerSignUpForm(UserCreationForm):
    """Registro público: crea el User (rol Cliente) y su Customer vinculado."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, label='Nombres', widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label='Apellidos', widget=forms.TextInput(attrs={'class': 'form-control'}))
    dni = forms.CharField(max_length=13, label='DNI / RUC', widget=_CUSTOMER_WIDGETS['dni'])
    phone = forms.CharField(max_length=20, label='Teléfono', required=False, widget=_CUSTOMER_WIDGETS['phone'])
    address = forms.CharField(label='Dirección', required=False, widget=_CUSTOMER_WIDGETS['address'])

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields:
            if 'class' not in self.fields[f].widget.attrs:
                self.fields[f].widget.attrs['class'] = 'form-control'

    def clean_dni(self):
        from shared.validators import validate_cedula_ec
        dni = self.cleaned_data['dni']
        validate_cedula_ec(dni)
        if Customer.objects.filter(dni=dni).exists():
            raise forms.ValidationError('Ya existe un cliente registrado con este DNI/RUC.')
        return dni

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            role, _ = Group.objects.get_or_create(name='Cliente')
            user.groups.add(role)
            Customer.objects.create(
                user=user,
                dni=self.cleaned_data['dni'],
                first_name=self.cleaned_data['first_name'],
                last_name=self.cleaned_data['last_name'],
                email=self.cleaned_data['email'],
                phone=self.cleaned_data.get('phone', ''),
                address=self.cleaned_data.get('address', ''),
            )
        return user


class CompleteProfileForm(forms.ModelForm):
    """Completa los datos de facturación de un Cliente creado por el Administrador
    (sin pasar por el registro público), para poder usar el carrito."""

    class Meta:
        model = Customer
        fields = ['dni', 'phone', 'address']
        widgets = _CUSTOMER_WIDGETS
        labels = {'dni': 'DNI / RUC', 'phone': 'Teléfono', 'address': 'Dirección'}
