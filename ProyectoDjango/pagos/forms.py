from django import forms
from django.utils import timezone

from .models import PagoCompra


class PagoCompraForm(forms.ModelForm):
    """Formulario para registrar/editar un abono sobre una compra a proveedor.

    Requiere que la vista pase `compra` (la Purchase sobre la que se abona)
    para poder validar el saldo disponible (incluyendo el caso de edición,
    donde el valor anterior del propio pago debe descontarse del saldo ya
    comprometido antes de comparar) y el rango de fechas permitido.
    """
    class Meta:
        model  = PagoCompra
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

    def __init__(self, *args, compra=None, **kwargs):
        self.compra = compra
        super().__init__(*args, **kwargs)
        if self.compra is not None:
            self.fields['fecha'].widget.attrs['min'] = self.compra.purchase_date.isoformat()
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
        if self.compra is not None and fecha < self.compra.purchase_date:
            raise forms.ValidationError(
                f'La fecha de pago no puede ser anterior a la fecha de la compra ({self.compra.purchase_date:%d/%m/%Y}).'
            )
        return fecha

    def clean(self):
        cleaned = super().clean()
        valor = cleaned.get('valor')
        if valor is None or self.compra is None:
            return cleaned

        saldo_disponible = self.compra.saldo
        if self.instance.pk:
            # Al editar, el valor anterior de este mismo pago ya está
            # descontado del saldo actual: hay que devolverlo antes de
            # comparar contra el nuevo valor propuesto.
            saldo_disponible += self.instance.valor

        if valor > saldo_disponible:
            self.add_error(
                'valor',
                f'El abono (${valor}) no puede ser mayor al saldo disponible (${saldo_disponible}).'
            )
        return cleaned
