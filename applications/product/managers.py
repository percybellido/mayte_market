from datetime import timedelta
# django
from django.utils import timezone
from django.db import models

from django.db.models import Q, F

class ProductManager(models.Manager):

    def buscar_producto(self, kword, order):
        consulta = self.filter(
            Q(nombre__icontains=kword) | Q(categoria__nombre__icontains=kword)
        ).exclude(nombre__iexact="ajuste_inicial")  # 🚫 excluir ese producto
        # verificamos en que orden se solicita
        if order == 'fecha':
            # ordenar por fecha
            return consulta.order_by('created')
        elif order == 'nombre':
            # ordenar por nombre
            return consulta.order_by('nombre')
        else:
            return consulta.order_by('-created')