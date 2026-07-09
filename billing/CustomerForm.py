from django import forms
from .models import Customer


class CustomerForm(forms.ModelForm):
    """
    Formulario centralizado para crear y editar Clientes.
    Centraliza widgets, validaciones, estilos, labels y mensajes de error.
    No duplicar configuración en las vistas.
    """

    class Meta:
        model = Customer
        fields = ['dni', 'first_name', 'last_name', 'email', 'phone', 'address', 'is_active', 'photo']
        widgets = {
            'dni': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': 'Ej. 0912345678',
                'autocomplete': 'off',
                'maxlength': '13',
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombres',
                'autocomplete': 'off',
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Apellidos',
                'autocomplete': 'off',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.com',
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. 0991234567',
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Dirección opcional del cliente…',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'role': 'switch',
            }),
            'photo': forms.FileInput(attrs={
                'class': 'd-none',
                'accept': 'image/*',
            }),
        }
        labels = {
            'dni':        'DNI / RUC',
            'first_name': 'Nombres',
            'last_name':  'Apellidos',
            'email':      'Correo Electrónico',
            'phone':      'Teléfono',
            'address':    'Dirección',
            'is_active':  'Activo',
            'photo':      'Foto del Cliente',
        }
        help_texts = {
            'dni':       'Cédula de identidad (10 dígitos) o RUC (13 dígitos).',
            'is_active': 'Desactiva para ocultar el cliente de las consultas.',
        }
        error_messages = {
            'dni': {
                'required':   'El DNI/RUC es obligatorio.',
                'unique':     'Ya existe un cliente registrado con este DNI/RUC.',
                'max_length': 'El DNI/RUC no puede superar 13 caracteres.',
            },
            'first_name': {'required': 'El nombre es obligatorio.'},
            'last_name':  {'required': 'El apellido es obligatorio.'},
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
