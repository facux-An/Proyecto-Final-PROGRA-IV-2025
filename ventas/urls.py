from django.urls import path, include
from ventas.views import pagos
from .views import PedidoHistorialView
from ventas.views import carrito

urlpatterns = [
    # Carrito de compras
    path("carrito/", include(("ventas.urls_carrito", "carrito"), namespace="carrito")),
    # Pedidos (listado, detalle, estado, eliminar, entregar, historial)
    path("pedidos/", include(("ventas.urls_pedidos", "pedidos"), namespace="pedidos")),
    path("pedidos/<int:pk>/historial/", PedidoHistorialView.as_view(), name="pedido_historial"),

    # Panel de administración de ventas
    path("panel/", include(("ventas.urls_panel", "panel"), namespace="panel")),

    # Pagos
    path("pagos/", include(("ventas.urls_pagos", "pagos"), namespace="pagos")),
    path("metodo/", pagos.MetodoPagoView.as_view(), name="metodo"),
    path("confirmacion/", pagos.ConfirmacionPagoView.as_view(), name="confirmacion"),
    path("error/", pagos.ConfirmacionPagoView.as_view(template_name="pagos/error.html"), name="error"),
    path("pendiente/", pagos.ConfirmacionPagoView.as_view(template_name="pagos/pendiente.html"), name="pendiente"),
    path("webhook/", pagos.mercado_pago_webhook, name="webhook"),
]
            