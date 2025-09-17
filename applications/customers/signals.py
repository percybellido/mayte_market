from django.db.models.signals import post_save
from django.dispatch import receiver
from applications.sales.models import Venta, PagoVenta, Pago, HistorialSaldo


# Cada vez que se crea un Pago
@receiver(post_save, sender=Pago)
def registrar_historial_pago(sender, instance, created, **kwargs):
    if created:
        print("✅ Signal de Pago ejecutado para:", instance)
        HistorialSaldo.objects.create(
            cliente=instance.cliente,
            fecha=instance.fecha,
            saldo=instance.saldo_despues,
            pago=instance
            # El saldo ya se calculó en Pago.save()
        )

# Cada vez que se crea una Venta
@receiver(post_save, sender=Venta)
def registrar_historial_venta(sender, instance, created, **kwargs):
    if created:
        # aquí usamos el saldo_pendiente del cliente
        cliente = instance.Venta_CliId
        saldo_actual = cliente.saldo_pendiente
        cliente.saldo = saldo_actual
        cliente.save(update_fields=["saldo"])

        HistorialSaldo.objects.create(
            cliente=cliente,
            fecha=instance.Venta_Fecha,
            saldo=saldo_actual,
            venta=instance
        )
