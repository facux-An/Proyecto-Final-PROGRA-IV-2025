from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from categorias.models import Categoria
from .models import Producto, PortadaProducto
from .forms import ProductoForm, ProductoPortadaForm, PortadasMultiplesForm
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import ProtectedError
import traceback


class ProductoListView(ListView):
    model = Producto
    template_name = 'productos/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 5

    def get_queryset(self):
        queryset = Producto.objects.select_related('categoria').prefetch_related('portadas')

        categoria_id = self.request.GET.get('categoria')
        search = self.request.GET.get('search')
        min_precio = self.request.GET.get('min_precio')
        max_precio = self.request.GET.get('max_precio')
        stock_min = self.request.GET.get('stock_min')

        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
        if search:
            queryset = queryset.filter(nombre__icontains=search)
        if min_precio:
            queryset = queryset.filter(precio__gte=min_precio)
        if max_precio:
            queryset = queryset.filter(precio__lte=max_precio)
        if stock_min:
            queryset = queryset.filter(stock__gte=stock_min)

        sort = self.request.GET.get('sort')
        if sort == 'precio_asc':
            queryset = queryset.order_by('precio')
        elif sort == 'precio_desc':
            queryset = queryset.order_by('-precio')
        elif sort == 'nuevos':
            queryset = queryset.order_by('-id')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        context['categoria_id'] = self.request.GET.get('categoria', '')
        context['search'] = self.request.GET.get('search', '')
        context['min_precio'] = self.request.GET.get('min_precio', '')
        context['max_precio'] = self.request.GET.get('max_precio', '')
        context['stock_min'] = self.request.GET.get('stock_min', '')
        context['sort'] = self.request.GET.get('sort', '')
        return context


class ProductoDetailView(DetailView):
    model = Producto
    template_name = 'productos/producto_detail.html'
    context_object_name = 'producto'

    def get_queryset(self):
        return (
            Producto.objects
            .select_related('categoria')
            .prefetch_related('portadas')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        producto = self.object  # ya viene con portadas prefetch

        if producto.categoria:
            relacionados_qs = (
                Producto.objects.filter(categoria=producto.categoria)
                .exclude(id=producto.id)
                .select_related('categoria')
                .prefetch_related('portadas')
                .order_by('-id')[:4]
            )
            context['relacionados'] = relacionados_qs
        else:
            context['relacionados'] = []

        context['portadas'] = producto.portadas.all()
        context['portadas_count'] = len(list(producto.portadas.all()))  # list() usa el prefetch cache
        return context


class ProductoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'productos/producto_form.html'
    success_url = reverse_lazy('productos:producto_list')
    permission_required = 'productos.add_producto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['portadas_form'] = PortadasMultiplesForm(self.request.POST or None, self.request.FILES or None)
        return context

    def form_valid(self, form):
        self.object = form.save()
        files = self.request.FILES.getlist("portadas")
        for f in files[:5]:
            PortadaProducto.objects.create(producto=self.object, imagen=f)
        messages.success(self.request, "✅ Producto creado correctamente con portadas.")
        return super().form_valid(form)


class ProductoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Producto
    form_class = ProductoForm
    template_name = 'productos/producto_form.html'
    success_url = reverse_lazy('productos:producto_list')
    permission_required = 'productos.change_producto'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['portadas_form'] = PortadasMultiplesForm(self.request.POST or None, self.request.FILES or None)
        return context

    def form_valid(self, form):
        self.object = form.save()
        files = self.request.FILES.getlist("portadas")

        if files:
            # Calcular cuántos lugares quedan para no superar las 5 portadas
            current_count = self.object.portadas.count()
            slots_left = max(0, 5 - current_count)
            
            for f in files[:slots_left]:
                PortadaProducto.objects.create(producto=self.object, imagen=f)

        messages.info(self.request, "✨ Producto actualizado correctamente.")
        return super().form_valid(form)


class ProductoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Producto
    template_name = 'productos/producto_confirm_delete.html'
    success_url = reverse_lazy('productos:producto_list')
    permission_required = 'productos.delete_producto'

    def delete(self, request, *args, **kwargs):
        try:
            response = super().delete(request, *args, **kwargs)
            messages.warning(self.request, "🗑️ Producto eliminado correctamente.")
            return response
        except ProtectedError:
            messages.error(self.request, "❌ No se puede eliminar este producto porque está asociado a ventas históricas. Para ocultarlo, dejá su stock en 0.")
            return redirect('productos:producto_list')


def subir_portada(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    if request.method == "POST":
        form = ProductoPortadaForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                img = form.cleaned_data["portada"]
                producto.portada = img
                producto.save()
                messages.success(request, "✅ Portada actualizada correctamente.")
                print("[Upload] Portada subida OK:", producto.portada.url if producto.portada else "(sin url)")
                return redirect("productos:producto_detail", pk=producto.id)
            except Exception as e:
                print("[Upload] Error al guardar portada:", str(e))
                traceback.print_exc()
                messages.error(request, "❌ No se pudo subir la imagen. Intentalo de nuevo.")
        else:
            messages.error(request, "❌ Imagen inválida: " + "; ".join([str(err) for err in form.errors.get("portada", [])]))
    else:
        form = ProductoPortadaForm()
    return render(request, "productos/subir_portada.html", {"form": form, "producto": producto})

@staff_member_required
@require_POST
def toggle_destacado(request, pk):
    producto = get_object_or_404(Producto, pk=pk)
    producto.destacado = not producto.destacado
    producto.save()
    status = "destacado" if producto.destacado else "removido de la vitrina"
    messages.success(request, f"⭐ Producto '{producto.nombre}' {status}.")
    return redirect(request.META.get('HTTP_REFERER', 'productos:producto_list'))

import json
from django.http import JsonResponse
from django.db import transaction


@staff_member_required
@require_POST
def eliminar_portada(request, portada_id):
    '''
    Elimina una PortadaProducto especifica por su ID.
    No permite borrar si es la unica imagen del producto.
    Responde JSON para actualizacion sin recarga de pagina.
    '''
    portada = get_object_or_404(PortadaProducto, id=portada_id)
    producto = portada.producto
    if producto.portadas.count() <= 1:
        return JsonResponse({'ok': False, 'error': 'No podes eliminar la unica imagen del producto.'}, status=400)
    portada.delete()
    return JsonResponse({'ok': True, 'portadas_restantes': producto.portadas.count()})


@staff_member_required
@require_POST
def reordenar_portadas(request, producto_id):
    '''
    Recibe una lista de IDs de PortadaProducto y actualiza su campo 'orden'.
    El payload debe ser JSON: {"orden_ids": [34, 32, 35]}
    '''
    producto = get_object_or_404(Producto, id=producto_id)
    try:
        data = json.loads(request.body)
        orden_ids = data.get('orden_ids', [])
        
        if not isinstance(orden_ids, list):
            return JsonResponse({'ok': False, 'error': 'Formato inválido.'}, status=400)

        # Usar una transacción para asegurar integridad
        with transaction.atomic():
            for index, p_id in enumerate(orden_ids):
                # Usar update para no emitir señales innecesarias, o save() si es necesario
                # Para ser seguros, verificamos que la portada pertenezca al producto
                PortadaProducto.objects.filter(id=p_id, producto=producto).update(orden=index)
                
            # Las portadas que no se enviaron quedarán con su orden actual,
            # pero típicamente el frontend envía todas.
            
        return JsonResponse({'ok': True, 'mensaje': 'Orden guardado correctamente.'})
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'Payload inválido.'}, status=400)
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=500)
