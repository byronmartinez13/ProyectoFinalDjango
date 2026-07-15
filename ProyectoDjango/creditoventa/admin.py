from django.contrib import admin

from .models import CobroFactura


@admin.register(CobroFactura)
class CobroFacturaAdmin(admin.ModelAdmin):
    list_display  = ('id', 'factura', 'fecha', 'valor', 'created_at')
    list_filter   = ('fecha',)
    search_fields = ('factura__id', 'factura__customer__first_name', 'factura__customer__last_name')
    date_hierarchy = 'fecha'
