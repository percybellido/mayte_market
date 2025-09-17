from django.db import models
from datetime import timedelta
# django
from django.utils import timezone

from django.db.models import Sum

from django.db.models import Q, Sum, F, FloatField, ExpressionWrapper

class VentaManagers(models.Manager):

    def listar_ventas(self):
        return self.all()

    def total_ventas(self):
        return self.aggregate(
            total=Sum('amount')
        )['total']
    
    def ventas_en_fecha(self, date_start, date_end):
        return self.filter(
            date_sale__range=(date_start, date_end),
        ).order_by('-date_sale')
    
class VentaDetalleManager(models.Manager):

    def detalle_por_venta(self, id_venta):
        return self.filter(
            sale__id=id_venta
        )

class CarShopManager(models.Manager):

    def total_cobrar(self):
        consulta=self.aggregate(
            total=Sum(
                F('cantidad')*F('producto__precio_venta'),
                output_field=FloatField()
            ),
        )
        if consulta['total']:
            return consulta['total']
        else:
            return 0
        
    def ganancia(self):
        utilidad = self.aggregate(
            total=Sum(
                (F('producto__precio_venta') - F('producto__precio_compra')) * F('cantidad'),
                output_field=FloatField()
            )
        )
        return utilidad['total'] or 0