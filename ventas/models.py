from django.db import models
from django.conf import settings
from productos.models import Producto

# -------------------------------
# 📦 1. La Cabecera: Pedido
# -------------------------------
class Pedido(models.Model):
    """
    Representa la transacción global (El ticket de compra).
    Ya no tiene 'producto' ni 'cantidad', eso va en los detalles.
    """
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("pagado", "Pagado"),
        ("enviado", "Enviado"),
        ("entregado", "Entregado"),
        ("cancelado", "Cancelado"),
    ]
    
    # El cliente (puede ser nulo si es una venta rápida de mostrador)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Fechas y control
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")
    
    # CACHÉ DEL TOTAL: Para no saturar la DB sumando los detalles todo el tiempo
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        ordering = ["-fecha_pedido"]

    def __str__(self):
        return f"Pedido #{self.id} - {self.get_estado_display()}"


# -------------------------------
# 📋 2. El Detalle: DetallePedido
# -------------------------------
class DetallePedido(models.Model):
    """
    Representa cada renglón dentro del ticket de compra.
    """
    # related_name='detalles' nos permite hacer: mi_pedido.detalles.all()
    pedido = models.ForeignKey(Pedido, related_name='detalles', on_delete=models.CASCADE)
    
    # PROTECT: Evita que borres un producto de la DB si ya fue vendido alguna vez
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT) 
    
    cantidad = models.PositiveIntegerField(default=1)
    
    # FOTOGRAFÍA DEL PRECIO: Guarda el precio exacto en el momento de la venta.
    # Si el producto sube de precio mañana, este ticket histórico no se altera.
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def subtotal(self):
        # ESCUDO DEFENSIVO: Verificamos que ambos valores existan antes de multiplicar.
        # Si la fila está vacía (None), devolvemos 0 en lugar de romper el programa.
        if self.cantidad is not None and self.precio_unitario is not None:
            return self.cantidad * self.precio_unitario
        return 0

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} (Pedido #{self.pedido.id})"


# -------------------------------
# 🔄 3. Historial y Logs (Mantenemos tu lógica)
# -------------------------------
class HistorialPedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='historial')
    estado_anterior = models.CharField(max_length=20, blank=True)
    estado_nuevo = models.CharField(max_length=20)
    fecha_cambio = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-fecha_cambio"]

class PedidoLog(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='logs')
    accion = models.CharField(max_length=255)
    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-fecha"]


# -------------------------------
# 🛒 4. Carrito de Compras
# -------------------------------
class Carrito(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        # ESCUDO DEFENSIVO CORREGIDO: El carrito lee el precio EN VIVO del producto.
        # Nos aseguramos de que el producto exista y tenga precio antes de multiplicar.
        if self.cantidad is not None and self.producto and self.producto.precio is not None:
            return self.cantidad * self.producto.precio
        return 0