from datetime import timedelta
# django
from django.utils import timezone
from django.db import models

from django.db.models import Q, F

class ProductManager(models.Manager):

    def buscar_producto(self, kword=None, order='nombre'):
        consulta = self.filter(
            Q(nombre__icontains=kword) | Q(categoria__nombre__icontains=kword)
        ).exclude(nombre__iexact="ajuste_inicial") if kword else self.all()

        # 🔥 ordenar
        if order == 'fecha':
            return consulta.order_by('-created')  # más recientes primero
        elif order == 'nombre':
            return consulta.order_by('nombre')  # alfabético
        else:
            return consulta.order_by('-created')