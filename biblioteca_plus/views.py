from django.shortcuts import redirect, render
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from django.core.cache import cache
from productos.models import Producto
from categorias.models import Categoria
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse, HttpResponse
from django.urls import get_resolver


def health_check(request):
    """
    Endpoint ultra-ligero para UptimeRobot.
    Retorna un simple texto plano 'OK' para confirmar que Render está vivo.
    IMPORTANTE: No realiza consultas a la base de datos para no gastar horas de Neon.
    """
    return HttpResponse("OK")


def home(request):
    """
    Vista de la página de inicio (Landing Page).
    
    Optimización: Los productos se cachean en memoria por 10 minutos (600s).
    La home es la página más visitada y sus datos no cambian con frecuencia.
    Cuando un admin modifica un producto, el caché expira solo y se recarga.
    
    El caché NO se comparte entre usuarios autenticados y anónimos para
    evitar mostrar datos incorrectos en la barra de admin.
    """
    # Clave de caché diferente para staff (ven la barra de admin) vs visitantes
    is_staff = request.user.is_authenticated and request.user.is_staff
    cache_key = "home_data_staff" if is_staff else "home_data_public"

    home_data = cache.get(cache_key)

    if home_data is None:
        # Cache MISS: consultamos Neon y guardamos el resultado
        productos_destacados = list(
            Producto.objects.filter(destacado=True)
            .select_related('categoria')
            .prefetch_related('portadas')[:4]
        )

        kits_combo = list(
            Producto.objects.filter(es_combo=True, en_oferta=True)
            .select_related('categoria')
            .prefetch_related('portadas')[:5]
        )

        productos_oferta = list(
            Producto.objects.filter(en_oferta=True, es_combo=False)
            .select_related('categoria')
            .prefetch_related('portadas')[:8]
        )

        productos_carrusel = list(
            Producto.objects.filter(en_carrusel=True)
            .select_related('categoria')
            .prefetch_related('portadas')[:5]
        )

        home_data = {
            'productos_destacados': productos_destacados,
            'kits_combo': kits_combo,
            'productos_oferta': productos_oferta,
            'productos_carrusel': productos_carrusel,
        }

        # Guardar en caché por 10 minutos
        cache.set(cache_key, home_data, 600)

    return render(request, 'home.html', home_data)


def cerrar_sesion(request):
    logout(request)
    messages.info(request, "Sesión cerrada correctamente.")
    return render(request, 'logout.html')


def registro(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Usuario registrado correctamente.")
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'registro.html', {'form': form})


def debug_namespaces(request):
    resolver = get_resolver()
    namespaces = set()

    def collect(patterns):
        for p in patterns:
            if hasattr(p, 'url_patterns'):
                if getattr(p, 'namespace', None):
                    namespaces.add(p.namespace)
                collect(p.url_patterns)

    collect(resolver.url_patterns)
    return JsonResponse({'namespaces': sorted(list(namespaces))})