from django.contrib import admin
from .models import Pedido, Carrito, ItemCarrito, HistorialPedido, PedidoLog


@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    """
    Configuración del modelo Pedido en el admin.
    Muestra información clave y permite filtrar/buscar fácilmente.
    """
    list_display = (
        "id",
        "producto",
        "usuario",
        "cantidad",
        "precio_unitario",
        "total",
        "metodo_pago",
        "estado",
        "fecha_pedido",
        "fecha_entrega",
    )
    list_filter = ("estado", "metodo_pago", "fecha_pedido", "fecha_entrega")
    search_fields = ("producto__nombre", "usuario__username", "metodo_pago")
    autocomplete_fields = ["producto", "usuario"]

    def total(self, obj):
        """Muestra el total calculado en el admin."""
        return obj.total
    total.short_description = "Total"


@admin.register(Carrito)
class CarritoAdmin(admin.ModelAdmin):
    list_display = ("id", "usuario", "total")
    search_fields = ("usuario__username",)


@admin.register(ItemCarrito)
class ItemCarritoAdmin(admin.ModelAdmin):
    list_display = ("id", "carrito", "producto", "cantidad", "subtotal")
    search_fields = ("producto__nombre", "carrito__usuario__username")


@admin.register(HistorialPedido)
class HistorialPedidoAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "estado_anterior", "estado_nuevo", "usuario", "fecha_cambio")
    list_filter = ("estado_nuevo", "fecha_cambio")
    search_fields = ("pedido__id", "usuario__username")


@admin.register(PedidoLog)
class PedidoLogAdmin(admin.ModelAdmin):
    list_display = ("id", "pedido", "accion", "usuario", "fecha")
    list_filter = ("accion", "fecha")
    search_fields = ("pedido__id", "usuario__username", "accion")
