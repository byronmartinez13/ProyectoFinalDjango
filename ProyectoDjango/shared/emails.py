import logging

from django.conf import settings
from django.core.mail import EmailMessage, send_mail

logger = logging.getLogger('django')


def send_welcome_email(user, raw_password, role_name):
    """Envía el correo de bienvenida con las credenciales de acceso.

    Se llama tanto desde el registro público de Clientes como desde la
    creación de usuarios por el Administrador, para que toda cuenta nueva
    reciba el mismo correo con su usuario, contraseña y rol asignado.
    """
    nombre = user.first_name or user.username
    subject = 'Bienvenido a TecnoStock'
    message = (
        f'Que tal {nombre}\n\n'
        f'Te damos la bienvenida a TecnoStock un lugar donde podrás encontrar '
        f'gran variedad de productos tecnologicos.\n\n'
        f'A continuación se detallan los datos de tu credencial para que puedas '
        f'ingresar a nuestra plataforma:\n\n'
        f'usuario: {user.username}\n'
        f'Contraseña: {raw_password}\n'
        f'Rol: {role_name}\n'
    )
    try:
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
    except Exception:
        logger.exception(f'No se pudo enviar el correo de bienvenida a {user.email}')


def send_invoice_email(invoice):
    """Envía la factura electrónica (PDF adjunto) al correo del cliente.

    Se llama automáticamente desde billing.services.emit_invoice() al emitir
    una factura, tanto por la emisión manual (Vendedor/Administrador) como
    por el checkout de la Tienda, para que la facturación electrónica llegue
    al cliente sin intervención manual. Si el cliente no tiene correo
    registrado o el envío falla, se registra en el log pero NO se interrumpe
    la emisión de la factura (mismo criterio que send_welcome_email).
    """
    customer = invoice.customer
    if not customer.email:
        logger.warning(
            f'Factura #{invoice.id}: el cliente "{customer}" no tiene correo '
            f'registrado, no se envía la factura electrónica.'
        )
        return

    subject = f'Factura electrónica #{invoice.id} — TecnoStock'
    message = (
        f'Estimado/a {customer.full_name}\n\n'
        f'Gracias por su compra en TecnoStock S.A. Adjuntamos su factura electrónica.\n\n'
        f'N° de Factura: {invoice.id}\n'
        f'Fecha de emisión: {invoice.invoice_date.strftime("%d/%m/%Y %H:%M")}\n'
        f'Total: ${invoice.total}\n\n'
        f'Este es un correo generado automáticamente, por favor no responda a esta dirección.\n'
    )
    try:
        from billing.pdf import build_invoice_pdf
        pdf_bytes = build_invoice_pdf(invoice)

        email = EmailMessage(
            subject, message, settings.DEFAULT_FROM_EMAIL, [customer.email],
        )
        email.attach(f'factura-{invoice.id}.pdf', pdf_bytes, 'application/pdf')
        email.send(fail_silently=False)
    except Exception:
        logger.exception(
            f'No se pudo enviar la factura electrónica #{invoice.id} a {customer.email}'
        )
