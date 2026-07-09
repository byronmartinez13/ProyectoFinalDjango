from django.contrib import admin
from .models import (Brand, ProductGroup, Supplier, Product,
                     Customer, CustomerProfile,
                     Invoice, InvoiceDetail, CreditNote)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display  = ['name', 'is_active', 'created_at']
    search_fields = ['name']
    list_filter   = ['is_active']


@admin.register(ProductGroup)
class ProductGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'contact_name', 'email', 'is_active']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display      = ['name', 'brand', 'group', 'unit_price', 'stock']
    list_filter       = ['brand', 'group']
    filter_horizontal = ['suppliers']


class CustomerProfileInline(admin.StackedInline):
    model = CustomerProfile
    extra = 0
    can_delete = False


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['dni', 'last_name', 'first_name', 'email']
    inlines      = [CustomerProfileInline]


class InvoiceDetailInline(admin.TabularInline):
    model           = InvoiceDetail
    extra           = 1
    readonly_fields = ('subtotal',)


class CreditNoteInline(admin.TabularInline):
    model           = CreditNote
    extra           = 0
    readonly_fields = ('date',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display    = ['id', 'customer', 'invoice_date', 'estado', 'subtotal', 'tax', 'total', 'is_active']
    list_filter     = ['estado', 'is_active', 'invoice_date']
    search_fields   = ['customer__first_name', 'customer__last_name', 'customer__dni']
    readonly_fields = ('subtotal', 'tax', 'total', 'invoice_date')
    inlines         = [InvoiceDetailInline, CreditNoteInline]


@admin.register(CreditNote)
class CreditNoteAdmin(admin.ModelAdmin):
    list_display    = ['id', 'invoice', 'date', 'tipo', 'amount', 'is_active']
    list_filter     = ['tipo', 'is_active']
    search_fields   = ['invoice__id', 'reason']
    readonly_fields = ('date',)
