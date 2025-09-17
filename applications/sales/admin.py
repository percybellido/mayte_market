from django.contrib import admin
from .models import Venta, VentaDetalle, MetodosPago, CarShop

admin.site.register(Venta)
admin.site.register(VentaDetalle)
admin.site.register(MetodosPago)
admin.site.register(CarShop)