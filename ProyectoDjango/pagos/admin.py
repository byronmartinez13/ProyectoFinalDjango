from django.contrib import admin

from .models import PagoCompra


@admin.register(PagoCompra)
class PagoCompraAdmin(admin.ModelAdmin):
    list_display  = ('id', 'compra', 'fecha', 'valor', 'created_at')
    list_filter   = ('fecha',)
    search_fields = ('compra__id', 'compra__supplier__name', 'compra__document_number')
    date_hierarchy = 'fecha'
