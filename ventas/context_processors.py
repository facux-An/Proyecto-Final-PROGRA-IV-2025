from django.core.cache import cache
from .models import Carrito


def carrito_count(request):
    """
    Retorna la cantidad de items en el carrito del usuario.
    
    Optimización: El resultado se guarda en el caché de memoria por 60 segundos.
    Esto evita hacer una query a Neon en cada página que carga (home, catálogo,
    detalle de producto, etc.). El caché se invalida explícitamente cuando el
    usuario agrega o quita productos del carrito.
    """
    if not request.user.is_authenticated:
        return {'carrito_count': 0}

    cache_key = f"carrito_count_user_{request.user.id}"
    count = cache.get(cache_key)

    if count is None:
        # Solo tocamos la DB si el caché está vacío (primera vez o expiró)
        from django.db.models import Sum
        resultado = Carrito.objects.filter(usuario=request.user).aggregate(
            total=Sum('items__cantidad')
        )
        count = resultado['total'] or 0
        # Guardar en caché por 60 segundos
        cache.set(cache_key, count, 60)

    return {'carrito_count': count}