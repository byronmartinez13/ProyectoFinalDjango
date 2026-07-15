"""Cliente HTTP delgado hacia los microservicios externos independientes:
microservicio_pagos (puerto 5001) y microservicio_facturacion (puerto 5002).

Todas las funciones fallan en silencio (solo loguean la excepción): un
microservicio caído nunca debe revertir una venta, una emisión de factura
o un abono ya confirmados en la BD local — mismo criterio que
shared/emails.py con el envío de correo.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger('django')


def notificar_pago(*, correo, monto, metodo, nombre_cliente):
    """Delega la confirmación de pago (correo) a microservicio_pagos."""
    if not correo:
        return
    try:
        requests.post(
            f'{settings.MICROSERVICIO_PAGOS_URL}/api/pagos',
            json={
                'monto': float(monto),
                'metodo': metodo,
                'correo': correo,
                'nombre_cliente': nombre_cliente,
            },
            timeout=10,
        )
    except requests.RequestException:
        logger.exception(f'No se pudo contactar al microservicio de pagos ({correo})')


def notificar_abono(*, correo, factura_id, monto_abono, saldo_restante, nombre_cliente='Cliente'):
    """Delega la confirmación de un abono (correo) a microservicio_pagos."""
    if not correo:
        return
    try:
        requests.post(
            f'{settings.MICROSERVICIO_PAGOS_URL}/api/abonos',
            json={
                'correo': correo,
                'factura_id': factura_id,
                'monto_abono': float(monto_abono),
                'saldo_restante': float(saldo_restante),
                'nombre_cliente': nombre_cliente,
            },
            timeout=10,
        )
    except requests.RequestException:
        logger.exception(f'No se pudo contactar al microservicio de pagos (abono Factura #{factura_id})')


def notificar_facturacion(*, invoice, metodo_pago='efectivo'):
    """Delega la generación de la clave de acceso SRI (simulada) y el
    correo de factura a microservicio_facturacion.

    metodo_pago: 'efectivo' | 'tarjeta' | 'credito' — define el formaPago
    del XML del SRI y el contenido del correo (ver microservicio_facturacion).
    """
    if not invoice.customer.email:
        return
    try:
        resp = requests.post(
            f'{settings.MICROSERVICIO_FACTURACION_URL}/api/facturar',
            json={
                'cliente': {
                    'nombre': invoice.customer.full_name,
                    'identificacion': invoice.customer.dni,
                    'email': invoice.customer.email,
                },
                'productos': [
                    {
                        'nombre': detail.product.name,
                        'cantidad': detail.quantity,
                        'precio_unitario': float(detail.unit_price),
                    }
                    for detail in invoice.details.select_related('product').all()
                ],
                'total': float(invoice.total),
                'metodo_pago': metodo_pago,
                'saldo': float(invoice.saldo),
            },
            timeout=10,
        )
        resp.raise_for_status()
        clave_acceso = resp.json().get('clave_acceso')
        logger.info(f'Factura #{invoice.id}: clave de acceso SRI (simulada) = {clave_acceso}')
    except requests.RequestException:
        logger.exception(f'No se pudo contactar al microservicio de facturación (Factura #{invoice.id})')
