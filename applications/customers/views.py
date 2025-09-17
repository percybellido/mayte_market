from django.shortcuts import render

from django.views.generic import ListView, TemplateView, DetailView

from .models import Cliente
from applications.sales.models import Pago, HistorialSaldo

# Create your views here.
class ClienteView(TemplateView):
    template_name='customers/clientes.html'

class ListClientes(ListView):
    context_object_name='lista_clientes'
    template_name='customers/lista_clientes.html'
    paginate_by=8

    def get_queryset(self):
        palabra_clave=self.request.GET.get('kword', '')
        return Cliente.objects.buscar_cliente(palabra_clave)
    
class HistorialVentasCliente(DetailView):
    model = Cliente
    template_name = 'customers/historial_cliente.html'
    context_object_name = 'cliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ultimas_ventas'] = self.object.cliente_venta.all().order_by('-Venta_Fecha')[:6]
        return context
    
# customers/views.py
from django.views.generic import ListView
from django.db.models import Sum, F, FloatField
from applications.sales.models import HistorialSaldo, CarShop, VentaDetalle
from applications.customers.models import Cliente


class HistorialClienteView(ListView):
    model = HistorialSaldo
    template_name = "customers/historial_pagos.html"
    context_object_name = "movimientos"

    
    def get_queryset(self):
        return HistorialSaldo.objects.filter(
            cliente_id=self.kwargs["pk"]
        ).order_by("fecha")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = Cliente.objects.get(id=self.kwargs["pk"])
        context["cliente"] = cliente

        # 🔹 Ganancia total acumulada (todas las ventas del cliente)
        ganancia_total = (
            VentaDetalle.objects
            .filter(VD_VentasId__Venta_CliId=cliente)
            .aggregate(
                total=Sum(
                    (F('VD_Precio') - F('producto__precio_compra')) * F('VD_Cantidad'),
                    output_field=FloatField()
                )
            )['total'] or 0
        )
        context["ganancia_acumulada"] = ganancia_total

        return context

from django.db.models import Sum, F, FloatField
from applications.sales.models import Venta

class HistorialClienteUtilidad(ListView):
    model = Venta
    template_name = 'customers/cliente_utilidad.html'
    context_object_name = "ventas"

    def get_queryset(self):
        cliente = Cliente.objects.get(pk=self.kwargs["pk"])
        return (
            Venta.objects.filter(Venta_CliId=cliente)
            .annotate(
                utilidad_total=Sum(
                    (F('detalles__VD_Precio') - F('detalles__producto__precio_compra')) * F('detalles__VD_Cantidad'),
                    output_field=FloatField()
                ),
                monto_total=Sum(
                    F('detalles__VD_Precio') * F('detalles__VD_Cantidad'),
                    output_field=FloatField()
                )
            )
            .order_by('-Venta_Fecha')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente = Cliente.objects.get(pk=self.kwargs["pk"])
        context["cliente"] = cliente

        # 🔹 Utilidad acumulada de todas las ventas
        utilidad_acumulada = (
            self.get_queryset().aggregate(total=Sum('utilidad_total'))['total'] or 0
        )
        context["utilidad_acumulada"] = utilidad_acumulada
        return context


    


