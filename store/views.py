from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView

from billing.models import Product, ProductGroup, Invoice, InvoiceDetail
from billing.services import check_stock, emit_invoice, recalc_invoice
from shared.mixins import ClienteRequiredMixin, SearchListMixin
from shared.decorators import cliente_required
from shared.emails import send_welcome_email

from .forms import CustomerSignUpForm, CompleteProfileForm
from .models import Cart, CartItem
from . import paypal


# === REGISTRO PÚBLICO DE CLIENTES ===
class CustomerSignUpView(CreateView):
    """Registro público desde la página principal: crea la cuenta con rol
    Cliente, inicia sesión automáticamente y envía el correo de bienvenida."""
    form_class    = CustomerSignUpForm
    template_name = 'store/customer_signup.html'

    def form_valid(self, form):
        response = super().form_valid(form)
        login(self.request, self.object)
        if self.object.email:
            send_welcome_email(self.object, form.cleaned_data['password1'], 'Cliente')
        messages.success(self.request, f'¡Bienvenido, {self.object.first_name}! Tu cuenta fue creada correctamente.')
        return response

    def get_success_url(self):
        return reverse('store:catalog')


# === COMPLETAR PERFIL (cuentas Cliente creadas por el Administrador) ===
@cliente_required
def complete_profile(request):
    if hasattr(request.user, 'customer_account'):
        return redirect('store:catalog')

    if request.method == 'POST':
        form = CompleteProfileForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.user       = request.user
            customer.first_name = request.user.first_name or request.user.username
            customer.last_name  = request.user.last_name or request.user.username
            customer.email      = request.user.email
            customer.save()
            messages.success(request, 'Datos guardados. Ya puedes usar la tienda.')
            return redirect('store:catalog')
    else:
        form = CompleteProfileForm()
    return render(request, 'store/complete_profile.html', {'form': form})


def _get_customer(request):
    return getattr(request.user, 'customer_account', None)


# === CATÁLOGO ===
class CatalogView(ClienteRequiredMixin, SearchListMixin, ListView):
    model               = Product
    queryset            = Product.objects.filter(is_active=True).select_related('brand', 'group')
    template_name       = 'store/catalog.html'
    context_object_name = 'items'
    paginate_by         = 12
    search_fields = [
        {'param': 'q',     'fields': ['name__icontains', 'description__icontains', 'brand__name__icontains']},
        {'param': 'group', 'field':  'group_id', 'type': 'number'},
    ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['categories'] = (
            ProductGroup.objects.filter(products__is_active=True)
            .distinct().order_by('name')
        )
        return ctx


# === CARRITO ===
@cliente_required
def add_to_cart(request, pk):
    customer = _get_customer(request)
    if customer is None:
        return redirect('store:complete_profile')

    product = get_object_or_404(Product, pk=pk, is_active=True)
    if product.stock <= 0:
        messages.error(request, f'"{product.name}" está agotado.')
        return redirect('store:catalog')

    cart, _ = Cart.objects.get_or_create(customer=customer)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        item.quantity = min(item.quantity + 1, product.stock)
        item.save()
    messages.success(request, f'"{product.name}" añadido al carrito.')
    return redirect('store:catalog')


@cliente_required
@require_POST
def update_cart_item(request, pk):
    customer = _get_customer(request)
    item = get_object_or_404(CartItem, pk=pk, cart__customer=customer)
    try:
        quantity = int(request.POST.get('quantity', item.quantity))
    except ValueError:
        quantity = item.quantity
    item.quantity = max(1, min(quantity, item.product.stock))
    item.save()
    return redirect('store:cart')


@cliente_required
@require_POST
def remove_from_cart(request, pk):
    customer = _get_customer(request)
    item = get_object_or_404(CartItem, pk=pk, cart__customer=customer)
    item.delete()
    return redirect('store:cart')


@cliente_required
def cart_view(request):
    customer = _get_customer(request)
    if customer is None:
        return redirect('store:complete_profile')
    cart, _ = Cart.objects.get_or_create(customer=customer)
    return render(request, 'store/cart.html', {'cart': cart})


# === CHECKOUT ===
@cliente_required
def checkout_view(request):
    customer = _get_customer(request)
    if customer is None:
        return redirect('store:complete_profile')
    cart, _ = Cart.objects.get_or_create(customer=customer)
    if not cart.items.exists():
        messages.info(request, 'Tu carrito está vacío.')
        return redirect('store:catalog')
    return render(request, 'store/checkout.html', {
        'cart': cart,
        'paypal_client_id': settings.PAYPAL_CLIENT_ID,
    })


@cliente_required
@require_POST
def paypal_create_order(request):
    customer = _get_customer(request)
    if customer is None:
        return JsonResponse({'error': 'Completa tu perfil primero.'}, status=400)
    cart, _ = Cart.objects.get_or_create(customer=customer)
    if not cart.items.exists():
        return JsonResponse({'error': 'El carrito está vacío.'}, status=400)
    try:
        order_id = paypal.create_order(cart.total)
    except paypal.PayPalError as e:
        return JsonResponse({'error': str(e)}, status=502)
    return JsonResponse({'id': order_id})


@cliente_required
@require_POST
def paypal_capture_order(request, paypal_order_id):
    customer = _get_customer(request)
    if customer is None:
        return JsonResponse({'error': 'Completa tu perfil primero.'}, status=400)
    cart, _ = Cart.objects.get_or_create(customer=customer)
    if not cart.items.exists():
        return JsonResponse({'error': 'El carrito está vacío.'}, status=400)

    try:
        paypal.capture_order(paypal_order_id)
    except paypal.PayPalError as e:
        return JsonResponse({'error': str(e)}, status=502)

    payment_method = 'card' if request.POST.get('funding_source') == 'card' else 'paypal'

    with transaction.atomic():
        invoice = Invoice.objects.create(customer=customer, estado=Invoice.BORRADOR)
        for item in cart.items.select_related('product'):
            InvoiceDetail.objects.create(
                invoice=invoice, product=item.product,
                quantity=item.quantity, unit_price=item.product.unit_price,
            )
        recalc_invoice(invoice)

        stock_errors = check_stock(invoice)
        if stock_errors:
            invoice.delete()
            return JsonResponse(
                {'error': 'Stock insuficiente: ' + '; '.join(stock_errors)}, status=409
            )

        emit_invoice(invoice, request.user)
        invoice.payment_method  = payment_method
        invoice.paypal_order_id = paypal_order_id
        invoice.save()
        cart.items.all().delete()

    return JsonResponse({'redirect_url': reverse('store:order_confirmation', args=[invoice.pk])})


@cliente_required
def order_confirmation(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk, customer__user=request.user)
    return render(request, 'store/order_confirmation.html', {'invoice': invoice})
