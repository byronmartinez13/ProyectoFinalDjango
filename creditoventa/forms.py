from decimal import Decimal

from django import forms
from django.utils import timezone

from .models import CobroFactura


class CobroFacturaForm(forms.ModelForm):
    """Formulario para registrar/editar un abono sobre una factura.

    Requiere que la vista pase `factura` (la Invoice sobre la que se abona)
    para poder validar el saldo disponible, incluyendo el caso de edición
    (donde el valor anterior del propio cobro debe descontarse del saldo
    ya comprometido antes de comparar).
    """
    class Meta:
        model  = CobroFactura
        fields = ['fecha', 'valor', 'observacion']
        labels = {
            'fecha':       'Fecha de pago',
            'valor':       'Valor del abono',
            'observacion': 'Observación',
        }
        widgets = {
            'fecha':       forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'valor':       forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0.01'}),
            'observacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2,
                                                  'placeholder': 'Referencia de pago, número de transferencia, etc. (opcional)'}),
        }

    def __init__(self, *args, factura=None, **kwargs):
        self.factura = factura
        super().__init__(*args, **kwargs)
        if self.factura is not None:
            self.fields['fecha'].widget.attrs['min'] = self.factura.invoice_date.date().isoformat()
            self.fields['fecha'].widget.attrs['max'] = timezone.localdate().isoformat()

    def clean_valor(self):
        valor = self.cleaned_data['valor']
        if valor <= 0:
            raise forms.ValidationError('El valor del abono debe ser mayor a cero.')
        return valor

    def clean_fecha(self):
        fecha = self.cleaned_data['fecha']
        hoy = timezone.localdate()
        if fecha > hoy:
            raise forms.ValidationError('La fecha de pago no puede ser una fecha futura.')
        if self.factura is not None:
            fecha_factura = self.factura.invoice_date.date()
            if fecha < fecha_factura:
                raise forms.ValidationError(
                    f'La fecha de pago no puede ser anterior a la fecha de emisión de la factura ({fecha_factura:%d/%m/%Y}).'
                )
        return fecha

    def clean(self):
        cleaned = super().clean()
        valor = cleaned.get('valor')
        if valor is None or self.factura is None:
            return cleaned

        saldo_disponible = self.factura.saldo
        if self.instance.pk:
            # Al editar, el valor anterior de este mismo cobro ya está
            # descontado del saldo actual: hay que devolverlo antes de
            # comparar contra el nuevo valor propuesto.
            saldo_disponible += self.instance.valor

        if valor > saldo_disponible:
            self.add_error(
                'valor',
                f'El abono (${valor}) no puede ser mayor al saldo disponible (${saldo_disponible}).'
            )
        return cleaned
