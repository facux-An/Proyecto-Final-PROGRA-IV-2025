from django.db.models import Sum
from .models import Carrito

def carrito_count(request):
    if request.user.is_authenticated:
        # Hacemos una agregación directa en la DB. Es mucho más rápido.
        resultado = Carrito.objects.filter(usuario=request.user).aggregate(total=Sum('items__cantidad'))
        return {'carrito_count': resultado['total'] or 0}
    return {'carrito_count': 0}