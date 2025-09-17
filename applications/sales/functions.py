from django.utils import timezone
from applications.customers.models import Cliente
from datetime import datetime
from django.db.models import Sum
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

def procesar_venta(self, **params_venta):

    # recupera la lista de productos en el carrito
    productos_en_car=CarShop.objects.all()

    if productos_en_car.exists() > 0:

        #Crea el objeto venta
        cliente=Cliente.objects.get(id=params_venta['cliente_id'])

        venta=Venta.objects.create(
            Venta_Fecha=timezone.now(),
            Venta_CliId=cliente,
            Venta_cantidad=0,
            Venta_NroFact=generar_nro_factura(),
            Venta_Total=0,
        )

        ventas_detalle=[]
        total=0
        productos_en_venta=[]
        cantidad_total=0

        for producto_car in productos_en_car:
            subtotal=producto_car.cantidad*producto_car.precio_venta
            venta_detalle=VentaDetalle(
                producto=producto_car.producto,
                venta=producto_car.VD_VentasId,
                cantidad=producto_car.VD_Cantidad,
                precio_venta=producto_car.precio_venta
            )
            producto=producto_car.producto
            ventas_detalle.append(venta_detalle)
            productos_en_venta.append(producto)
        venta.save()
        VentaDetalle.objects.bulk_create(ventas_detalle)
        #Completada la vente, eliminamos productos del Carrito
        productos_en_car.delete()
        return venta
    else:
        return None
    
def registrar_pago(cliente, total_pagado, metodo_pago):
    ventas_pendientes = Venta.objects.filter(
        Venta_CliId=cliente
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