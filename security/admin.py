from django.contrib import admin  # noqa: F401

# La gestión de usuarios, roles (Group) y permisos (Permission) se hace desde
# las vistas propias de esta app (ver security/views.py), no desde el admin
# de Django. Group y User ya se muestran en /admin/ por defecto gracias a
# django.contrib.auth.
