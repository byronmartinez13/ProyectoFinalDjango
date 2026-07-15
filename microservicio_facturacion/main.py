"""Microservicio de Facturación Electrónica (FastAPI) — independiente del
proyecto Django.

Simula la autorización de una factura electrónica ante el SRI (Ecuador):
genera un XML de comprobante, calcula una clave de acceso simulada de 49
dígitos y notifica al cliente por correo. No conoce ni toca la base de
datos de Django: solo responde con el resultado de la "autorización".
"""
import logging
import os
import random
import smtplib
from datetime import date
from email.message import EmailMessage
from typing import List, Literal, Optional

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel, EmailStr, Field

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('microservicio_facturacion')

app = FastAPI(title='Microservicio de Facturación Electrónica SRI', version='1.0.0')

EMAIL_HOST          = os.environ.get('EMAIL_HOST', '')
EMAIL_PORT          = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS       = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL  = os.environ.get('DEFAULT_FROM_EMAIL', 'TecnoStock Facturación <noreply@tecnostock.ec>')
RUC_EMISOR          = os.environ.get('RUC_EMISOR', '0999999999001')

# Códigos de forma de pago del SRI (ficha técnica de comprobantes electrónicos)
FORMA_PAGO_SRI = {
    'efectivo': '01',  # Sin utilización del sistema financiero
    'tarjeta':  '19',  # Tarjeta de crédito
    'credito':  '20',  # Otros con utilización del sistema financiero
}


class ProductoFactura(BaseModel):
    nombre: str
    cantidad: int = Field(gt=0)
    precio_unitario: float = Field(gt=0)


class ClienteFactura(BaseModel):
    nombre: str
    identificacion: str
    email: EmailStr


class FacturaRequest(BaseModel):
    cliente: ClienteFactura
    productos: List[ProductoFactura]
    total: float = Field(gt=0)
    metodo_pago: Literal['efectivo', 'tarjeta', 'credito'] = 'efectivo'
    # Saldo pendiente por cobrar. Solo relevante si metodo_pago == 'credito';
    # si no se envía, se asume que aún no se ha abonado nada (saldo = total).
    saldo: Optional[float] = None


class FacturaResponse(BaseModel):
    status: str
    clave_acceso: str
    numero_factura: str


def _modulo11(clave48: str) -> int:
    """Dígito verificador módulo 11 según la ficha técnica de comprobantes
    electrónicos del SRI (factores cíclicos 2,3,4,5,6,7 de derecha a izq.)."""
    factores = [2, 3, 4, 5, 6, 7]
    total = sum(int(d) * factores[i % len(factores)] for i, d in enumerate(reversed(clave48)))
    residuo = total % 11
    verificador = 11 - residuo
    if verificador == 11:
        return 0
    if verificador == 10:
        return 1
    return verificador


def _generar_clave_acceso() -> str:
    """Simula la clave de acceso de 49 dígitos del SRI:
    fecha(8) + tipoComprobante(2) + ruc(13) + ambiente(1) + serie(6) +
    numero(9) + codigoNumerico(8) + tipoEmision(1) + verificador(1) = 49
    """
    fecha             = date.today().strftime('%d%m%Y')
    tipo_comprobante  = '01'  # 01 = Factura
    ambiente          = '1'   # 1 = Pruebas, 2 = Producción
    serie             = '001001'
    numero            = f'{random.randint(1, 999999999):09d}'
    codigo_numerico   = f'{random.randint(0, 99999999):08d}'
    tipo_emision      = '1'

    clave48 = f'{fecha}{tipo_comprobante}{RUC_EMISOR}{ambiente}{serie}{numero}{codigo_numerico}{tipo_emision}'
    return f'{clave48}{_modulo11(clave48)}'


def _generar_xml(factura: FacturaRequest, clave_acceso: str, numero_factura: str) -> str:
    detalles_xml = ''.join(
        f'''
        <detalle>
            <descripcion>{p.nombre}</descripcion>
            <cantidad>{p.cantidad}</cantidad>
            <precioUnitario>{p.precio_unitario:.2f}</precioUnitario>
            <precioTotalSinImpuesto>{p.cantidad * p.precio_unitario:.2f}</precioTotalSinImpuesto>
        </detalle>'''
        for p in factura.productos
    )

    forma_pago = FORMA_PAGO_SRI.get(factura.metodo_pago, FORMA_PAGO_SRI['efectivo'])
    plazo_xml = ''
    if factura.metodo_pago == 'credito':
        # Plazo simulado; en un SRI real vendría de las condiciones de crédito del cliente.
        plazo_xml = '\n            <plazo>30</plazo>\n            <unidadTiempo>dias</unidadTiempo>'
    pagos_xml = f'''
    <pagos>
        <pago>
            <formaPago>{forma_pago}</formaPago>
            <total>{factura.total:.2f}</total>{plazo_xml}
        </pago>
    </pagos>'''

    return f'''<?xml version="1.0" encoding="UTF-8"?>
<factura id="comprobante" version="1.1.0">
    <infoTributaria>
        <ambiente>1</ambiente>
        <claveAcceso>{clave_acceso}</claveAcceso>
        <ruc>{RUC_EMISOR}</ruc>
        <numeroFactura>{numero_factura}</numeroFactura>
    </infoTributaria>
    <infoFactura>
        <fechaEmision>{date.today().strftime('%d/%m/%Y')}</fechaEmision>
        <razonSocialComprador>{factura.cliente.nombre}</razonSocialComprador>
        <identificacionComprador>{factura.cliente.identificacion}</identificacionComprador>
        <importeTotal>{factura.total:.2f}</importeTotal>
    </infoFactura>
    <detalles>{detalles_xml}
    </detalles>{pagos_xml}
</factura>'''


def _enviar_correo_factura(factura: FacturaRequest, clave_acceso: str, numero_factura: str, xml: str) -> None:
    if not EMAIL_HOST:
        logger.info(
            f'EMAIL_HOST no configurado — correo simulado para {factura.cliente.email} '
            f'(factura {numero_factura}, clave {clave_acceso}, metodo_pago={factura.metodo_pago})'
        )
        return

    es_credito = factura.metodo_pago == 'credito'
    # Si aún no llegó ningún abono, el saldo pendiente es el total de la factura.
    saldo = factura.saldo if factura.saldo is not None else factura.total

    msg = EmailMessage()
    if es_credito:
        msg['Subject'] = f'Factura electrónica {numero_factura} — A CRÉDITO'
        cuerpo = (
            f'Estimado/a {factura.cliente.nombre},\n\n'
            f'Su factura electrónica fue AUTORIZADA por el SRI.\n\n'
            f'N° de factura: {numero_factura}\n'
            f'Clave de acceso: {clave_acceso}\n'
            f'Estado: A CRÉDITO\n'
            f'Total de la factura: ${factura.total:.2f}\n'
            f'Saldo pendiente por pagar: ${saldo:.2f}\n\n'
            f'Recibirá un correo de confirmación cada vez que se registre un abono.\n\n'
            f'Adjuntamos el XML del comprobante.\n'
        )
    else:
        msg['Subject'] = f'Factura electrónica {numero_factura} — Autorizada'
        cuerpo = (
            f'Estimado/a {factura.cliente.nombre},\n\n'
            f'Su factura electrónica fue AUTORIZADA por el SRI.\n\n'
            f'N° de factura: {numero_factura}\n'
            f'Clave de acceso: {clave_acceso}\n'
            f'Total: ${factura.total:.2f}\n\n'
            f'Adjuntamos el XML del comprobante.\n'
        )
    msg['From'] = DEFAULT_FROM_EMAIL
    msg['To'] = factura.cliente.email
    msg.set_content(cuerpo)
    msg.add_attachment(xml.encode('utf-8'), maintype='application', subtype='xml', filename=f'{numero_factura}.xml')

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=15) as server:
            if EMAIL_USE_TLS:
                server.starttls()
            if EMAIL_HOST_USER:
                server.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
            server.send_message(msg)
    except Exception:
        logger.exception(f'No se pudo enviar la factura electrónica a {factura.cliente.email}')


@app.post('/api/facturar', response_model=FacturaResponse)
def facturar(factura: FacturaRequest):
    clave_acceso   = _generar_clave_acceso()
    numero_factura = f'001-001-{random.randint(1, 999999999):09d}'
    xml            = _generar_xml(factura, clave_acceso, numero_factura)

    _enviar_correo_factura(factura, clave_acceso, numero_factura, xml)

    return FacturaResponse(
        status='AUTORIZADO',
        clave_acceso=clave_acceso,
        numero_factura=numero_factura,
    )


@app.get('/health')
def health():
    return {'status': 'ok', 'service': 'microservicio_facturacion'}
