from django.utils import timezone
from datetime import date
from django.db import models
from django.db.models import Sum, F
from .managers import ClienteManager


# Create your models here.
class Cliente(models.Model):
    nombre=models.CharField('Nombre', max_length=50)
    estado=models.SmallIntegerField('Estado', default=1, null=True)
    dni=models.CharField(max_length=10, null=True, blank=True)
    direccion=models.CharField(max_length=100, blank=True)
    telefono=models.CharField(max_length=50, blank=True, null=True)
    email=models.EmailField('Email', null=True, blank=True, )

    saldo = models.DecimalField(default=0, max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objects=ClienteManager()

    
    @property
    def saldo_pendiente(self):
        from django.db.models import Sum
        from applications.sales.models import PagoVenta

        total_ventas = self.cliente_venta.aggregate(total=Sum('Venta_Total'))['total'] or 0

        total_pagado = PagoVenta.objects.filter(
            venta__Venta_CliId=self
        ).aggregate(total=Sum('monto_pagado'))['total'] or 0

        return total_ventas - total_pagado
        
   
    
    def actualizar_saldo(self):
        self.saldo = self.saldo_pendiente
        self.save(update_fields=["saldo"])
        return self.saldo 

    @property
    def dias_vencidos(self):
        """Devuelve los días desde la venta pendiente más antigua"""
        from applications.sales.models import PagoVenta
        hoy = timezone.now().date()

        # Traemos todas las ventas del cliente con su total y lo pagado
        ventas = self.cliente_venta.annotate(
            pagado=Sum('pagos_aplicados__monto_pagado')
        ).filter(
            Venta_Total__gt=F('pagado')  # Solo ventas con deuda
        ).order_by("Venta_Fecha")

        if not ventas.exists():
            return 0

        venta_mas_antigua = ventas.first()
        return (hoy - venta_mas_antigua.Venta_Fecha.date()).days

    @property
    def color_alerta(self):
        """Devuelve clase CSS según los días de vencimiento"""
        dias = self.dias_vencidos
        if dias >= 30:
            return "vencido-rojo"
        elif dias > 15:
            return "vencido-naranja"
        elif dias > 7:
            return "vencido-amarillo"
        return ""

    class Meta:
        verbose_name='Cliente'
        ordering=['nombre']

    def __str__(self):
        return str(self.id) +' - '+self.nombre

