from django.urls import path
from ventas.views.panel import PanelPedidosView, PedidoDeleteView, PedidoEntregarView, VentaMostradorCreateView,ReportesVentasView, TicketVentaDetailView

urlpatterns = [
    # Listado principal del panel
    path('', PanelPedidosView.as_view(), name='panel_pedidos'),
    path('nueva-venta/', VentaMostradorCreateView.as_view(), name='venta_mostrador'),
    path('reportes/', ReportesVentasView.as_view(), name='reportes_ventas'),
    path('pedido/<int:pk>/ticket/', TicketVentaDetailView.as_view(), name='pedido_ticket'),

    # Acciones sobre pedidos
    path('pedido/<int:pk>/eliminar/', PedidoDeleteView.as_view(), name='pedido_delete'),
    path('pedido/<int:pk>/entregar/', PedidoEntregarView.as_view(), name='pedido_entregar'),
]
