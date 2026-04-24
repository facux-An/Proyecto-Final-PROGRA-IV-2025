# ventas/views/pedidos.py

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from ventas.models import Pedido, HistorialPedido
from ventas.views.helpers import registrar_historial, registrar_log


class PedidoHistorialView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """Historial completo de un pedido (solo staff o dueño del pedido)."""
    model = HistorialPedido
    template_name = "pedidos/historial.html"
    context_object_name = "historial"

    def get_queryset(self):
        return (
            HistorialPedido.objects
            .filter(pedido_id=self.kwargs["pk"])
            .select_related("pedido", "usuario")
            .order_by("-fecha_cambio")
        )

    def test_func(self):
        pedido = get_object_or_404(Pedido, pk=self.kwargs["pk"])
        return self.request.user.is_staff or pedido.usuario_id == self.request.user.id
    

class PedidoDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Pedido
    template_name = "pedidos/pedido_detail.html"
    context_object_name = "pedido"

    def get_queryset(self):
        # CAMBIO CLAVE: select_related para el usuario (1a1), prefetch_related para detalles (1 a Muchos)
        return Pedido.objects.select_related("usuario").prefetch_related("detalles__producto")

    def test_func(self):
        pedido = self.get_object()
        return self.request.user.is_staff or pedido.usuario_id == self.request.user.id

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Detectar si el origen es el panel
        origen = self.request.GET.get("origen")
        context["volver_al_panel"] = origen == "panel"
        return context


class PedidoListView(LoginRequiredMixin, ListView):
    model = Pedido
    template_name = 'pedidos/pedido_list.html'
    context_object_name = 'pedidos'
    paginate_by = 10

    def get_queryset(self):
        # CAMBIO CLAVE: prefetch_related
        qs = Pedido.objects.filter(usuario=self.request.user).prefetch_related('detalles__producto')
        estado = self.request.GET.get('estado')
        producto = self.request.GET.get('producto')

        if estado:
            qs = qs.filter(estado=estado)
        if producto:
            # CAMBIO CLAVE: Filtramos buscando DENTRO de los detalles. Usamos distinct() para que el pedido no aparezca repetido si tiene varios productos con ese nombre.
            qs = qs.filter(detalles__producto__nombre__icontains=producto).distinct()

        return qs.order_by('-fecha_pedido')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        usuario = self.request.user
        estados = ['pendiente', 'pagado', 'enviado', 'entregado', 'cancelado']
        estadisticas = {
            estado: Pedido.objects.filter(usuario=usuario, estado=estado).count()
            for estado in estados
        }

        context.update({
            'total_pedidos': Pedido.objects.filter(usuario=usuario).count(),
            'estadisticas': estadisticas,
            'estados': estados,
            'f_estado': self.request.GET.get('estado', ''),
            'f_producto': self.request.GET.get('producto', ''),
        })
        return context


@method_decorator(staff_member_required, name="dispatch")
class PedidoCreateView(SuccessMessageMixin, CreateView):
    model = Pedido
    fields = ["usuario", "estado"] # Quitamos "producto"
    template_name = "pedidos/pedido_form.html"
    success_url = reverse_lazy("pedidos:list")
    success_message = "✅ Pedido creado correctamente."

    def form_valid(self, form):
        if not form.cleaned_data.get("usuario"):
            form.instance.usuario = self.request.user
        return super().form_valid(form)

class PedidoUpdateView(LoginRequiredMixin, UserPassesTestMixin, SuccessMessageMixin, UpdateView):
    model = Pedido
    fields = ["usuario", "estado"] # Quitamos "producto"
    template_name = "pedidos/pedido_update.html"
    # Redirigir al panel después de guardar
    success_url = reverse_lazy("panel:panel_pedidos")
    success_message = "✏️ Pedido actualizado correctamente."

    def get_queryset(self):
        return Pedido.objects.select_related("producto", "usuario")

    def test_func(self):
        pedido = self.get_object()
        return self.request.user.is_staff or pedido.usuario_id == self.request.user.id


@method_decorator(staff_member_required, name="dispatch")
class PedidoEstadoUpdateView(SuccessMessageMixin, UpdateView):
   
    model = Pedido
    fields = ["estado"]
    template_name = "pedidos/pedido_estado_form.html"
    success_url = reverse_lazy("pedidos:list")
    success_message = "✏️ Estado del pedido actualizado correctamente."

    def form_valid(self, form):
        pedido = form.instance
        estado_anterior = pedido.estado
        with transaction.atomic():
            response = super().form_valid(form)
            registrar_historial(pedido, estado_anterior, pedido.estado, self.request.user)
            registrar_log(pedido, self.request.user, f"estado:{estado_anterior}→{pedido.estado}")
        messages.info(self.request, "🧾 Historial y log registrados.")
        return response


@staff_member_required
def eliminar_pedido(request, pk):
    """
    Elimina un pedido y registra log (solo staff).
    """
    pedido = get_object_or_404(Pedido, pk=pk)
    with transaction.atomic():
        registrar_log(pedido, request.user, "eliminado")
        pedido.delete()
    messages.success(request, f"🗑️ Pedido #{pk} eliminado correctamente.")
    return redirect("panel:panel_pedidos")


@staff_member_required
def marcar_como_entregado(request, pk):
    """
    Marca un pedido como entregado y registra historial/log (solo staff).
    Valida stock antes de confirmar la entrega.
    """
    pedido = get_object_or_404(Pedido, pk=pk)

    if pedido.estado == "entregado":
        messages.info(request, f"ℹ️ El pedido #{pedido.id} ya estaba entregado.")
        return redirect("panel:panel_pedidos")

    if pedido.producto.stock < pedido.cantidad:
        messages.error(request, f"❌ No hay stock suficiente para entregar el pedido #{pedido.id}.")
        return redirect("panel:panel_pedidos")

    with transaction.atomic():
        # CAMBIO CLAVE: Bucle para descontar stock de todos los productos del pedido
        for detalle in pedido.detalles.all():
            detalle.producto.stock -= detalle.cantidad
            detalle.producto.save()

        # Registrar historial y log
        registrar_historial(pedido, pedido.estado, "entregado", request.user)
        registrar_log(pedido, request.user, "entregado")

        # Actualizar estado
        pedido.estado = "entregado"
        pedido.save()

    messages.success(request, f"✅ Pedido #{pedido.id} marcado como entregado correctamente.")
    return redirect("panel:panel_pedidos")
