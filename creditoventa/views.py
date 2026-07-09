from datetime import date

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from billing.models import Invoice
from shared.decorators import roles_required

from .forms import CobroFacturaForm
from .models import CobroFactura, actualizar_cobro, eliminar_cobro, registrar_cobro

ROLES_COBROS = ('Administrador', 'Vendedor')


@roles_required(*ROLES_COBROS)
def factura_list(request):
    """Lista las facturas emitidas a crédito, filtrables por estado de cobro.

    Por defecto muestra solo las Pendientes, pero permite ver también las
    Pagadas (?estado=PAGADA) o todas (?estado=) — útil para cuando un
    cliente llega a pagar y su factura ya figura como cancelada.
    """
    q = request.GET.get('q', '').strip()
    estado_cobro = request.GET.get('estado', Invoice.PENDIENTE)

    facturas = (
        Invoice.objects
        .filter(estado=Invoice.EMITIDA, tipo_pago=Invoice.CREDITO)
        .select_related('customer')
        .order_by('invoice_date')
    )
    if estado_cobro in (Invoice.PENDIENTE, Invoice.PAGADA):
        facturas = facturas.filter(estado_cobro=estado_cobro)
    if q:
        facturas = facturas.filter(
            Q(customer__first_name__icontains=q) |
            Q(customer__last_name__icontains=q) |
            Q(customer__dni__icontains=q) |
            Q(id__icontains=q)
        )
    return render(request, 'creditoventa/factura_list.html', {
        'items': facturas,
        'q': q,
        'estado_cobro': estado_cobro,
    })


@roles_required(*ROLES_COBROS)
def cobro_create(request, factura_pk):
    """Registra un abono sobre una factura pendiente de pago."""
    factura = get_object_or_404(Invoice, pk=factura_pk)

    if factura.estado == Invoice.ANULADA:
        messages.error(request, 'No se puede registrar un cobro sobre una factura anulada.')
        return redirect('creditoventa:factura_list')
    if factura.estado != Invoice.EMITIDA:
        messages.error(request, 'Solo se pueden registrar cobros sobre facturas emitidas.')
        return redirect('creditoventa:factura_list')
    if factura.saldo <= 0:
        messages.error(request, f'La Factura #{factura.id} ya está totalmente pagada.')
        return redirect('creditoventa:factura_list')

    if request.method == 'POST':
        form = CobroFacturaForm(request.POST, factura=factura)
        if form.is_valid():
            registrar_cobro(
                factura_id=factura.id,
                fecha=form.cleaned_data['fecha'],
                valor=form.cleaned_data['valor'],
                observacion=form.cleaned_data['observacion'],
            )
            messages.success(request, f'Abono registrado sobre la Factura #{factura.id}.')
            return redirect('creditoventa:historial_pagos', factura_pk=factura.id)
    else:
        form = CobroFacturaForm(initial={'fecha': date.today()}, factura=factura)

    return render(request, 'creditoventa/cobro_form.html', {
        'form': form, 'factura': factura, 'title': f'Registrar pago — Factura #{factura.id}',
    })


@roles_required(*ROLES_COBROS)
def historial_pagos(request, factura_pk):
    """Muestra el historial de abonos registrados sobre una factura."""
    factura = get_object_or_404(Invoice.objects.select_related('customer'), pk=factura_pk)
    cobros = factura.cobros.all()
    return render(request, 'creditoventa/historial_pagos.html', {
        'factura': factura, 'cobros': cobros,
    })


@roles_required(*ROLES_COBROS)
def cobro_update(request, pk):
    """Edita un abono ya registrado, recalculando el saldo de la factura."""
    cobro = get_object_or_404(CobroFactura.objects.select_related('factura'), pk=pk)
    factura = cobro.factura

    if request.method == 'POST':
        form = CobroFacturaForm(request.POST, instance=cobro, factura=factura)
        if form.is_valid():
            actualizar_cobro(
                cobro,
                fecha=form.cleaned_data['fecha'],
                valor=form.cleaned_data['valor'],
                observacion=form.cleaned_data['observacion'],
            )
            messages.success(request, f'Abono #{cobro.id} actualizado.')
            return redirect('creditoventa:historial_pagos', factura_pk=factura.id)
    else:
        form = CobroFacturaForm(instance=cobro, factura=factura)

    return render(request, 'creditoventa/cobro_form.html', {
        'form': form, 'factura': factura, 'cobro': cobro,
        'title': f'Editar pago #{cobro.id} — Factura #{factura.id}',
    })


@roles_required(*ROLES_COBROS)
def cobro_delete(request, pk):
    """Elimina un abono, solo si la factura no está totalmente pagada."""
    cobro = get_object_or_404(CobroFactura.objects.select_related('factura'), pk=pk)
    factura = cobro.factura

    if factura.estado_cobro == Invoice.PAGADA:
        messages.error(
            request,
            f'No se puede eliminar el abono: la Factura #{factura.id} ya está pagada completamente.'
        )
        return redirect('creditoventa:historial_pagos', factura_pk=factura.id)

    if request.method == 'POST':
        factura_id = factura.id
        eliminar_cobro(cobro)
        messages.success(request, f'Abono #{cobro.id} eliminado.')
        return redirect('creditoventa:historial_pagos', factura_pk=factura_id)

    return render(request, 'creditoventa/cobro_confirm_delete.html', {
        'cobro': cobro, 'factura': factura,
    })
