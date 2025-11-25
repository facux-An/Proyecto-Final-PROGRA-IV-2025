from django.views.generic import ListView, DeleteView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy

from ventas.models import Pedido


@method_decorator(staff_member_required, name='dispatch')
class PanelPedidosView(ListView):
    """
    Panel de pedidos para staff con filtros y métricas rápidas.
    """
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

        # Estados disponibles
        estados = ['pendiente', 'pagado', 'enviado', 'entregado', 'cancelado']

        # Estadísticas globales
        estadisticas = {
            estado: Pedido.objects.filter(estado=estado).count()
            for estado in estados
        }

        context.update({
            'total_pedidos': Pedido.objects.count(),
            'estadisticas': estadisticas,
            # Filtros activos (para mantener valores en el formulario)
            'f_estado': self.request.GET.get('estado', ''),
            'f_producto': self.request.GET.get('producto', ''),
            'f_usuario': self.request.GET.get('usuario', ''),
            'f_fecha': self.request.GET.get('fecha', ''),
            'estados': estados,
        })
        return context


@method_decorator(staff_member_required, name='dispatch')
class PedidoDeleteView(DeleteView):
    """
    Eliminar un pedido desde el panel (solo staff).
    """
    model = Pedido
    template_name = 'pedidos/pedido_confirm_delete.html'
    success_url = reverse_lazy('panel:panel_pedidos')


@method_decorator(staff_member_required, name='dispatch')
class PedidoEntregarView(UpdateView):
    """
    Confirmar entrega de un pedido desde el panel (solo staff).
    """
    model = Pedido
    fields = []  # no mostramos formulario
    template_name = 'pedidos/pedido_entregar.html'
    success_url = reverse_lazy('panel:panel_pedidos')

    def form_valid(self, form):
        self.object.estado = 'entregado'
        self.object.save()
        return super().form_valid(form)
