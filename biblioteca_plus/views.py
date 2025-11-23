from django.shortcuts import redirect, render
from django.contrib.auth import logout
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count
from productos.models import Producto
from categorias.models import Categoria
from django.contrib.auth.forms import UserCreationForm
from django.http import JsonResponse
from django.urls import get_resolver

def home(request):
    productos_qs = Producto.objects.select_related('categoria').order_by('id')
    paginator = Paginator(productos_qs, 10)
    page_number = request.GET.get('page')
    productos = paginator.get_page(page_number)

    categorias = (
        Categoria.objects
        .annotate(num_productos=Count('productos'))
        .order_by('nombre')
    )

    context = {
        'productos': productos,
        'categorias': categorias,
    }
    return render(request, 'home.html', context)

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
    # Recorrer url_patterns y coleccionar namespaces únicos
    namespaces = set()

    def collect(patterns):
        for p in patterns:
            # include(...) genera URLResolver con atributo namespace
            if hasattr(p, 'url_patterns'):
                if getattr(p, 'namespace', None):
                    namespaces.add(p.namespace)
                collect(p.url_patterns)

    collect(resolver.url_patterns)
    return JsonResponse({'namespaces': sorted(list(namespaces))})