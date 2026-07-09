from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission

# Diccionario: rol -> lista de codenames de permisos.
# '__all__' asigna TODOS los permisos existentes en el sistema.
ROLES = {
    # El Administrador recibe todos los permisos y ve todo el sistema,
    # incluyendo la gestión de usuarios, roles y permisos.
    'Administrador': '__all__',

    # El Vendedor atiende clientes y gestiona la facturación de ventas.
    # Ve el catálogo (marcas, grupos, proveedores, productos) en modo lectura
    # para poder armar facturas, pero no lo administra.
    'Vendedor': [
        'view_customer', 'add_customer', 'change_customer',
        'view_customerprofile', 'add_customerprofile', 'change_customerprofile',
        'view_invoice', 'add_invoice', 'change_invoice', 'delete_invoice',
        'view_invoicedetail', 'add_invoicedetail', 'change_invoicedetail', 'delete_invoicedetail',
        'view_creditnote', 'add_creditnote',
        'view_brand', 'view_productgroup', 'view_supplier', 'view_product',
    ],

    # El Analista de Compras gestiona el catálogo completo y las compras
    # a proveedores, y puede consultar el historial de movimientos de stock.
    'Analista de Compras': [
        'view_brand', 'add_brand', 'change_brand', 'delete_brand',
        'view_productgroup', 'add_productgroup', 'change_productgroup', 'delete_productgroup',
        'view_supplier', 'add_supplier', 'change_supplier', 'delete_supplier',
        'view_product', 'add_product', 'change_product', 'delete_product',
        'view_purchase', 'add_purchase', 'change_purchase', 'delete_purchase',
        'view_purchasedetail', 'add_purchasedetail', 'change_purchasedetail', 'delete_purchasedetail',
        'view_suppliercreditnote', 'add_suppliercreditnote',
        'view_stockmovement',
    ],

    # El Cliente se autoregistra desde la página pública. Solo puede ver el
    # catálogo de productos (su propia tienda, carrito y pedidos se manejan
    # con lógica de vista, no con permisos de Django).
    'Cliente': [
        'view_product',
    ],
}


class Command(BaseCommand):
    help = 'Crea (o actualiza) los 3 roles del sistema con sus permisos: Administrador, Vendedor y Analista de Compras.'

    def handle(self, *args, **kwargs):
        for role_name, codenames in ROLES.items():
            # get_or_create: si el rol ya existe no lo duplica.
            group, created = Group.objects.get_or_create(name=role_name)

            if codenames == '__all__':
                perms = Permission.objects.all()
            else:
                perms = Permission.objects.filter(codename__in=codenames)

            # set() reemplaza los permisos del rol por esta lista (idempotente).
            group.permissions.set(perms)

            status = 'creado' if created else 'actualizado'
            self.stdout.write(self.style.SUCCESS(
                f'Rol "{role_name}" {status} con {perms.count()} permisos'
            ))
