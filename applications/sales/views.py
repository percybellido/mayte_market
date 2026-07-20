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

from .models import Venta, VentaDetalle, CarShop, PagoVenta, Pago, HistorialSaldo
from .forms import VentaForm, PagoForm, AbonoForm
from .functions import procesar_venta, ganancia_total_por_dia, ganancias_ultimos_dias
from decimal import Decimal, ROUND_HALF_UP
from .functions import registrar_pago
import json
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

        cliente_id = self.request.session.get('cliente_id')
        if cliente_id:
            productos = CarShop.objects.filter(
                cliente_id=cliente_id,
                user=self.request.user
            ).select_related('producto')
        else:
            productos = CarShop.objects.none()

        context["productos"] = productos
        context["stock_json"] = json.dumps([
            {
                "id": p["id"],
                "cantidad": float(p["cantidad"])  # 🔥 aquí está la clave
            }
            for p in Producto.objects.values("id", "cantidad")
        ])
        context["total_cobrar"] = productos.total_cobrar()
        context["ganancia"] = productos.ganancia()
        # Si hay cliente en sesión, mostrarlo
        
        context["cliente"] = Cliente.objects.filter(id=cliente_id).first() if cliente_id else None
        return context
    
    def form_valid(self, form):
        cliente_id = self.request.session.get('cliente_id')

        # 🔹 Si NO hay cliente en sesión
        if not cliente_id:
            cliente = form.cleaned_data.get('cliente')

            if not cliente:
                messages.error(self.request, "Debe seleccionar un cliente")

                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    context = self.get_context_data()
                    context['form'] = form
                    return render(self.request, 'sales/partials/carrito.html', context)

                return self.form_invalid(form)

            # 🔥 GUARDAR EN SESIÓN (ESTO TE FALTABA)
            self.request.session['cliente_id'] = cliente.id

        else:
            cliente = Cliente.objects.get(id=cliente_id)

        # 🔹 Datos del producto
        producto = form.cleaned_data['producto']
        cantidad = form.cleaned_data['cantidad']
        precio_unitario = form.cleaned_data.get('precio_unitario') or producto.precio_venta

        # 🔹 Crear o actualizar carrito
        obj, created = CarShop.objects.get_or_create(
            producto=producto,
            cliente=cliente,
            user=self.request.user,
            defaults={
                'cantidad': cantidad,
                'precio': precio_unitario,
            }
        )

        if not created:
            nueva_cantidad = obj.cantidad + cantidad

            if nueva_cantidad > producto.cantidad:
                messages.error(
                    self.request,
                    f"Stock insuficiente. Disponible: {producto.cantidad}"
                )

                if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    context = self.get_context_data()
                    context['form'] = self.form_class()
                    return render(self.request, 'sales/partials/carrito.html', context)

                return self.form_invalid(form)

            obj.cantidad = nueva_cantidad
            obj.precio = precio_unitario
            obj.save()

        # 🔹 Respuesta AJAX
        if self.request.headers.get('x-requested-with') == 'XMLHttpRequest':
            context = self.get_context_data()
            context['form'] = self.form_class()
            return render(self.request, 'sales/partials/carrito.html', context)

        return super().form_valid(form)
    
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

    def post(self, request, *args, **kwargs):
        print("se esta usando proceso simple")
        cliente_id = request.POST.get('cliente_id')

        if not cliente_id:
            messages.error(request, "Debe seleccionar un cliente")
            return HttpResponseRedirect(reverse('venta_app:venta-index'))

        try:
            procesar_venta(
                user=request.user,
                cliente_id=cliente_id
            )
            messages.success(request, "Venta realizada correctamente")

        except ValueError as e:
            messages.error(request, str(e))

        return HttpResponseRedirect(
            reverse('venta_app:venta-index')
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
    success_url = reverse_lazy('cliente_app:lista-clientes')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cliente_id = self.kwargs.get('cliente_id')

        if cliente_id:
            context['cliente_seleccionado'] = Cliente.objects.get(id=cliente_id)

        return context
    
    def get_initial(self):
        initial = super().get_initial()
        cliente_id = self.kwargs.get('cliente_id')

        if cliente_id:
            initial['cliente'] = Cliente.objects.get(id=cliente_id)

        return initial

    def form_valid(self, form):
        cliente_id = self.kwargs.get('cliente_id')
        cliente = (
            Cliente.objects.get(id=cliente_id)
            if cliente_id
            else form.cleaned_data['cliente']
        )

        monto = form.cleaned_data['monto']
        metodo_pago = form.cleaned_data['metodo_pago']

        with transaction.atomic():
            pago = Pago.objects.create(
                cliente=cliente,
                total_pagado=monto,
                metodo_pago=metodo_pago
            )

            monto_restante = Decimal(monto)

            ventas_pendientes = (
                Venta.objects.activas()
                .filter(Venta_CliId=cliente)
                .annotate(
                    total_pagado=Sum('pagos_aplicados__monto_pagado')
                )
                .order_by("Venta_Fecha")
            )

            for venta in ventas_pendientes:

                total_pagado_venta = (venta.total_pagado or Decimal("0.00")).quantize(Decimal("0.01"))

                saldo_venta = (venta.Venta_Total - total_pagado_venta).quantize(Decimal("0.01"))

                             


                if saldo_venta <= 0:
                    continue

                abono = min(saldo_venta, monto_restante)

                abono = abono.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                PagoVenta.objects.create(
                    pago=pago,
                    venta=venta,
                    monto_pagado=abono
                )

                monto_restante = (monto_restante - abono).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

                if monto_restante <= 0:
                    break

            cliente.actualizar_saldo()

            HistorialSaldo.objects.create(
                cliente=cliente,
                saldo=cliente.saldo,
                pago=pago
            )
            pago.saldo_despues = cliente.saldo
            pago.save(update_fields=["saldo_despues"])

        return super().form_valid(form)
    
class ConfirmarVentaView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        cliente_id = request.session.get('cliente_id')
        if not cliente_id:
            return redirect('venta_app:venta-index')  # Redirigir si no hay cliente

        
        try:
            with transaction.atomic():
                venta=procesar_venta(
                    user=request.user,
                    cliente_id=cliente_id
                )

                cliente=Cliente.objects.get(id=cliente_id)
            
                # 3. AHORA sí actualizar saldo
                cliente.actualizar_saldo()

                # 4. Guardar historial
                HistorialSaldo.objects.create(
                    cliente=cliente,
                    saldo=cliente.saldo,
                    venta=venta
                )

        except ValueError as e:
            messages.error(request, str(e))
            return redirect('venta_app:venta-index')

        # Limpiar la sesión del cliente
        del request.session['cliente_id']

        
        request.session.modified = True  # 🔥 fuerza persistencia

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
    
class VentaDeleteView(VentasPermisoMixin, DeleteView):
    template_name = "sales/delete.html"
    model = Venta
    success_url = reverse_lazy('venta_app:venta-index')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.anulate = True
        self.object.save()
        # actualizmos sl stok y ventas
        VentaDetalle.objects.restablecer_stock_num_ventas(self.object.id)
        success_url = self.get_success_url()

        return HttpResponseRedirect(success_url)
    
class GananciasUltimosDiasView(TemplateView):
    template_name = "sales/ganancias_ultimos_dias.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['ganancias'] = ganancias_ultimos_dias(7)
        return context

class SaldoTotalView(TemplateView):
    template_name = "sales/saldo_total.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["saldo_global"] = Cliente.objects.aggregate(total=Sum("saldo"))["total"] or 0
        return ctx



    
