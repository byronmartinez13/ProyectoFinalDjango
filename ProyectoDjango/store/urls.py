from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('registro/', views.CustomerSignUpView.as_view(), name='customer_signup'),
    path('perfil/completar/', views.complete_profile, name='complete_profile'),

    path('', views.CatalogView.as_view(), name='catalog'),
    path('carrito/', views.cart_view, name='cart'),
    path('carrito/agregar/<int:pk>/', views.add_to_cart, name='add_to_cart'),
    path('carrito/actualizar/<int:pk>/', views.update_cart_item, name='update_cart_item'),
    path('carrito/quitar/<int:pk>/', views.remove_from_cart, name='remove_from_cart'),

    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/paypal/crear-orden/', views.paypal_create_order, name='paypal_create_order'),
    path('checkout/paypal/capturar/<str:paypal_order_id>/', views.paypal_capture_order, name='paypal_capture_order'),
    path('pedido/<int:pk>/confirmacion/', views.order_confirmation, name='order_confirmation'),
]
