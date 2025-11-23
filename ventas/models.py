from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from productos.models import Producto


class Pedido(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    fecha_pedido = models.DateTimeField(auto_now_add=True)
    fecha_entrega = models.DateField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    cantidad = models.PositiveIntegerField(default=1)

    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("pagado", "Pagado"),
        ("enviado", "Enviado"),
        ("entregado", "Entregado"),
        ("cancelado", "Cancelado"),
    ]
    estado = models.CharField(max_length=20, choices=ESTADOS, default="pendiente")

    class Meta:
        ordering = ["-fecha_pedido"]  # siempre mostrar pedidos más recientes primero

    def save(self, *args, **kwargs):
        """
        Al crear un pedido nuevo, se guarda el precio unitario del producto.
        La validación de stock se hace en el formulario (forms.py).
        El stock se descuenta recién al marcar el pedido como entregado.
        """
        if not self.pk:  # solo al crear
            self.precio_unitario = self.producto.precio
        super().save(*args, **kwargs)

    @property
    def total(self):
        """Devuelve el total del pedido (precio unitario × cantidad)."""
        return (self.precio_unitario or 0) * (self.cantidad or 0)

    def __str__(self):
        return f"Pedido #{self.id} - {self.producto.nombre} x{self.cantidad} ({self.usuario}) - {self.estado}"


# -------------------------------
# 🛒 Modelos para el carrito
# -------------------------------
class Carrito(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    @property
    def total(self):
        """Devuelve el total del carrito sumando subtotales de cada item."""
        return sum(item.subtotal for item in self.items.all())


class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        """Subtotal = precio del producto × cantidad."""
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"


# -------------------------------
# 📜 Historial y Logs de pedidos
# -------------------------------
class HistorialPedido(models.Model):
    pedido = models.ForeignKey("Pedido", on_delete=models.CASCADE, related_name="historial")
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.pedido.id}: {self.estado_anterior} → {self.estado_nuevo}"


class PedidoLog(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name="logs")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=50)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pedido} - {self.accion} por {self.usuario}"
