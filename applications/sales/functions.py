from django.utils import timezone
from datetime import timedelta
from applications.customers.models import Cliente
from datetime import datetime
from django.db.models import Sum, DecimalField, F
from applications.product.models import Producto

from .models import Venta, VentaDetalle, CarShop, Pago, PagoVenta

from django.db import transaction

def generar_nro_factura():
    hoy = datetime.now()
    año = hoy.year
    mes = hoy.month
    prefijo = f"{año}-{mes:05d}"
    
    ultima = Venta.objects.filter(Venta_NroFact__startswith=prefijo).order_by('Venta_NroFact').last()

    if ultima and ultima.Venta_NroFact:
        try:
            ultimo_num = int(ultima.Venta_NroFact.split('-')[-1])
        except (ValueError, IndexError):
            ultimo_num = 0
        nuevo_num = ultimo_num + 1
    else:
        nuevo_num = 1

    return f"{prefijo}-{nuevo_num:06d}"

def aplicar_saldo_a_favor(cliente, venta):
    """
    Aplica el saldo a favor del cliente como pago automático.
    """
    saldo = cliente.saldo_pendiente   # puede ser negativo

    if saldo >= 0:
        return  # no hay saldo a favor

    saldo_a_favor = abs(saldo)

    
    monto_a_usar = min(saldo_a_favor, venta.Venta_Total)

    PagoVenta.objects.create(
        venta=venta,
        monto_pagado=monto_a_usar,
        descripcion="Aplicación automática de saldo a favor"
    )

    cliente.actualizar_saldo()

from django.db import transaction
from django.db.models import F
from django.utils import timezone


def procesar_venta(user, cliente_id):
    from decimal import Decimal
    
    # 🔹 carrito SOLO del usuario actual
    productos_en_car = CarShop.objects.select_related('producto').filter(
    user=user, 
    cliente_id=cliente_id)

    if not productos_en_car.exists():
        raise ValueError("El carrito esta vacio")

    with transaction.atomic():

        cliente = Cliente.objects.get(id=cliente_id)

        # 🔥 1. VALIDAR STOCK ANTES DE TODO
        for item in productos_en_car:
            if item.cantidad > item.producto.cantidad:
                raise ValueError(
                    f"Stock insuficiente para {item.producto.nombre}"
                )

        venta = Venta.objects.create(
            Venta_Fecha=timezone.now(),
            Venta_CliId=cliente,
            Venta_cantidad=0,
            Venta_NroFact=generar_nro_factura(),
            Venta_Total=0,
            user=user,
            status='confirmed'  # opcional, pero recomendado
        )

        ventas_detalle = []
        total = 0
        cantidad_total = 0

        for item in productos_en_car:
            producto = item.producto
            cantidad_item = Decimal(str(item.cantidad))
            updated = Producto.objects.filter(
                id=producto.id,
                cantidad__gte=item.cantidad
            ).update(
                cantidad=F('cantidad') - cantidad_item
            )
            

            if updated == 0:
                raise ValueError(f"Stock insuficiente para {producto.nombre}")

            subtotal = item.cantidad * item.precio

            ventas_detalle.append(
                VentaDetalle(
                    VD_VentasId=venta,
                    producto=producto,
                    VD_Cantidad=item.cantidad,
                    VD_Precio=item.precio,
                    VD_precio_compra=producto.precio_compra
                )
            )

            total += subtotal
            cantidad_total += item.cantidad

        # 🔹 guardar detalles en lote
        VentaDetalle.objects.bulk_create(ventas_detalle)

        # 🔹 actualizar totales
        venta.Venta_Total = total
        venta.Venta_cantidad = cantidad_total
        venta.save()

        # 🔹 limpiar carrito SOLO de este usuario
        productos_en_car.delete()

        return venta
    
def registrar_pago(cliente, total_pagado, metodo_pago):
    ventas_pendientes = Venta.objects.filter(
        Venta_CliId=cliente,
        status='confirmed'
    ).order_by('Venta_Fecha')

    with transaction.atomic():
        pago = Pago.objects.create(
            cliente=cliente,
            total_pagado=total_pagado,
            metodo_pago=metodo_pago
        )
        
        restante = total_pagado
        for venta in ventas_pendientes:
            total_pagado_en_venta = venta.pagos_aplicados.aggregate(total=Sum('monto_pagado'))['total'] or 0
            saldo = venta.Venta_Total - total_pagado_en_venta

            if saldo <= 0:
                continue

            abono = min(restante, saldo)
            PagoVenta.objects.create(
                pago=pago,
                venta=venta,
                monto_pagado=abono
            )

            restante -= abono
            if restante <= 0:
                break


        cliente.actualizar_saldo()
    
def ganancia_total_por_dia(fecha):

    utilidad = VentaDetalle.objects.filter(
        VD_VentasId__Venta_Fecha__date=fecha,
        VD_VentasId__status='confirmed'
    ).aggregate(
        total=Sum(
            (F('VD_Precio') - F('VD_precio_compra')) * F('VD_Cantidad'),
            output_field=DecimalField(max_digits=12, decimal_places=2)
        )
    )['total'] or 0

    return utilidad

def ganancias_ultimos_dias(dias=7):
    """Devuelve una lista con la ganancia de los últimos 'dias' días."""
    hoy = timezone.now().date()
    datos = []

    for i in range(dias):
        fecha = hoy - timedelta(days=i)
        utilidad = ganancia_total_por_dia(fecha)
        datos.append({
            'fecha': fecha,
            'ganancia': utilidad
        })

    return datos[::-1] 

