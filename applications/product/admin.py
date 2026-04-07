from django.contrib import admin
from .models import Producto, Categoria

# Register your models here.
@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display=('nombre', 'precio_compra', 'cantidad')
    list_editable=('precio_compra', 'cantidad')

    search_fields=('nombre',)
    list_filter=('categoria',)
    ordering=('nombre',)


admin.site.register(Categoria)