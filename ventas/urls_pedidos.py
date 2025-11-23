# ventas/urls_pedidos.py

from django.urls import path
from ventas.views.pedidos import (
    PedidoListView,
    PedidoDetailView,
    PedidoCreateView,
    PedidoUpdateView,
    PedidoEstadoUpdateView,
    PedidoHistorialView,
    eliminar_pedido,
    marcar_como_entregado,
)

app_name = "pedidos"

urlpatterns = [
    # Listado de pedidos del usuario autenticado
    path("", PedidoListView.as_view(), name="list"),

    # Detalle de un pedido individual
    path("<int:pk>/", PedidoDetailView.as_view(), name="detail"),

    # Crear un pedido (solo staff)
    path("crear/", PedidoCreateView.as_view(), name="create"),

    # Editar un pedido existente
    path("<int:pk>/editar/", PedidoUpdateView.as_view(), name="update"),

    # Actualizar estado de un pedido (solo staff)
    path("<int:pk>/estado/", PedidoEstadoUpdateView.as_view(), name="estado_update"),

    # Ver historial de cambios de un pedido
    path("<int:pk>/historial/", PedidoHistorialView.as_view(), name="historial"),

    # Eliminar un pedido (solo staff)
    path("<int:pk>/eliminar/", eliminar_pedido, name="delete"),

    # Marcar pedido como entregado (solo staff)
    path("<int:pk>/entregar/", marcar_como_entregado, name="deliver"),
]
