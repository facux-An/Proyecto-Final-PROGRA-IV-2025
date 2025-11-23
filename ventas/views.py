from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView,DetailView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Pedido, Carrito, ItemCarrito, PedidoLog, HistorialPedido
from productos.models import Producto


class PedidoListView(ListView):
    """Listado de pedidos del usuario autenticado, con filtros por estado y producto."""
    model = Pedido
    template_name = "pedidos/pedido_list.html"
    context_object_name = "pedidos"
    paginate_by = 5

    def get_queryset(self):
        estado = self.request.GET.get("estado")
        producto = self.request.GET.get("producto")

        queryset = Pedido.objects.filter(usuario=self.request.user)
        if estado:
            queryset = queryset.filter(estado=estado)
        if producto:
            queryset = queryset.filter(producto__nombre__icontains=producto)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        context.update({
            "total_pedidos": Pedido.objects.filter(usuario=usuario).count(),
            "pendientes": Pedido.objects.filter(usuario=usuario, estado="pendiente").count(),
            "entregados": Pedido.objects.filter(usuario=usuario, estado="entregado").count(),
        })
        return context


@method_decorator(staff_member_required, name='dispatch')
class PedidoCreateView(SuccessMessageMixin, CreateView):
    """Creación de pedidos (solo staff)."""
    model = Pedido
    fields = ['producto', 'usuario', 'estado']
    template_name = 'pedidos/pedido_form.html'
    success_url = reverse_lazy('pedidos:create')
    success_message = "✅ Pedido creado correctamente."

    def form_valid(self, form):
        if not form.cleaned_data.get('usuario'):
            form.instance.usuario = self.request.user
        return super().form_valid(form)


@staff_member_required
def eliminar_pedido(request, pk):
    """Elimina un pedido y registra log."""
    pedido = get_object_or_404(Pedido, pk=pk)
    PedidoLog.objects.create(pedido=pedido, usuario=request.user, accion="eliminado")
    pedido.delete()
    messages.success(request, f"🗑️ Pedido #{pk} eliminado correctamente.")
    return redirect('panel:panel_pedidos')


@login_required
def ver_carrito(request):
    """Muestra el carrito del usuario."""
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    return render(request, 'ventas/carrito.html', {'carrito': carrito})


@login_required
def agregar_al_carrito(request, producto_id):
    """Agrega un producto al carrito."""
    if request.method != "POST":
        messages.warning(request, "Para agregar al carrito usá el botón correspondiente.")
        return redirect('productos:producto_list')

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    producto = get_object_or_404(Producto, id=producto_id)

    if producto.stock < 1:
        messages.error(request, "❌ No hay stock disponible.")
        return redirect('productos:producto_list')

    item, creado = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
    if not creado:
        item.cantidad += 1
        item.save()

    messages.success(request, f"✅ {producto.nombre} agregado al carrito.")
    return redirect('carrito:carrito_detail')


@login_required
def eliminar_item(request, item_id):
    """Elimina un producto del carrito."""
    if request.method != "POST":
        messages.warning(request, "Para eliminar un producto usá el botón correspondiente.")
        return redirect('carrito:carrito_detail')

    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
    item.delete()
    messages.warning(request, "🗑️ Producto eliminado del carrito.")
    return redirect('carrito:carrito_detail')


@login_required
def finalizar_compra(request):
    """Convierte el carrito en pedidos y ajusta stock."""
    if request.method != "POST":
        messages.warning(request, "Para finalizar la compra usá el botón correspondiente.")
        return redirect('carrito:carrito_detail')

    carrito = get_object_or_404(Carrito, usuario=request.user)

    if not carrito.items.exists():
        messages.warning(request, "Tu carrito está vacío.")
        return redirect('carrito:carrito_detail')

    for item in carrito.items.select_related('producto'):
        Pedido.objects.create(
            producto=item.producto,
            usuario=request.user,
            cantidad=item.cantidad
        )
        item.producto.stock -= item.cantidad
        item.producto.save()

    carrito.items.all().delete()

    messages.success(request, "✅ Compra realizada con éxito. Tus productos fueron registrados como pedidos.")
    return redirect('pedidos:list')


@method_decorator(staff_member_required, name='dispatch')
class PanelPedidosView(ListView):
    """Panel de administración de pedidos con filtros y estadísticas."""
    model = Pedido
    template_name = 'ventas/panel_pedidos.html'
    context_object_name = 'pedidos'
    paginate_by = 10

    def get_queryset(self):
        qs = Pedido.objects.select_related('producto', 'usuario')
        estado = self.request.GET.get('estado')
        producto = self.request.GET.get('producto')
        usuario = self.request.GET.get('usuario')
        fecha = self.request.GET.get('fecha')

        if estado:
            qs = qs.filter(estado=estado)
        if producto:
            qs = qs.filter(producto__nombre__icontains=producto)
        if usuario:
            qs = qs.filter(usuario__username__icontains=usuario)
        if fecha:
            qs = qs.filter(fecha_pedido__date=fecha)

        return qs.order_by('-fecha_pedido')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        estados = ['pendiente', 'entregado', 'pagado', 'enviado', 'cancelado']
        context.update({
            'total_pedidos': Pedido.objects.count(),
            'estadisticas': {estado: Pedido.objects.filter(estado=estado).count() for estado in estados},
            'f_estado': self.request.GET.get('estado', ''),
            'f_producto': self.request.GET.get('producto', ''),
            'f_usuario': self.request.GET.get('usuario', ''),
            'f_fecha': self.request.GET.get('fecha', ''),
            'estados': estados,
        })
        return context


@method_decorator(staff_member_required, name='dispatch')
class PedidoEstadoUpdateView(UpdateView):
    """Actualiza el estado de un pedido y registra historial."""
    model = Pedido
    fields = ['estado']
    template_name = 'pedidos/pedido_estado_form.html'
    success_url = reverse_lazy('pedidos:list')

    def form_valid(self, form):
        pedido = form.instance
        estado_anterior = pedido.estado
        response = super().form_valid(form)
        HistorialPedido.objects.create(
            pedido=pedido,
            estado_anterior=estado_anterior,
            estado_nuevo=pedido.estado,
            usuario=self.request.user
        )
        messages.info(self.request, "✏️ Estado del pedido actualizado y registrado en historial.")
        return response



class VerHistorialPedidoView(ListView):
    """Historial completo de un pedido (staff)."""
    model = HistorialPedido
    template_name = 'ventas/historial_pedido.html'
    context_object_name = 'historial'

    def get_queryset(self):
        return HistorialPedido.objects.filter(
            pedido_id=self.kwargs['pk']
        ).order_by('-fecha_cambio')


class HistorialUsuarioView(LoginRequiredMixin, ListView):
    """Historial de un pedido visible solo para su usuario dueño."""
    model = HistorialPedido
    template_name = 'ventas/historial_usuario.html'
    context_object_name = 'historial'

    def get_queryset(self):
        return HistorialPedido.objects.filter(
            pedido_id=self.kwargs['pk'],
            pedido__usuario=self.request.user
        ).order_by('-fecha_cambio')


@login_required
def finalizar_compra(request):
    """Convierte el carrito en pedidos, valida stock y ajusta inventario."""
    if request.method != "POST":
        messages.warning(request, "Usá el botón para finalizar la compra.")
        return redirect('carrito:carrito_detail')

    carrito = Carrito.objects.filter(usuario=request.user).first()
    if not carrito:
        messages.error(request, "El carrito está vacío.")
        return redirect('carrito:carrito_detail')

    items = ItemCarrito.objects.filter(carrito=carrito)
    if not items.exists():
        messages.error(request, "El carrito está vacío.")
        return redirect('carrito:carrito_detail')

    # Validar stock
    for item in items.select_related('producto'):
        if item.producto.stock < item.cantidad:
            messages.error(
                request,
                f"No hay stock suficiente para {item.producto.nombre}. Disponible: {item.producto.stock}"
            )
            return redirect('carrito:carrito_detail')

    # Crear pedidos y descontar stock
    for item in items:
        producto = item.producto
        Pedido.objects.create(
            producto=producto,
            usuario=request.user,
            precio_unitario=producto.precio,
            cantidad=item.cantidad,
            estado='pendiente'
        )
        producto.stock -= item.cantidad
        producto.save()

    items.delete()
    messages.success(request, "✅ Compra finalizada con éxito.")
    return redirect('pedidos:list')


