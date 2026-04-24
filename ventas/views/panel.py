from django.views.generic import ListView, DeleteView, UpdateView
from django.utils.decorators import method_decorator
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView
from ventas.models import Pedido
from ..views.helpers import descontar_stock
from django.contrib import messages
from django.db.models import Sum, Count, F, DecimalField, ExpressionWrapper, Q
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta
import json
from django.http import JsonResponse
from django.db import transaction
from productos.models import Producto
from ventas.models import Pedido, DetallePedido
from ventas.views.helpers import registrar_historial, registrar_log
@method_decorator(staff_member_required, name='dispatch')
class ReportesVentasView(TemplateView):
    template_name = 'ventas/reportes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = timezone.now()
        hace_30_dias = hoy - timedelta(days=30)

        # 1. Filtramos las ventas válidas (Cabeceras)
        ventas_validas = Pedido.objects.filter(
            fecha_pedido__gte=hace_30_dias,
            estado__in=['pagado', 'entregado']
        )

        # 2. Recaudación total: Ahora es MUCHO más rápido porque sumamos directamente el campo 'total' del Pedido
        metricas = ventas_validas.aggregate(
            recaudacion_total=Sum('total'),
            conteo=Count('id')
        )

        total_recaudado = metricas['recaudacion_total'] or 0
        cantidad_ventas = metricas['conteo'] or 0
        ticket_promedio = total_recaudado / cantidad_ventas if cantidad_ventas > 0 else 0

        # 3. Productos más vendidos (Top 5): Ahora tenemos que preguntarle a la tabla de Detalles!
        top_productos = (
            DetallePedido.objects.filter(pedido__estado__in=['pagado', 'entregado'])
            .values('producto__nombre')
            .annotate(total_vendido=Sum('cantidad'))
            .order_by('-total_vendido')[:5]
        )

        # 4. Ventas por método de pago (Esto queda igual porque el método de pago está en la cabecera)
        metodos_pago = (
            ventas_validas
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
class VentaMostradorView(TemplateView):
    template_name = 'ventas/venta_mostrador.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtenemos productos con stock
        productos = Producto.objects.filter(stock__gt=0)
        
        # Formateamos el catálogo en una lista de diccionarios (Data pura)
        catalogo = [
            {
                'id': p.id,
                'nombre': p.nombre,
                'precio': float(p.precio), # Convertimos a float para JS
                'stock': p.stock
            }
            for p in productos
        ]
        
        # Pasamos el catálogo al contexto
        context['catalogo_json'] = catalogo
        return context

    def post(self, request, *args, **kwargs):
        """
        Recibe el "ticket" armado en JavaScript como un paquete JSON
        y guarda la cabecera y sus múltiples detalles.
        """
        try:
            datos = json.loads(request.body)
            items = datos.get('items', [])
            metodo_pago = datos.get('metodo_pago', 'efectivo')

            if not items:
                return JsonResponse({'error': 'El carrito está vacío'}, status=400)

            # transaction.atomic() asegura que si falla el producto 5, 
            # no se guarde ni se descuente el stock de los 4 anteriores.
            with transaction.atomic():
                # 1. Creamos la cabecera (Ticket)
                pedido = Pedido.objects.create(
                    usuario=request.user,  # El cajero queda registrado como dueño
                    metodo_pago=metodo_pago,
                    estado='entregado',    # Venta de mostrador se entrega en el acto
                    total=0
                )
                
                total_calculado = 0

                # 2. Iteramos los renglones del ticket
                for item in items:
                    # select_for_update() bloquea la fila en la DB temporalmente para evitar 
                    # que otra persona compre el mismo producto en el mismo milisegundo
                    producto = Producto.objects.select_for_update().get(id=item['id'])
                    cantidad = int(item['cantidad'])

                    if producto.stock < cantidad:
                        raise ValueError(f"Stock insuficiente para {producto.nombre}")

                    # Descontamos el stock de la base de datos
                    producto.stock -= cantidad
                    producto.save()

                    # Guardamos el renglón
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=producto,
                        cantidad=cantidad,
                        precio_unitario=producto.precio
                    )
                    total_calculado += (producto.precio * cantidad)

                # 3. Cerramos el total de la cabecera
                pedido.total = total_calculado
                pedido.save()

                # Registramos en tus logs
                registrar_historial(pedido, "", "entregado", request.user)
                registrar_log(pedido, request.user, "Venta mostrador (POS múltiple)")

            # Respuesta exitosa para que JavaScript imprima el comprobante
            return JsonResponse({'success': True, 'pedido_id': pedido.id})

        except ValueError as e:
            return JsonResponse({'error': str(e)}, status=400)
        except Exception as e:
            return JsonResponse({'error': 'Error interno al procesar la venta'}, status=500)
    
@method_decorator(staff_member_required, name='dispatch')
class PanelPedidosView(ListView):
    model = Pedido
    template_name = 'ventas/panel_pedidos.html'
    context_object_name = 'pedidos'
    paginate_by = 10

    def get_queryset(self):
        # CAMBIO CLAVE: Cambiamos select_related por prefetch_related para traer los detalles sin ahorcar la base de datos
        qs = Pedido.objects.select_related('usuario').prefetch_related('detalles__producto').all()

        query = self.request.GET.get('q') 
        estado = self.request.GET.get('estado')
        producto = self.request.GET.get('producto')
        usuario = self.request.GET.get('usuario')
        fecha = self.request.GET.get('fecha')

        if query:
            clean_query = query.replace('#', '')
            # Buscamos el nombre del producto DENTRO de los detalles. Usamos distinct() para no duplicar el pedido si tiene varios productos con "cepillo".
            qs = qs.filter(
                Q(detalles__producto__nombre__icontains=query) | 
                Q(id__icontains=clean_query)
            ).distinct()

        # Mantenemos los filtros
        if estado:
            qs = qs.filter(estado=estado)
        if producto:
            qs = qs.filter(detalles__producto__nombre__icontains=producto).distinct()
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
    template_name = 'ventas/ticket_pdf.html' 
    context_object_name = 'pedido'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # El total ya no se calcula multiplicando porque ahora viene guardado en el pedido
        context['total'] = self.object.total
        return context
        