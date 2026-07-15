from django.urls import path

from . import views

app_name = 'pagos'

urlpatterns = [
    path('', views.compra_list, name='compra_list'),
    path('compras/<int:compra_pk>/pagar/', views.pago_create, name='pago_create'),
    path('compras/<int:compra_pk>/historial/', views.historial_pagos, name='historial_pagos'),
    path('pagos/<int:pk>/editar/', views.pago_update, name='pago_update'),
    path('pagos/<int:pk>/eliminar/', views.pago_delete, name='pago_delete'),
]
