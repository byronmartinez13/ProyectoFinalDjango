import logging

from django.conf import settings
from django.core.mail import send_mail

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
