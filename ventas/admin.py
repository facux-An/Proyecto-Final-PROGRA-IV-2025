from django.contrib import admin
from .models import Pedido, DetallePedido, Carrito, ItemCarrito, HistorialPedido, PedidoLog

# 1. Creamos el "Inline" para los renglones del ticket
class DetallePedidoInline(admin.TabularInline):
    model = DetallePedido
    extra = 0  # No muestra filas vacías extra por defecto
    readonly_fields = ['subtotal'] # El subtotal lo calcula el modelo, no se edita
    autocomplete_fields = ['producto'] # Para buscar productos rápido

# 2. Registramos el Pedido (La cabecera)
@admin.register(Pedido)
class PedidoAdmin(admin.ModelAdmin):
    # Quitamos 'producto', 'cantidad' y 'precio_unitario' porque ahora están en el Inline
    list_display = (
        "id",
        "usuario",
        "total",
        "metodo_pago",
        "estado",
        "fecha_pedido",
        "fecha_entrega",
    )
    list_filter = ("estado", "metodo_pago", "fecha_pedido", "fecha_entrega")
    search_fields = ("usuario__username", "metodo_pago") 
    autocomplete_fields = ["usuario"]
    
    # ¡Acá conectamos la cabecera con el detalle!
    inlines = [DetallePedidoInline]

# El resto queda exactamente igual a tu código
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