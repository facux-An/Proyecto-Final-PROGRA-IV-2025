from django.urls import path, include
from .views import PedidoHistorialView


urlpatterns = [
    # Carrito de compras
    path("carrito/", include(("ventas.urls_carrito", "carrito"), namespace="carrito")),
    # Pedidos (listado, detalle, estado, eliminar, entregar, historial)
    path("pedidos/", include(("ventas.urls_pedidos", "pedidos"), namespace="pedidos")),
    path("pedidos/<int:pk>/historial/", PedidoHistorialView.as_view(), name="pedido_historial"),

    # Panel de administración de ventas
    path("panel/", include(("ventas.urls_panel", "panel"), namespace="panel")),

    # Pagos (todas las rutas están centralizadas en urls_pagos.py)
    path("pagos/", include(("ventas.urls_pagos", "pagos"), namespace="pagos")),
]

            