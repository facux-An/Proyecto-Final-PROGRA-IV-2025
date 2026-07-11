from django.contrib import admin
from .models import (
    Pedido, DetallePedido, Carrito, ItemCarrito,
    HistorialPedido, PedidoLog, ConfiguracionTienda,
)


# ────────────────────────────────────────────
# ⚙️ Configuración de la Tienda (Singleton)
# ────────────────────────────────────────────
@admin.register(ConfiguracionTienda)
class ConfiguracionTiendaAdmin(admin.ModelAdmin):
    """
    Admin singleton: no permite crear ni borrar.
    Si no existe, lo crea automáticamente al entrar.
    """
    fieldsets = (
        ('🚚 Envío Gratis — Barra de progreso en el Carrito', {
            'fields': (
                'envio_gratis_activo',
                'envio_gratis_umbral',
                'envio_gratis_mensaje',
                'envio_gratis_mensaje_logrado',
            ),
            'description': (
                'Configurá la promoción de envío gratis. El cliente ve una barra de progreso '
                'en el carrito que se va llenando hasta alcanzar el monto mínimo.'
            ),
        }),
    )

    def has_add_permission(self, request):
        # Solo puede existir 1 registro
        return not ConfiguracionTienda.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        # Si no existe, crearlo y redirigir directo a editar
        obj = ConfiguracionTienda.get()
        from django.shortcuts import redirect
        return redirect(f'/admin/ventas/configuraciontienda/{obj.pk}/change/')

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
        "cupon_aplicado",
        "descuento_aplicado",
        "metodo_pago",
        "estado",
        "fecha_pedido",
        "fecha_entrega",
    )
    list_filter = ("estado", "metodo_pago", "fecha_pedido", "fecha_entrega")
    search_fields = ("usuario__username", "metodo_pago") 
    autocomplete_fields = ["usuario"]
    readonly_fields = ("cupon_aplicado", "descuento_aplicado")
    
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