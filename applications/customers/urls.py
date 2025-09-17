from django.urls import path
from . import views

app_name='cliente_app'

urlpatterns=[
    path(
        '',
        views.ClienteView.as_view(),
        name='clientes',
    ),

    path(
        'lista-clientes/',
        views.ListClientes.as_view(),
        name='lista-clientes',
    ),
    
    path('cliente/<int:pk>/historial/', views.HistorialVentasCliente.as_view(), name='historial_cliente'),
    path('cliente/<int:pk>/saldos/', views.HistorialClienteView.as_view(), name='historial_saldos'),
    path('cliente/<int:pk>/utilidad/', views.HistorialClienteUtilidad.as_view(), name='historial_utilidad'),
]
