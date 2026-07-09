import logging
from functools import wraps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils import timezone

# Configurar logger para auditoría
# Los mensajes se guardan en la consola y pueden redirigirse a archivo
logger = logging.getLogger('audit')


def audit_action(action_name):
    """
    Decorador que registra las acciones del usuario para auditoría.
    
    Parámetros:
        action_name (str): Nombre de la acción a registrar.
                          Ejemplo: "CREATE_BRAND", "DELETE_PRODUCT"
    
    Uso:
        @login_required
        @audit_action("CREATE_BRAND")
        def brand_create(request):
            ...
    
    ¿POR QUÉ?
    Para tener un registro de quién hizo qué en el sistema.
    Si un producto es eliminado, puedes rastrear quién lo hizo.
    
    ¿CÓMO FUNCIONA?
    1. El usuario llama a la vista (ej: brand_create)
    2. El decorador intercepta ANTES de ejecutar la vista
    3. Registra: usuario, acción, fecha/hora, método HTTP, IP
    4. Ejecuta la vista normalmente
    5. Si el método es POST (envío de formulario), registra también
       que la acción fue completada
    """

    def decorator(view_func):
        @wraps(view_func)  # Preserva el nombre y docstring de la vista original
        def wrapper(request, *args, **kwargs):

            # Obtener datos del usuario y la petición
            user = request.user.username if request.user.is_authenticated else 'Anonymous'
            ip = request.META.get('REMOTE_ADDR', 'unknown')  # IP del usuario
            method = request.method  # GET o POST
            timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
            path = request.path  # URL que visitó

            # Registrar la acción en el log
            logger.info(
                f'[AUDIT] {timestamp} | User: {user} | '
                f'Action: {action_name} | Method: {method} | '
                f'Path: {path} | IP: {ip}'
            )

            # También imprimir en consola para desarrollo
            print(
                f'\n[AUDIT] {timestamp} | User: {user} | '
                f'Action: {action_name} | Method: {method} | '
                f'Path: {path} | IP: {ip}'
            )

            # Ejecutar la vista original normalmente
            response = view_func(request, *args, **kwargs)

            # Si fue POST, registrar que la acción se completó
            if method == 'POST':
                print(f'[AUDIT] {timestamp} | COMPLETED: {action_name} by {user}')

            return response

        return wrapper
    return decorator


def roles_required(*group_names, strict=False, redirect_url='/'):
    """
    Decorador equivalente a shared.mixins.GroupRequiredMixin pero para
    vistas basadas en función. El superusuario siempre pasa.

    Con strict=False (por defecto) las cuentas sin ningún rol asignado
    (legado) conservan acceso completo, igual que GroupRequiredMixin.
    Con strict=True, ninguna cuenta sin rol pasa.

    Uso:
        @roles_required('Administrador', 'Analista de Compras')
        def purchase_create(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if request.user.is_superuser:
                return view_func(request, *args, **kwargs)
            user_groups = request.user.groups.all()
            if not strict and not user_groups.exists():
                return view_func(request, *args, **kwargs)
            if user_groups.filter(name__in=group_names).exists():
                return view_func(request, *args, **kwargs)
            messages.error(request, 'No tienes permiso para acceder a esta opción.')
            return redirect(redirect_url)
        return wrapper
    return decorator


def cliente_required(view_func):
    """
    Decorador equivalente a shared.mixins.ClienteRequiredMixin pero para
    vistas basadas en función (usado en store/views.py: carrito, checkout).
    Solo deja pasar a cuentas con el rol Cliente (o superusuario).
    """
    return roles_required('Cliente', strict=True, redirect_url='billing:dashboard')(view_func)
