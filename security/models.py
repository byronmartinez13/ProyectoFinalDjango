from django.db import models  # noqa: F401

# Esta app no define modelos propios: la gestión de usuarios, roles y
# permisos usa directamente los modelos que Django ya trae incluidos
# (django.contrib.auth.models.User, Group y Permission). Por eso no hay
# migraciones que generar ni ejecutar para esta app.
