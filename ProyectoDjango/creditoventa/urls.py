from django.urls import path

from . import views

app_name = 'creditoventa'

urlpatterns = [
    path('', views.factura_list, name='factura_list'),
    path('facturas/<int:factura_pk>/pagar/', views.cobro_create, name='cobro_create'),
    path('facturas/<int:factura_pk>/historial/', views.historial_pagos, name='historial_pagos'),
    path('pagos/<int:pk>/editar/', views.cobro_update, name='cobro_update'),
    path('pagos/<int:pk>/eliminar/', views.cobro_delete, name='cobro_delete'),
]
