from django.db import models


class ClienteManager(models.Manager):

    def buscar_cliente(self, kword):
        resultado=self.filter(
            nombre__icontains=kword
        )
        return resultado
