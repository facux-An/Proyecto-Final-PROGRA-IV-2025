from django.views.generic import ListView, DeleteView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView
from ventas.models import Pedido
from ..forms import VentaPresencialForm
from ..views.helpers import descontar_stock
from django.contrib import messages
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper, Q
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta

@method_decorator(staff_member_required, name='dispatch')
class ReportesVentasView(TemplateView):
    template_name = 'ventas/reportes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now()
        hace_30_dias = hoy - timedelta(days=30)

        # 1. Filtramos las ventas válidas
        ventas_validas = Pedido.objects.filter(
            fecha_pedido__gte=hace_30_dias,
            estado__in=['pagado', 'entregado']
        )

        # 2. Calculamos el total de cada pedido (cantidad * precio_unitario) y luego sumamos todo
        # Usamos F() para referenciar campos de la base de datos
        metricas = ventas_validas.annotate(
            subtotal_db=ExpressionWrapper(
                F('cantidad') * F('precio_unitario'), 
                output_field=DecimalField()
            )
        ).aggregate(
            recaudacion_total=Sum('subtotal_db'),
            conteo=Count('id')
        )

        total_recaudado = metricas['recaudacion_total'] or 0
        cantidad_ventas = metricas['conteo'] or 0
        ticket_promedio = total_recaudado / cantidad_ventas if cantidad_ventas > 0 else 0

        # 3. Productos más vendidos (Top 5)
        top_productos = (
            Pedido.objects.filter(estado__in=['pagado', 'entregado'])
            .values('producto__nombre')
            .annotate(total_vendido=Sum('cantidad'))
            .order_by('-total_vendido')[:5]
        )

        # 4. Ventas por método de pago
        metodos_pago = (
            Pedido.objects.filter(estado__in=['pagado', 'entregado'])
            .values('metodo_pago')
            .annotate(count=Count('id'))
        )

        context.update({
            'total_recaudado': total_recaudado,
            'cantidad_ventas': cantidad_ventas,
            'ticket_promedio': ticket_promedio,
            'top_productos': top_productos,
            'metodos_pago': metodos_pago,
            'rango': "Últimos 30 días"
        })
        return context

@method_decorator(staff_member_required, name='dispatch')
class VentaMostradorCreateView(CreateView):
    model = Pedido
    form_class = VentaPresencialForm
    template_name = 'ventas/venta_mostrador.html'
    success_url = reverse_lazy('panel:panel_pedidos')

    def form_valid(self, form):
        pedido = form.save(commit=False)
        producto = pedido.producto
        
        # 1. Validación de Stock (Antes de intentar guardar)
        if producto.stock < pedido.cantidad:
            messages.error(
                self.request, 
                f"❌ Stock insuficiente. Solo quedan {producto.stock} unidades de {producto.nombre}."
            )
            return self.form_invalid(form)

        # 2. Asignar datos automáticos
        pedido.usuario = self.request.user
        pedido.estado = 'entregado'  # Al ser entregado, el save() del modelo descontará el stock
        
        # 3. Guardar (El método save() que modificamos en el paso anterior hace el resto)
        pedido.save()
        
        messages.success(self.request, f"✅ Venta exitosa: {producto.nombre} x{pedido.cantidad}")
        return super().form_valid(form)
    
@method_decorator(staff_member_required, name='dispatch')
class PanelPedidosView(ListView):
    """
    Panel de pedidos para staff con filtros avanzados, 
    busqueda global y métricas rápidas.
    """
    model = Pedido
    template_name = 'ventas/panel_pedidos.html'
    context_object_name = 'pedidos'
    paginate_by = 10

    def get_queryset(self):
        # Usamos select_related para evitar el problema de N+1 consultas
        qs = Pedido.objects.select_related('producto', 'usuario').all()

        # Captura de parámetros
        query = self.request.GET.get('q') # Buscador general (el nuevo)
        estado = self.request.GET.get('estado')
        producto = self.request.GET.get('producto')
        usuario = self.request.GET.get('usuario')
        fecha = self.request.GET.get('fecha')

        # 1. Lógica del Buscador General (por ID o Producto)
        if query:
            clean_query = query.replace('#', '')
            qs = qs.filter(
                Q(producto__nombre__icontains=query) | 
                Q(id__icontains=clean_query)
            )

        # 2. Mantener Filtros Específicos (por si se usan en conjunto)
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

        # Definición de estados para el negocio
        estados_lista = ['pendiente', 'pagado', 'enviado', 'entregado', 'cancelado']

        # Estadísticas globales (usando la lista para consistencia)
        # Optimizamos contando sobre el modelo directamente
        estadisticas = {
            est: Pedido.objects.filter(estado=est).count()
            for est in estados_lista
        }

        context.update({
            'total_pedidos': Pedido.objects.count(),
            'estadisticas': estadisticas,
            'estados': estados_lista,
            
            # Variables de retorno para persistencia en el template
            'f_estado': self.request.GET.get('estado', ''),
            'f_producto': self.request.GET.get('producto', ''),
            'f_usuario': self.request.GET.get('usuario', ''),
            'f_fecha': self.request.GET.get('fecha', ''),
            'q': self.request.GET.get('q', ''), # Retornamos la búsqueda actual
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
    
@method_decorator(staff_member_required, name='dispatch')
class TicketVentaDetailView(DetailView):
    model = Pedido
    template_name = 'ventas/ticket_pdf.html' # Un diseño limpio para imprimir
    context_object_name = 'pedido'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Calculamos el total aquí para asegurar precisión en el ticket
        context['total'] = self.object.cantidad * self.object.precio_unitario
        return context
        