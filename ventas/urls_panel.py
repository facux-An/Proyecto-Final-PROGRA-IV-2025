from django.urls import path
from ventas.views.panel import PanelPedidosView, PedidoDeleteView, PedidoEntregarView

app_name = 'panel'

urlpatterns = [
    # Listado principal del panel
    path('', PanelPedidosView.as_view(), name='panel_pedidos'),

    # Acciones sobre pedidos
    path('pedido/<int:pk>/eliminar/', PedidoDeleteView.as_view(), name='pedido_delete'),
    path('pedido/<int:pk>/entregar/', PedidoEntregarView.as_view(), name='pedido_entregar'),
]
