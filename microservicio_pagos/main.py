"""Microservicio de Pagos (FastAPI) — independiente del proyecto Django.

Recibe una solicitud de pago, simula su procesamiento (Sandbox) y notifica
al cliente por correo usando smtplib. No conoce ni toca la base de datos
de Django: solo responde con el resultado del pago.
"""
import logging
import os
import smtplib
import uuid
from email.message import EmailMessage
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('microservicio_pagos')

app = FastAPI(title='Microservicio de Pagos', version='1.0.0')

EMAIL_HOST          = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'TecnoStock Pagos <noreply@tecnostock.ec>')


class PagoRequest(BaseModel):
    monto: float = Field(gt=0)
    metodo: Literal['paypal', 'tarjeta']
    correo: EmailStr
    nombre_cliente: str = 'Cliente'


class PagoResponse(BaseModel):
    status: str
    transaction_id: str
    monto: float
    metodo: str


class AbonoRequest(BaseModel):
    correo: EmailStr
    factura_id: int
    monto_abono: float = Field(gt=0)
    saldo_restante: float = Field(ge=0)
    nombre_cliente: str = 'Cliente'


class AbonoResponse(BaseModel):
    status: str
    abono_id: str
    factura_id: int
    monto_abono: float
    saldo_restante: float


def _enviar_correo_confirmacion(pago: PagoRequest, transaction_id: str) -> None:
    """Envía el correo de confirmación de pago. Nunca lanza excepción: un
    fallo de correo no debe revertir un pago ya aprobado (mismo criterio
    que usa el proyecto Django en shared/emails.py)."""
    if not EMAIL_HOST:
        logger.info(
            f'EMAIL_HOST no configurado — correo simulado para {pago.correo} '
            f'(transacción {transaction_id})'
        )
        return

    msg = EmailMessage()
    msg['Subject'] = f'Confirmación de pago — {transaction_id}'
    msg['From'] = DEFAULT_FROM_EMAIL
    msg['To'] = pago.correo
    msg.set_content(
        f'Hola {pago.nombre_cliente},\n\n'
        f'Tu pago fue APROBADO exitosamente.\n\n'
        f'ID de transacción: {transaction_id}\n'
        f'Monto: ${pago.monto:.2f}\n'
        f'Método: {pago.metodo}\n\n'
        f'Gracias por tu compra en TecnoStock.\n'
    )

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=15) as server:
            if EMAIL_USE_TLS:
                server.starttls()
            if EMAIL_HOST_USER:
                server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
    except Exception:
        logger.exception(f'No se pudo enviar el correo de confirmación de pago a {pago.correo}')


@app.post('/api/pagos', response_model=PagoResponse)
def procesar_pago(pago: PagoRequest):
    # --- Aquí colocas tu lógica real de Sandbox (PayPal / pasarela de tarjeta) ---
    transaction_id = f'TXN-{uuid.uuid4().hex[:16].upper()}'
    aprobado = True  # simulación: siempre aprueba

    if not aprobado:
        raise HTTPException(status_code=402, detail='Pago rechazado')

    _enviar_correo_confirmacion(pago, transaction_id)

    return PagoResponse(
        status='APPROVED',
        transaction_id=transaction_id,
        monto=pago.monto,
        metodo=pago.metodo,
    )


def _enviar_correo_abono(abono: AbonoRequest, abono_id: str) -> None:
    """Envía el comprobante de abono. Nunca lanza excepción: el abono ya
    quedó registrado en la BD local de Django, un fallo de correo no debe
    revertirlo."""
    if not EMAIL_HOST:
        logger.info(
            f'EMAIL_HOST no configurado — correo simulado de abono para {abono.correo} '
            f'(Factura #{abono.factura_id})'
        )
        return

    msg = EmailMessage()
    msg['Subject'] = f'Confirmación de Abono — Factura {abono.factura_id}'
    msg['From'] = DEFAULT_FROM_EMAIL
    msg['To'] = abono.correo
    estado_final = (
        'Con este abono, tu factura queda totalmente cancelada.\n'
        if abono.saldo_restante <= 0
        else 'Gracias por tu pago.\n'
    )
    msg.set_content(
        f'Hola {abono.nombre_cliente},\n\n'
        f'Hemos registrado tu abono sobre la Factura #{abono.factura_id}.\n\n'
        f'Abono recibido: ${abono.monto_abono:.2f}\n'
        f'Saldo pendiente por pagar: ${abono.saldo_restante:.2f}\n\n'
        f'{estado_final}'
    )

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=15) as server:
            if EMAIL_USE_TLS:
                server.starttls()
            if EMAIL_HOST_USER:
                server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
    except Exception:
        logger.exception(f'No se pudo enviar el correo de confirmación de abono a {abono.correo}')


@app.post('/api/abonos', response_model=AbonoResponse)
def procesar_abono(abono: AbonoRequest):
    abono_id = f'ABN-{uuid.uuid4().hex[:16].upper()}'

    _enviar_correo_abono(abono, abono_id)

    return AbonoResponse(
        status='APPROVED',
        abono_id=abono_id,
        factura_id=abono.factura_id,
        monto_abono=abono.monto_abono,
        saldo_restante=abono.saldo_restante,
    )


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'microservicio_pagos'}
