from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, View, DeleteView, DetailView, TemplateView
from django.views.generic.edit import FormView
from django.db.models import F, Sum
from django.contrib import messages
from applications.customers.models import Cliente
from applications.product.models import Producto
from applications.users.mixins import VentasPermisoMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.utils.timezone import now

from .models import Venta, VentaDetalle, CarShop, PagoVenta, Pago
from .forms import VentaForm, PagoForm, AbonoForm
from .functions import procesar_venta

from .functions import registrar_pago

from django.db import transaction

class AddCarView(VentasPermisoMixin, FormView):
    template_name = 'sales/index.html'
    form_class = VentaForm
    success_url = '.'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Si ya hay cliente en sesión, quitamos el campo del formulario
        if 'cliente_id' in self.request.session:
            form.fields.pop('cliente', None)
        return form

    def get_context_data(self, **kwargs):
       
        context = super().get_context_data(**kwargs)
        productos = CarShop.objects.all()
        context["productos"] = productos
        context["total_cobrar"] = CarShop.objects.total_cobrar()
        context["ganancia"] = CarShop.objects.ganancia()
        # Si hay cliente en sesión, mostrarlo
        cliente_id = self.request.session.get('cliente_id')
        context["cliente"] = Cliente.objects.get(id=cliente_id) if cliente_id else None
        return context
    
    def form_valid(self, form):
        if 'cliente_id' not in self.request.session:
            # Obtener cliente desde el formulario y guardarlo en la sesión
            cliente = form.cleaned_data['cliente']
            self.request.session['cliente_id'] = cliente.id
        else:
            # Si ya está en sesión, recuperarlo de la base de datos
            cliente_id = self.request.session['cliente_id']
            cliente = Cliente.objects.get(id=cliente_id)
        producto = form.cleaned_data['producto']
        cantidad = form.cleaned_data['cantidad']

        # Guardar cliente en sesión si no existe
        if 'cliente_id' not in self.request.session:
            self.request.session['cliente_id'] = cliente.id

        # Obtener cliente desde la sesión
        cliente_id = self.request.session['cliente_id']
        cliente = Cliente.objects.get(id=cliente_id)

        obj, created = CarShop.objects.get_or_create(
            producto=producto,
            cliente=cliente,
            defaults={
                'cantidad': cantidad,
            }
        )
        #
        if not created:
            obj.cantidad = obj.cantidad + cantidad
            obj.save()
        return super(AddCarView, self).form_valid(form)
    
class CarShopAddView(VentasPermisoMixin, View):
    """ aumenta en 1 la cantidad en un carshop """

    def post(self, request, *args, **kwargs):
        pk = self.kwargs.get('pk')

        updated = CarShop.objects.filter(id=pk).update(cantidad=F('cantidad') + 1)

        if not updated:
            messages.error(request, "Producto no encontrado en el carrito.")

        return HttpResponseRedirect(reverse('venta_app:venta-index'))
    
class CarShopUpdateView(VentasPermisoMixin, View):
    """ quita en 1 la cantidad en un carshop """

    def post(self, request, *args, **kwargs):
        car = CarShop.objects.get(id=self.kwargs['pk'])
        if car.cantidad > 1:
            car.cantidad = car.cantidad - 1
            car.save()
        #
        return HttpResponseRedirect(
            reverse(
                'venta_app:venta-index'
            )
        )

class CarShopDeleteView(VentasPermisoMixin, DeleteView):
    model = CarShop
    success_url = reverse_lazy('venta_app:venta-index')

class CarShopDeleteAll(VentasPermisoMixin, View):
    
    def post(self, request, *args, **kwargs):
        #
        CarShop.objects.all().delete()
        #

        self.request.session.pop('cliente_id', None)

        return HttpResponseRedirect(
            reverse(
                'venta_app:venta-index'
            )
        )

class ProcesoVentaSimpleView(VentasPermisoMixin, View):
    """ Procesa una venta simple """

    def post(self, request, *args, **kwargs):
        cliente = request.POST.get('cliente_id')  # El id del cliente debe venir en el POST
        if not cliente:
            return HttpResponseRedirect(reverse('venta_app:venta-index'))
        #
        procesar_venta(
            self=self,
            user=self.request.user,
        )
        #
        return HttpResponseRedirect(
            reverse(
                'venta_app:venta-index'
            )
        )


def ventas(request):
    return render(request, 'sales/ventas.html')

class ListVentas(ListView):
    context_object_name='lista_ventas'
    template_name='sales/lista_ventas.html'
    paginate_by=8
    ordering=['Venta_Fecha']

    def get_queryset(self):
        return Venta.objects.listar_ventas()
    
class RegistrarPagoView(FormView):
    template_name = 'sales/registrar_pago.html'
    form_class = PagoForm
    success_url = reverse_lazy('venta_app:lista-ventas')

    def form_valid(self, form):
        registrar_pago(
            cliente=form.cleaned_data['cliente'],
            total_pagado=form.cleaned_data['total_pagado'],
            metodo_pago=form.cleaned_data['metodo_pago']
        )
        return super().form_valid(form)
    
class RegistrarAbonoView(FormView):
    template_name = 'sales/registrar_abono.html'
    form_class = AbonoForm
    success_url = reverse_lazy('venta_app:venta-index')

    def form_valid(self, form):
        cliente = form.cleaned_data['cliente']
        monto = form.cleaned_data['monto']
        metodo_pago = form.cleaned_data['metodo_pago']
        print("Cliente recibido:", form.cleaned_data.get("cliente"))
        print("Método pago recibido:", form.cleaned_data.get("metodo_pago"))
        print("Monto:", form.cleaned_data.get("monto"))

        with transaction.atomic():
            pago = Pago.objects.create(
                cliente=cliente,
                total_pagado=monto,
                metodo_pago=metodo_pago
            )

            ventas_pendientes = Venta.objects.filter(Venta_CliId=cliente)

            monto_restante = monto
            for venta in ventas_pendientes:
                total_venta = venta.Venta_Total
                pagado = venta.pagos_aplicados.aggregate(total=Sum('monto_pagado'))['total'] or 0
                saldo = total_venta - pagado
                if saldo <= 0:
                    continue
                abono = min(saldo, monto_restante)
                if abono > 0:
                    PagoVenta.objects.create(pago=pago, venta=venta, monto_pagado=abono)
                    monto_restante -= abono
                if monto_restante <= 0:
                    break
            cliente.actualizar_saldo()
            
        return super().form_valid(form)
    
class ConfirmarVentaView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            return redirect('venta_app:venta-index')  # Redirigir si no hay cliente

        cliente = Cliente.objects.get(id=cliente_id)
        carrito = CarShop.objects.filter(cliente=cliente)

        if not carrito.exists():
            return redirect('venta_app:venta-index')  # Redirigir si el carrito está vacío

        with transaction.atomic():
            # Calcular totales
            total_venta = sum(item.producto.precio_venta * item.cantidad for item in carrito)
            cantidad_total = sum(item.cantidad for item in carrito)

            # Crear la venta
            venta = Venta.objects.create(
                Venta_Fecha=now(),
                Venta_CliId=cliente,
                Venta_cantidad=cantidad_total,
                Venta_Total=total_venta,
                user=request.user  # usuario cajero
            )

        # Crear los detalles
        for item in carrito:
            VentaDetalle.objects.create(
                VD_VentasId=venta,
                producto=item.producto,
                VD_Cantidad=item.cantidad,
                VD_Precio=item.producto.precio_venta
            )

        # Limpiar el carrito
        carrito.delete()

        # Limpiar la sesión del cliente
        del request.session['cliente_id']

        return redirect('venta_app:venta-detalle', pk=venta.pk)  # Redirigir a página principal
    



class VentaDetailView(DetailView):
    model = Venta
    template_name = "sales/venta_detalle.html"
    context_object_name = "venta"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        venta = self.get_object()
        context["detalles"] = venta.detalles.all()  # relacionados por related_name en VentaDetalle
        return context






    
