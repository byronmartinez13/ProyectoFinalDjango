"""Wrapper delgado sobre el REST API v2 de PayPal Checkout (sandbox/live).

Requiere PAYPAL_CLIENT_ID / PAYPAL_CLIENT_SECRET / PAYPAL_MODE en settings
(leídos desde variables de entorno, ver .env.example).
"""
import requests
from django.conf import settings


class PayPalError(Exception):
    pass


def _base_url():
    return (
        'https://api-m.sandbox.paypal.com'
        if settings.PAYPAL_MODE != 'live'
        else 'https://api-m.paypal.com'
    )


def get_access_token():
    if not settings.PAYPAL_CLIENT_ID or not settings.PAYPAL_CLIENT_SECRET:
        raise PayPalError(
            'PayPal no está configurado: define PAYPAL_CLIENT_ID y '
            'PAYPAL_CLIENT_SECRET en el archivo .env.'
        )
    resp = requests.post(
        f'{_base_url()}/v1/oauth2/token',
        auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
        data={'grant_type': 'client_credentials'},
        timeout=15,
    )
    if not resp.ok:
        raise PayPalError(f'No se pudo autenticar con PayPal: {resp.text}')
    return resp.json()['access_token']


def create_order(total):
    """Crea una orden de PayPal por `total` (Decimal) en USD y devuelve su id."""
    token = get_access_token()
    resp = requests.post(
        f'{_base_url()}/v2/checkout/orders',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'intent': 'CAPTURE',
            'purchase_units': [{
                'amount': {'currency_code': 'USD', 'value': f'{total:.2f}'},
            }],
        },
        timeout=15,
    )
    if not resp.ok:
        raise PayPalError(f'No se pudo crear la orden en PayPal: {resp.text}')
    return resp.json()['id']


def capture_order(paypal_order_id):
    """Captura el pago de una orden ya aprobada por el comprador."""
    token = get_access_token()
    resp = requests.post(
        f'{_base_url()}/v2/checkout/orders/{paypal_order_id}/capture',
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'},
        json={},
        timeout=15,
    )
    data = resp.json()
    if not resp.ok or data.get('status') != 'COMPLETED':
        raise PayPalError(f'No se pudo capturar el pago en PayPal: {data}')
    return data
