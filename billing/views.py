import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, JsonResponse
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db import transaction
from django.db.models import F
from .models import *
from shared.mixins import StaffRequiredMixin, SearchExportMixin, AdminOnlyMixin, GroupRequiredMixin
from shared.decorators import audit_action, roles_required
from shared.emails import send_welcome_email
from django.views.decorators.http import require_POST
from .forms import SignUpForm, BrandForm, InvoiceForm, InvoiceDetailFormSet, InvoiceDetailEditFormSet, CreditNoteForm, CustomerQuickForm, SupplierQuickForm
from .ProductForm import ProductForm
from .CustomerForm import CustomerForm
from .services import check_stock, emit_invoice, recalc_invoice
from inventory.models import StockMovement


# === REGISTRO (solo Administrador puede crear usuarios) ===
class SignUpView(AdminOnlyMixin, CreateView):
    """
    Crea una cuenta de usuario nueva. Restringido al rol Administrador:
    ya no es un registro público, así que NO inicia sesión automáticamente
    como el usuario recién creado (el Administrador conserva su propia
    sesión) y redirige de vuelta al listado de usuarios.
    """
    form_class    = SignUpForm
    template_name = 'registration/signup.html'
    success_url   = reverse_lazy('security:user_list')

    def form_valid(self, form):
        response = super().form_valid(form)
        role = form.cleaned_data.get('role')
        if self.object.email:
            send_welcome_email(self.object, form.cleaned_data['password1'], role.name if role else '—')
        messages.success(
            self.request,
            f'Usuario "{self.object.username}" creado correctamente.'
        )
        return response

# === HOME (página pública) ===
def home(request):
    if request.user.is_authenticated:
        return redirect('billing:dashboard')
    return render(request, 'billing/home.html')

# === DASHBOARD (selector de módulos) ===
@login_required
def dashboard(request):
    if request.user.groups.filter(name='Cliente').exists() and not request.user.is_superuser:
        return redirect('store:catalog')

    from purchasing.models import Purchase
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    from datetime import timedelta, date

    total_ventas  = Invoice.objects.filter(estado=Invoice.EMITIDA).aggregate(t=Sum('total'))['t'] or 0
    total_compras = Purchase.objects.filter(estado=Purchase.CONFIRMADA).aggregate(t=Sum('total'))['t'] or 0
    margen_bruto  = total_ventas - total_compras

    top_products = (
        InvoiceDetail.objects
        .filter(invoice__estado=Invoice.EMITIDA)
        .values('product__name')
        .annotate(total_qty=Sum('quantity'), total_rev=Sum('subtotal'))
        .order_by('-total_qty')[:5]
    )
    top_suppliers = (
        Purchase.objects
        .filter(estado=Purchase.CONFIRMADA)
        .values('supplier__name')
        .annotate(total_amount=Sum('total'), num_orders=Count('id'))
        .order_by('-total_amount')[:5]
    )

    six_months_ago = date.today() - timedelta(days=183)
    monthly_sales = (
        Invoice.objects
        .filter(estado=Invoice.EMITIDA, invoice_date__date__gte=six_months_ago)
        .annotate(month=TruncMonth('invoice_date'))
        .values('month')
        .annotate(total=Sum('total'))
        .order_by('month')
    )
    sales_labels = [m['month'].strftime('%b %Y') for m in monthly_sales]
    sales_data   = [float(m['total']) for m in monthly_sales]

    estado_data = [
        Invoice.objects.filter(estado=Invoice.BORRADOR).count(),
        Invoice.objects.filter(estado=Invoice.EMITIDA).count(),
        Invoice.objects.filter(estado=Invoice.ANULADA).count(),
    ]

    context = {
        'total_products':    Product.objects.count(),
        'total_customers':   Customer.objects.count(),
        'total_invoices':    Invoice.objects.count(),
        'low_stock':         Product.objects.filter(stock__lte=5, is_active=True).count(),
        'total_ventas':      total_ventas,
        'total_compras':     total_compras,
        'margen_bruto':      margen_bruto,
        'top_products':      top_products,
        'top_suppliers':     top_suppliers,
        'sales_labels_json': json.dumps(sales_labels),
        'sales_data_json':   json.dumps(sales_data),
        'estado_data_json':  json.dumps(estado_data),
    }
    return render(request, 'billing/dashboard.html', context)


# === PDF DE FACTURA ===
@login_required
def invoice_pdf(request, pk):
    from .pdf import build_invoice_pdf

    invoice = get_object_or_404(
        Invoice.objects.select_related('customer')
                       .prefetch_related('details__product', 'credit_notes'),
        pk=pk,
    )
    resp = HttpResponse(build_invoice_pdf(invoice), content_type='application/pdf')
    resp['Content-Disposition'] = f'attachment; filename="factura-{invoice.id}.pdf"'
    return resp


# ── BRANDS ──────────────────────────────────────────────────────────────
@roles_required('Administrador', 'Analista de Compras')
@audit_action('CREATE_BRAND')
def brand_create(request):
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca creada correctamente.')
            return redirect('billing:brand_list')
    else:
        form = BrandForm()
    return render(request, 'billing/brand_form.html', {'form': form, 'title': 'Crear Marca'})

@roles_required('Administrador', 'Analista de Compras')
@audit_action('UPDATE_BRAND')
def brand_update(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        form = BrandForm(request.POST, instance=brand)
        if form.is_valid():
            form.save()
            messages.success(request, 'Marca actualizada correctamente.')
            return redirect('billing:brand_list')
    else:
        form = BrandForm(instance=brand)
    return render(request, 'billing/brand_form.html', {'form': form, 'title': 'Editar Marca'})

@roles_required('Administrador')
@audit_action('DELETE_BRAND')
def brand_delete(request, pk):
    brand = get_object_or_404(Brand, pk=pk)
    if request.method == 'POST':
        brand.delete()
        messages.success(request, 'Marca eliminada.')
        return redirect('billing:brand_list')
    return render(request, 'billing/brand_confirm_delete.html', {'object': brand})


# ── INVOICES ─────────────────────────────────────────────────────────────

def _product_data_json():
    data = {
        str(p['id']): {
            'price':    str(p['unit_price']),
            'stock':    p['stock'],
            'tax_rate': str(p['tax_rate']),
        }
        for p in Product.objects.filter(is_active=True)
                                .values('id', 'unit_price', 'stock', 'tax_rate')
    }
    return json.dumps(data)


@roles_required('Administrador', 'Vendedor')
def invoice_create(request):
    """Crea un borrador de factura con sus líneas de detalle (sin afectar stock)."""
    if request.method == 'POST':
        form    = InvoiceForm(request.POST)
        formset = InvoiceDetailFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            invoice          = form.save(commit=False)
            invoice.estado   = Invoice.BORRADOR
            invoice.save()
            formset.instance = invoice
            formset.save()
            recalc_invoice(invoice)
            messages.info(request,
                f'Borrador #{invoice.id} guardado. Revísalo y pulsa "Emitir" para confirmar.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        form    = InvoiceForm()
        formset = InvoiceDetailFormSet()

    return render(request, 'billing/invoice_form.html', {
        'form': form, 'formset': formset,
        'title': 'Nueva Factura',
        'product_data_json': _product_data_json(),
    })


@roles_required('Administrador', 'Vendedor')
def invoice_update(request, pk):
    """Edita un borrador de factura (solo en estado BORRADOR)."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not invoice.can_edit:
        messages.error(request, 'Solo se puede editar una factura en estado Borrador.')
        return redirect('billing:invoice_detail', pk=pk)

    if request.method == 'POST':
        form    = InvoiceForm(request.POST, instance=invoice)
        formset = InvoiceDetailEditFormSet(request.POST, instance=invoice)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            recalc_invoice(invoice)
            messages.success(request, f'Borrador #{invoice.id} actualizado.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        form    = InvoiceForm(instance=invoice)
        formset = InvoiceDetailEditFormSet(instance=invoice)

    return render(request, 'billing/invoice_form.html', {
        'form': form, 'formset': formset,
        'invoice': invoice,
        'title': f'Editar Borrador #{invoice.id}',
        'product_data_json': _product_data_json(),
    })


@login_required
def invoice_confirm(request, pk):
    """Emite un borrador: valida stock, cambia estado a EMITIDA y descuenta stock."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not invoice.can_confirm:
        messages.error(request, 'Solo se puede emitir una factura en estado Borrador.')
        return redirect('billing:invoice_detail', pk=pk)

    if request.method == 'POST':
        tipo_pago = request.POST.get('tipo_pago')
        if tipo_pago not in (Invoice.CONTADO, Invoice.CREDITO):
            messages.error(request, 'Selecciona la forma de pago: Contado o Crédito.')
            return redirect('billing:invoice_confirm', pk=pk)

        stock_errors = check_stock(invoice)
        if stock_errors:
            for msg in stock_errors:
                messages.error(request, f'Stock insuficiente — {msg}')
            return redirect('billing:invoice_confirm', pk=pk)

        emit_invoice(invoice, request.user, tipo_pago=tipo_pago)

        if tipo_pago == Invoice.CONTADO:
            messages.success(request, f'Factura #{invoice.id} emitida y pagada al contado.')
        else:
            messages.success(request, f'Factura #{invoice.id} emitida a crédito. Saldo pendiente: ${invoice.saldo}.')
        return redirect('billing:invoice_detail', pk=invoice.pk)

    details_with_status = [
        {
            'det': d,
            'ok': d.product.stock >= d.quantity,
            'low': d.product.stock == d.quantity,
            'remaining': d.product.stock - d.quantity,
        }
        for d in invoice.details.select_related('product').all()
    ]
    can_emit = all(row['ok'] for row in details_with_status)
    return render(request, 'billing/invoice_confirm_emit.html', {
        'invoice': invoice,
        'details_with_status': details_with_status,
        'can_emit': can_emit,
    })


@roles_required('Administrador', 'Analista de Compras')
def invoice_cancel(request, pk):
    """Anula una factura emitida: revierte el stock y la marca como Anulada/Inactiva."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not invoice.can_cancel:
        messages.error(request, 'Solo se puede anular una factura en estado Emitida.')
        return redirect('billing:invoice_detail', pk=pk)

    if request.method == 'POST':
        details = list(invoice.details.select_related('product').all())
        with transaction.atomic():
            for detail in details:
                Product.objects.filter(pk=detail.product_id).update(
                    stock=F('stock') + detail.quantity
                )
            StockMovement.objects.bulk_create([
                StockMovement(
                    product_id=detail.product_id,
                    quantity=detail.quantity,
                    movement_type=StockMovement.DEVOLUCION_VENTA,
                    user=request.user,
                    invoice=invoice,
                )
                for detail in details
            ])
            invoice.estado    = Invoice.ANULADA
            invoice.is_active = False
            invoice.save()
        messages.success(request,
            f'Factura #{invoice.id} anulada. Stock revertido automáticamente.')
        return redirect('billing:invoice_list')

    return render(request, 'billing/invoice_cancel.html', {'invoice': invoice})


@login_required
def invoice_substitute(request, pk):
    """Anula la factura original y crea un nuevo borrador con los mismos datos."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not invoice.can_substitute:
        messages.error(request, 'Solo se puede sustituir una factura emitida.')
        return redirect('billing:invoice_detail', pk=pk)

    if request.method == 'POST':
        original_details = list(invoice.details.select_related('product').all())
        with transaction.atomic():
            for detail in original_details:
                Product.objects.filter(pk=detail.product_id).update(
                    stock=F('stock') + detail.quantity
                )
            StockMovement.objects.bulk_create([
                StockMovement(
                    product_id=detail.product_id,
                    quantity=detail.quantity,
                    movement_type=StockMovement.DEVOLUCION_VENTA,
                    user=request.user,
                    invoice=invoice,
                )
                for detail in original_details
            ])
            invoice.estado    = Invoice.ANULADA
            invoice.is_active = False
            invoice.save()

            new_invoice = Invoice.objects.create(
                customer=invoice.customer,
                estado=Invoice.BORRADOR,
            )
            for detail in original_details:
                InvoiceDetail.objects.create(
                    invoice      = new_invoice,
                    product      = detail.product,
                    quantity     = detail.quantity,
                    unit_price   = detail.unit_price,
                    discount_pct = detail.discount_pct,
                )
        recalc_invoice(new_invoice)

        messages.success(request,
            f'Factura #{invoice.id} anulada. Nuevo borrador #{new_invoice.id} creado. '
            f'Corrija los datos y emita la factura de reemplazo.')
        return redirect('billing:invoice_update', pk=new_invoice.pk)

    return render(request, 'billing/invoice_substitute.html', {'invoice': invoice})


@login_required
def credit_note_create(request, pk):
    """Crea una Nota de Crédito vinculada a una factura emitida."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not invoice.can_credit_note:
        messages.error(request, 'Solo se pueden crear notas de crédito sobre facturas emitidas.')
        return redirect('billing:invoice_detail', pk=pk)

    if request.method == 'POST':
        form = CreditNoteForm(request.POST, invoice=invoice)
        if form.is_valid():
            note         = form.save(commit=False)
            note.invoice = invoice
            note.save()
            messages.success(request,
                f'Nota de Crédito NC-{note.id} registrada sobre Factura #{invoice.id}.')
            return redirect('billing:invoice_detail', pk=invoice.pk)
    else:
        form = CreditNoteForm(invoice=invoice, initial={
            'amount': invoice.total,
            'tipo':   CreditNote.TIPO_TOTAL,
        })

    return render(request, 'billing/credit_note_form.html', {
        'form': form, 'invoice': invoice,
    })


@login_required
def invoice_detail(request, pk):
    """Muestra el detalle completo de una factura."""
    invoice = get_object_or_404(
        Invoice.objects.select_related('customer')
                       .prefetch_related('details__product', 'credit_notes'),
        pk=pk
    )
    return render(request, 'billing/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_delete(request, pk):
    """Elimina un borrador de factura (solo en estado BORRADOR)."""
    invoice = get_object_or_404(Invoice, pk=pk)
    if not invoice.can_delete:
        messages.error(request,
            'Solo se puede eliminar una factura en estado Borrador. '
            'Para las emitidas, usa "Anular".')
        return redirect('billing:invoice_detail', pk=pk)
    if request.method == 'POST':
        invoice_id = invoice.id
        invoice.delete()
        messages.success(request, f'Borrador #{invoice_id} eliminado.')
        return redirect('billing:invoice_list')
    return render(request, 'billing/invoice_confirm_delete.html', {'object': invoice})


# ── BRAND (CBV list) ─────────────────────────────────────────────────────
class BrandListView(LoginRequiredMixin, GroupRequiredMixin, SearchExportMixin, ListView):
    group_required  = ['Administrador', 'Analista de Compras']
    model           = Brand
    template_name   = 'billing/brand_list.html'
    context_object_name = 'items'
    export_filename = 'marcas'
    export_fields   = [
        ('Nombre', 'name'), ('Descripción', 'description'), ('Activo', 'is_active'),
    ]
    search_fields   = [
        {'param': 'q',         'fields': ['name__icontains', 'description__icontains']},
        {'param': 'is_active', 'field':  'is_active', 'type': 'bool'},
    ]


# ── PRODUCTGROUP (CBV) ──────────────────────────────────────────────────
class ProductGroupListView(LoginRequiredMixin, GroupRequiredMixin, SearchExportMixin, ListView):
    group_required  = ['Administrador', 'Analista de Compras']
    model           = ProductGroup
    template_name   = 'billing/productgroup_list.html'
    context_object_name = 'items'
    export_filename = 'grupos'
    export_fields   = [('Nombre', 'name'), ('Activo', 'is_active')]
    search_fields   = [
        {'param': 'q',         'field': 'name__icontains'},
        {'param': 'is_active', 'field': 'is_active', 'type': 'bool'},
    ]

class ProductGroupCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    group_required = ['Administrador', 'Analista de Compras']
    model         = ProductGroup
    fields        = ['name', 'is_active']
    template_name = 'billing/productgroup_form.html'
    success_url   = reverse_lazy('billing:productgroup_list')

class ProductGroupUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    group_required = ['Administrador', 'Analista de Compras']
    model         = ProductGroup
    fields        = ['name', 'is_active']
    template_name = 'billing/productgroup_form.html'
    success_url   = reverse_lazy('billing:productgroup_list')

class ProductGroupDeleteView(LoginRequiredMixin, GroupRequiredMixin, StaffRequiredMixin, DeleteView):
    group_required    = ['Administrador']
    model             = ProductGroup
    template_name     = 'billing/productgroup_confirm_delete.html'
    success_url       = reverse_lazy('billing:productgroup_list')
    staff_redirect_url = '/groups/'


# ── SUPPLIER (CBV) ──────────────────────────────────────────────────────
class SupplierListView(LoginRequiredMixin, GroupRequiredMixin, SearchExportMixin, ListView):
    group_required  = ['Administrador', 'Analista de Compras']
    model           = Supplier
    template_name   = 'billing/supplier_list.html'
    context_object_name = 'items'
    export_filename = 'proveedores'
    export_fields   = [
        ('Nombre', 'name'), ('Contacto', 'contact_name'),
        ('Email', 'email'), ('Teléfono', 'phone'), ('Activo', 'is_active'),
    ]
    search_fields   = [
        {'param': 'q',         'fields': ['name__icontains', 'contact_name__icontains', 'email__icontains']},
        {'param': 'phone',     'field':  'phone__icontains'},
        {'param': 'is_active', 'field':  'is_active', 'type': 'bool'},
    ]

class SupplierCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    group_required = ['Administrador', 'Analista de Compras']
    model         = Supplier
    fields        = ['name', 'contact_name', 'email', 'phone', 'address', 'is_active', 'photo']
    template_name = 'billing/supplier_form.html'
    success_url   = reverse_lazy('billing:supplier_list')

class SupplierUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    group_required = ['Administrador', 'Analista de Compras']
    model         = Supplier
    fields        = ['name', 'contact_name', 'email', 'phone', 'address', 'is_active', 'photo']
    template_name = 'billing/supplier_form.html'
    success_url   = reverse_lazy('billing:supplier_list')

class SupplierDeleteView(LoginRequiredMixin, GroupRequiredMixin, DeleteView):
    group_required     = ['Administrador', 'Analista de Compras']
    model              = Supplier
    template_name      = 'billing/supplier_confirm_delete.html'
    success_url        = reverse_lazy('billing:supplier_list')


# ── PRODUCT (CBV) ───────────────────────────────────────────────────────
class ProductListView(LoginRequiredMixin, GroupRequiredMixin, SearchExportMixin, ListView):
    group_required  = ['Administrador', 'Analista de Compras', 'Vendedor']
    model           = Product
    queryset        = Product.objects.select_related('brand', 'group').prefetch_related('suppliers')
    template_name   = 'billing/product_list.html'
    context_object_name = 'items'
    export_filename = 'productos'
    export_fields   = [
        ('Nombre',      'name'),
        ('Descripción', 'description'),
        ('Marca',       'brand__name'),
        ('Grupo',       'group__name'),
        ('Precio',      'unit_price'),
        ('Stock',       'stock'),
        ('Balance',     lambda p: p.unit_price * p.stock),
        ('Activo',      'is_active'),
    ]
    search_fields   = [
        {'param': 'q',         'fields': ['name__icontains', 'description__icontains']},
        {'param': 'brand',     'field':  'brand__name__icontains'},
        {'param': 'group',     'field':  'group__name__icontains'},
        {'param': 'supplier',  'field':  'suppliers__name__icontains'},
        {'param': 'price_min', 'field':  'unit_price__gte', 'type': 'number'},
        {'param': 'price_max', 'field':  'unit_price__lte', 'type': 'number'},
        {'param': 'stock_min', 'field':  'stock__gte',      'type': 'number'},
        {'param': 'stock_max', 'field':  'stock__lte',      'type': 'number'},
        {'param': 'is_active', 'field':  'is_active',       'type': 'bool'},
    ]

class ProductCreateView(LoginRequiredMixin, GroupRequiredMixin, CreateView):
    group_required = ['Administrador', 'Analista de Compras']
    model         = Product
    form_class    = ProductForm
    template_name = 'billing/product_form.html'
    success_url   = reverse_lazy('billing:product_list')

class ProductUpdateView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    group_required = ['Administrador', 'Analista de Compras']
    model         = Product
    form_class    = ProductForm
    template_name = 'billing/product_form.html'
    success_url   = reverse_lazy('billing:product_list')

class ProductDeleteView(LoginRequiredMixin, GroupRequiredMixin, StaffRequiredMixin, DeleteView):
    group_required     = ['Administrador']
    model              = Product
    template_name      = 'billing/product_confirm_delete.html'
    success_url        = reverse_lazy('billing:product_list')
    staff_redirect_url = '/products/'


# ── CUSTOMER (CBV) ──────────────────────────────────────────────────────
class CustomerListView(LoginRequiredMixin, SearchExportMixin, ListView):
    model           = Customer
    template_name   = 'billing/customer_list.html'
    context_object_name = 'items'
    export_filename = 'clientes'
    export_fields   = [
        ('DNI', 'dni'), ('Apellidos', 'last_name'), ('Nombres', 'first_name'),
        ('Email', 'email'), ('Teléfono', 'phone'), ('Activo', 'is_active'),
    ]
    search_fields   = [
        {'param': 'q',         'fields': ['first_name__icontains', 'last_name__icontains',
                                          'dni__icontains', 'email__icontains']},
        {'param': 'phone',     'field':  'phone__icontains'},
        {'param': 'is_active', 'field':  'is_active', 'type': 'bool'},
    ]

class CustomerCreateView(LoginRequiredMixin, CreateView):
    model         = Customer
    form_class    = CustomerForm
    template_name = 'billing/customer_form.html'
    success_url   = reverse_lazy('billing:customer_list')

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    model         = Customer
    form_class    = CustomerForm
    template_name = 'billing/customer_form.html'
    success_url   = reverse_lazy('billing:customer_list')

class CustomerDeleteView(LoginRequiredMixin, StaffRequiredMixin, DeleteView):
    model              = Customer
    template_name      = 'billing/customer_confirm_delete.html'
    success_url        = reverse_lazy('billing:customer_list')
    staff_redirect_url = '/customers/'


# ── INVOICE (CBV list) ──────────────────────────────────────────────────
@login_required
@require_POST
def customer_quick_create(request):
    form = CustomerQuickForm(request.POST)
    if form.is_valid():
        c = form.save()
        return JsonResponse({'id': c.id, 'text': c.full_name})
    errors = {f: [e['message'] for e in errs] for f, errs in form.errors.get_json_data().items()}
    return JsonResponse({'errors': errors}, status=400)


@login_required
@require_POST
def supplier_quick_create(request):
    form = SupplierQuickForm(request.POST)
    if form.is_valid():
        s = form.save()
        return JsonResponse({'id': s.id, 'text': s.name})
    errors = {f: [e['message'] for e in errs] for f, errs in form.errors.get_json_data().items()}
    return JsonResponse({'errors': errors}, status=400)


class InvoiceListView(LoginRequiredMixin, SearchExportMixin, ListView):
    model           = Invoice
    queryset        = Invoice.objects.select_related('customer')
    template_name   = 'billing/invoice_list.html'
    context_object_name = 'items'
    export_filename = 'facturas'
    export_fields   = [
        ('#',       'id'),
        ('Cliente', lambda inv: str(inv.customer)),
        ('Fecha',   lambda inv: inv.invoice_date.strftime('%d/%m/%Y')),
        ('Estado',  lambda inv: inv.get_estado_display()),
        ('Subtotal','subtotal'),
        ('IVA',     'tax'),
        ('Total',   'total'),
    ]
    search_fields   = [
        {'param': 'q', 'fields': [
            'customer__first_name__icontains',
            'customer__last_name__icontains',
            'customer__dni__icontains',
        ]},
        {'param': 'estado',    'field': 'estado',              'type': 'number'},
        {'param': 'date_from', 'field': 'invoice_date__date__gte', 'type': 'date'},
        {'param': 'date_to',   'field': 'invoice_date__date__lte', 'type': 'date'},
        {'param': 'total_min', 'field': 'total__gte',          'type': 'number'},
        {'param': 'total_max', 'field': 'total__lte',          'type': 'number'},
    ]
