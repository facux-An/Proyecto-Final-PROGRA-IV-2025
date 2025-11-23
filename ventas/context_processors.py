from .models import Carrito

def carrito_count(request):
    if request.user.is_authenticated:
        try:
            carrito = Carrito.objects.get(usuario=request.user)
            return {'carrito_count': carrito.items.count()}
        except Carrito.DoesNotExist:
            return {'carrito_count': 0}
    return {'carrito_count': 0}
