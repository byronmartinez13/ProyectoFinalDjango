from django.urls import path
from . import views

app_name = 'purchasing'

urlpatterns = [
    path('',                      views.PurchaseListView.as_view(),   name='purchase_list'),
    path('create/',               views.purchase_create,             name='purchase_create'),
    path('<int:pk>/',             views.purchase_detail,             name='purchase_detail'),
    path('<int:pk>/edit/',        views.purchase_update,             name='purchase_update'),
    path('<int:pk>/confirm/',     views.purchase_confirm,            name='purchase_confirm'),
    path('<int:pk>/cancel/',      views.purchase_cancel,             name='purchase_cancel'),
    path('<int:pk>/delete/',      views.purchase_delete,             name='purchase_delete'),
    path('<int:pk>/credit-note/', views.supplier_credit_note_create, name='supplier_credit_note_create'),
    path('<int:pk>/pdf/',         views.purchase_pdf,                name='purchase_pdf'),
]
