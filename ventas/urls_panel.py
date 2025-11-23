from django.urls import path
from ventas.views.panel import PanelPedidosView

app_name = 'panel'

urlpatterns = [
    path('', PanelPedidosView.as_view(), name='panel_pedidos'),
]
