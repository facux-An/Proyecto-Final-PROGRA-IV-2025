from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from categorias.models import Categoria
from .models import Producto, PortadaProducto
from .forms import ProductoForm, ProductoPortadaForm, PortadasMultiplesForm
from django.shortcuts import get_object_or_404, redirect, render
import traceback


class ProductoListView(ListView):
    model = Producto
    template_name = 'productos/producto_list.html'
    context_object_name = 'productos'
    paginate_by = 5

    def get_queryset(self):
        queryset = Producto.objects.select_related('categoria').all()
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

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.all()
        context['categoria_id'] = self.request.GET.get('categoria', '')
        context['search'] = self.request.GET.get('search', '')
        context['min_precio'] = self.request.GET.get('min_precio', '')
        context['max_precio'] = self.request.GET.get('max_precio', '')
        context['stock_min'] = self.request.GET.get('stock_min', '')
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
        context['relacionados'] = (
            Producto.objects.filter(categoria=producto.categoria)
            .exclude(id=producto.id)
            .order_by('-id')[:4]
        ) if producto.categoria else []
        context['portadas'] = producto.portadas.all()
        context['portadas_count'] = producto.portadas.count()
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
        for f in files[:5]:
            PortadaProducto.objects.create(producto=self.object, imagen=f)
        messages.info(self.request, "✏️ Producto actualizado correctamente. Portadas agregadas si se subieron nuevas.")
        return super().form_valid(form)


class ProductoDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Producto
    template_name = 'productos/producto_confirm_delete.html'
    success_url = reverse_lazy('productos:producto_list')
    permission_required = 'productos.delete_producto'

    def delete(self, request, *args, **kwargs):
        messages.warning(self.request, "🗑️ Producto eliminado correctamente.")
        return super().delete(request, *args, **kwargs)


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
