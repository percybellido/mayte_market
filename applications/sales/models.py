from django.db import models
from django.db.models import Sum, F, FloatField
from django.conf import settings
from applications.product.models import Producto
from applications.customers.models import Cliente
from .managers import VentaManagers, CarShopManager

# Create your models here.
class Venta(models.Model):
    Venta_Fecha=models.DateTimeField('Fecha de Venta')
    Venta_CliId=models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='cliente_venta', null=False)
    Venta_cantidad=models.PositiveIntegerField('Cantidad de Producto')
    Venta_NroFact = models.CharField('Número de Boleta', max_length=20, null=True, blank=True)
    Venta_Total=models.DecimalField('Total', max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        verbose_name='cajero',
        related_name="user_venta",
    )

    @property
    def ganancia_total(self):
        """Calcula la utilidad de esta venta a partir de sus detalles"""
        utilidad = self.detalles.aggregate(
            total=Sum(
                (F('VD_Precio') - F('producto__precio_compra')) * F('VD_Cantidad'),
                output_field=FloatField()
            )
        )
        return utilidad['total'] or 0

    objects=VentaManagers()

    class Meta:
        verbose_name='Ventas'
        ordering=['-Venta_CliId']

    def __str__(self):
        return str(self.Venta_CliId)
    
class VentaDetalle(models.Model):
    VD_VentasId=models.ForeignKey(Venta, on_delete=models.CASCADE, related_name="detalles" )
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        verbose_name='producto',
        related_name='product_sale'
    )
    VD_Cantidad = models.DecimalField('Cantidad', max_digits=10, decimal_places=2, default=0)
    VD_Precio=models.DecimalField('Precio Venta', max_digits=10, decimal_places=2)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name='Detalle de Ventas'
        ordering=['VD_VentasId']
        
    @property
    def subtotal(self):
        return self.VD_Cantidad * self.VD_Precio
    
    def __str__(self):
        return str(self.VD_VentasId)+'--'+str(self.VD_Cantidad)+'--'+str(self.VD_Precio)

class MetodosPago(models.Model):
    description=models.CharField('Metodos Pago', max_length=50, null=True)
    status=models.IntegerField(null=True, default=1)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name='Metodos de Pago'

    def __str__(self):
        return self.description

class Pago(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pagos')
    fecha = models.DateTimeField(auto_now_add=True)
    total_pagado = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago = models.ForeignKey(MetodosPago, on_delete=models.SET_NULL, null=True)
    saldo_despues = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # 👈 nuevo campo

    def save(self, *args, **kwargs):
        # Primero actualizamos el saldo del cliente
        nuevo_saldo = self.cliente.saldo_pendiente - self.total_pagado
        # Importante: guardamos el nuevo saldo al cliente
        self.cliente.saldo = nuevo_saldo
        self.cliente.save(update_fields=["saldo"])

        # Ahora asignamos saldo_despues ANTES de guardar el pago
        self.saldo_despues = nuevo_saldo

        # Y recién aquí guardamos el pago
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Pago de {self.cliente} - S/ {self.total_pagado}"

class PagoVenta(models.Model):
    pago = models.ForeignKey(Pago, on_delete=models.CASCADE, related_name='detalle_ventas')
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos_aplicados')
    monto_pagado = models.DecimalField(max_digits=10, decimal_places=2)

    
    class Meta:
        unique_together = ('pago', 'venta')

    def __str__(self):
        return f"S/ {self.monto_pagado} para venta #{self.venta.id}"
    
class HistorialSaldo(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name="historial_saldos")
    fecha = models.DateTimeField(auto_now_add=True)
    saldo = models.DecimalField(max_digits=10, decimal_places=2)
    pago = models.ForeignKey("Pago", on_delete=models.SET_NULL, null=True, blank=True)
    venta = models.ForeignKey("Venta", on_delete=models.SET_NULL, null=True, blank=True)  # 👈 nuevo campo

    def __str__(self):
        return f"{self.cliente.nombre} - Saldo: {self.saldo} ({self.fecha.strftime('%Y-%m-%d %H:%M')})"



class CarShop(models.Model):
    """Modelo que representa a un carrito de compras"""
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        verbose_name='producto',
        related_name='product_car'
    )

    cliente = models.ForeignKey(
    Cliente,
    on_delete=models.CASCADE,
    verbose_name='Cliente',
    null=True,
    blank=True
    )
    cantidad = models.DecimalField(
    max_digits=10,
    decimal_places=2,
    default=0
    )
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    objects=CarShopManager()
    
    class Meta:
        verbose_name = 'Carrito de compras'
        verbose_name_plural = 'Carrito de compras'
        ordering = ['-created']

    def __str__(self):
        return str(self.product.name)
