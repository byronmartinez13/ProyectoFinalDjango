from django.contrib import admin
from .models import Purchase, PurchaseDetail


class PurchaseDetailInline(admin.TabularInline):
    model = PurchaseDetail
    extra = 1
    readonly_fields = ('subtotal',)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('id', 'supplier', 'document_number', 'purchase_date', 'subtotal', 'tax', 'total', 'is_active')
    list_filter = ('is_active', 'supplier', 'purchase_date')
    search_fields = ('document_number', 'supplier__name')
    readonly_fields = ('subtotal', 'tax', 'total')
    inlines = [PurchaseDetailInline]
