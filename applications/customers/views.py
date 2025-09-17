from django.shortcuts import render
from django.core.paginator import Paginator
from django.views.generic import ListView, TemplateView, DetailView

from .models import Cliente
from applications.sales.models import Pago, HistorialSaldo, VentaDetalle

# Create your views here.
class ClienteView(TemplateView):
    template_name='customers/clientes.html'

class ListClientes(ListView):
    context_object_name='lista_clientes'
    template_name='customers/lista_clientes.html'
    paginate_by=10

    def get_queryset(self):
        palabra_clave=self.request.GET.get('kword', '')
        return Cliente.objects.buscar_cliente(palabra_clave)
    
class HistorialVentasCliente(DetailView):
    model = Cliente
    template_name = 'customers/historial_cliente.html'
    context_object_name = 'cliente'
    paginate_by=10

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # obtenemos todas las ventas del cliente
        ventas = self.object.cliente_venta.all().order_by('-Venta_Fecha')

        # paginación
        paginator = Paginator(ventas, self.paginate_by)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # contexto
        context['ultimas_ventas'] = page_obj   # ahora es un Page object
        context['page_obj'] = page_obj
        context['paginator'] = paginator
        context['is_paginated'] = page_obj.has_other_pages()

        return context
    

class HistorialClienteView(ListView):
    model = HistorialSaldo
    template_name = "customers/historial_pagos.html"
    context_object_name = "movimientos"
    paginate_by=10

    
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
    paginate_by=10

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


    


