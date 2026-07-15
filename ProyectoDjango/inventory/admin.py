from django.contrib import admin
from .models import StockMovement


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display  = ('date', 'product', 'movement_type', 'quantity', 'user', 'invoice', 'purchase')
    list_filter   = ('movement_type', 'date')
    search_fields = ('product__name', 'notes')
    readonly_fields = ('date',)
    date_hierarchy = 'date'
