from datetime import date

from django.contrib import messages
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from purchasing.models import Purchase
from shared.decorators import roles_required

from .forms import PagoCompraForm
from .models import PagoCompra, actualizar_pago, eliminar_pago, registrar_pago

ROLES_PAGOS = ('Administrador', 'Analista de Compras')


@roles_required(*ROLES_PAGOS)
def compra_list(request):
    """Lista las compras confirmadas a crédito, filtrables por estado de pago.

    Por defecto muestra solo las Pendientes, pero permite ver también las
    Pagadas (?estado=PAGADA) o todas (?estado=) — útil para cuando hay que
    verificar si una compra a un proveedor ya quedó saldada.
    """
    q = request.GET.get('q', '').strip()
    estado_pago = request.GET.get('estado', Purchase.PENDIENTE)

    compras = (
        Purchase.objects
        .filter(estado=Purchase.CONFIRMADA, tipo_pago=Purchase.CREDITO)
        .select_related('supplier')
        .order_by('purchase_date')
    )
    if estado_pago in (Purchase.PENDIENTE, Purchase.PAGADA):
        compras = compras.filter(estado_pago=estado_pago)
    if q:
        compras = compras.filter(
            Q(supplier__name__icontains=q) |
            Q(document_number__icontains=q) |
            Q(id__icontains=q)
        )
    return render(request, 'pagos/compra_list.html', {
        'items': compras,
        'q': q,
        'estado_pago': estado_pago,
    })


@roles_required(*ROLES_PAGOS)
def pago_create(request, compra_pk):
    """Registra un abono sobre una compra pendiente de pago."""
    compra = get_object_or_404(Purchase, pk=compra_pk)

    if compra.estado == Purchase.ANULADA:
        messages.error(request, 'No se puede registrar un pago sobre una compra anulada.')
        return redirect('pagos:compra_list')
    if compra.estado != Purchase.CONFIRMADA:
        messages.error(request, 'Solo se pueden registrar pagos sobre compras confirmadas.')
        return redirect('pagos:compra_list')
    if compra.saldo <= 0:
        messages.error(request, f'La Compra #{compra.id} ya está totalmente pagada.')
        return redirect('pagos:compra_list')

    if request.method == 'POST':
        form = PagoCompraForm(request.POST, compra=compra)
        if form.is_valid():
            registrar_pago(
                compra_id=compra.id,
                fecha=form.cleaned_data['fecha'],
                valor=form.cleaned_data['valor'],
                observacion=form.cleaned_data['observacion'],
            )
            messages.success(request, f'Abono registrado sobre la Compra #{compra.id}.')
            return redirect('pagos:historial_pagos', compra_pk=compra.id)
    else:
        form = PagoCompraForm(initial={'fecha': date.today()}, compra=compra)

    return render(request, 'pagos/pago_form.html', {
        'form': form, 'compra': compra, 'title': f'Registrar pago — Compra #{compra.id}',
    })


@roles_required(*ROLES_PAGOS)
def historial_pagos(request, compra_pk):
    """Muestra el historial de abonos registrados sobre una compra."""
    compra = get_object_or_404(Purchase.objects.select_related('supplier'), pk=compra_pk)
    pagos = compra.pagos.all()
    return render(request, 'pagos/historial_pagos.html', {
        'compra': compra, 'pagos': pagos,
    })


@roles_required(*ROLES_PAGOS)
def pago_update(request, pk):
    """Edita un abono ya registrado, recalculando el saldo de la compra."""
    pago = get_object_or_404(PagoCompra.objects.select_related('compra'), pk=pk)
    compra = pago.compra

    if request.method == 'POST':
        form = PagoCompraForm(request.POST, instance=pago, compra=compra)
        if form.is_valid():
            actualizar_pago(
                pago,
                fecha=form.cleaned_data['fecha'],
                valor=form.cleaned_data['valor'],
                observacion=form.cleaned_data['observacion'],
            )
            messages.success(request, f'Abono #{pago.id} actualizado.')
            return redirect('pagos:historial_pagos', compra_pk=compra.id)
    else:
        form = PagoCompraForm(instance=pago, compra=compra)

    return render(request, 'pagos/pago_form.html', {
        'form': form, 'compra': compra, 'pago': pago,
        'title': f'Editar pago #{pago.id} — Compra #{compra.id}',
    })


@roles_required(*ROLES_PAGOS)
def pago_delete(request, pk):
    """Elimina un abono, solo si la compra no está totalmente pagada."""
    pago = get_object_or_404(PagoCompra.objects.select_related('compra'), pk=pk)
    compra = pago.compra

    if compra.estado_pago == Purchase.PAGADA:
        messages.error(
            request,
            f'No se puede eliminar el abono: la Compra #{compra.id} ya está pagada completamente.'
        )
        return redirect('pagos:historial_pagos', compra_pk=compra.id)

    if request.method == 'POST':
        compra_id = compra.id
        eliminar_pago(pago)
        messages.success(request, f'Abono #{pago.id} eliminado.')
        return redirect('pagos:historial_pagos', compra_pk=compra_id)

    return render(request, 'pagos/pago_confirm_delete.html', {
        'pago': pago, 'compra': compra,
    })
