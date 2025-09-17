from applications.customers.models import Cliente

def cliente_en_sesion(request):
    cliente = None
    cliente_id = request.session.get('cliente_id')
    if cliente_id:
        try:
            cliente = Cliente.objects.get(id=cliente_id)
        except Cliente.DoesNotExist:
            cliente = None
    return {
        'cliente_en_sesion': cliente
    }