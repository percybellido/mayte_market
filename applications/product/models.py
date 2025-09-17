import uuid
from django.db import models
from django.utils.text import slugify

from .managers import ProductManager


class Categoria(models.Model):
    nombre = models.CharField('Categoría', max_length=100, unique=True)
    slug = models.SlugField(blank=True, unique=True, null=True)  # 🔹 por ahora sin unique
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorias'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            self.slug = base_slug or str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    UNIT_CHOICES = (
        ('0', 'Kilogramos'),
        ('1', 'Litros'),
        ('2', 'Unidades'),
    )

    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    nombre = models.CharField('Nombre', max_length=40)
    descripcion = models.TextField('Descripcion del producto', blank=True)
    unidad = models.CharField('Unidad de medida', max_length=1, choices=UNIT_CHOICES)
    cantidad = models.PositiveBigIntegerField('Cantidad en Almacen', default=0)
    precio_compra = models.DecimalField('Precio de Compra', max_digits=7, decimal_places=2)
    slug = models.SlugField(blank=True, unique=True, null=True)  # 🔹 por ahora sin unique
    precio_venta = models.DecimalField('Precio de Venta', max_digits=7, decimal_places=2)
    image = models.ImageField(upload_to='uploads/product/', null=True, blank=True)

    visible_en_tienda = models.BooleanField(default=True)
    # Campos para etiquetas
    disponible = models.BooleanField(default=True, verbose_name="¿Disponible?")
    es_nuevo = models.BooleanField(default=False, verbose_name="¿Nuevo?")
    en_oferta = models.BooleanField(default=False, verbose_name="¿En oferta?")
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    objects = ProductManager()

    class Meta:
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.nombre)
            # 🔹 aseguramos slug único usando UUID en caso de duplicados
            self.slug = base_slug or str(uuid.uuid4())
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.nombre}"

    
