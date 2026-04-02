from .models import Carrito

def carrito_count(request):
    if request.user.is_authenticated:
        carrito = Carrito.objects.filter(usuario=request.user).first()
        if carrito:
            # Sumamos las cantidades, no solo las filas
            total_items = sum(item.cantidad for item in carrito.items.all())
            return {'carrito_count': total_items}
    return {'carrito_count': 0}