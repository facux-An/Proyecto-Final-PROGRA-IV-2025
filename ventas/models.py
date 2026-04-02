from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from productos.models import Producto

# -------------------------------
# 📜 1. Historial y Logs (Deben ir PRIMERO para ser usados por Pedido)
# -------------------------------
class HistorialPedido(models.Model):
    pedido = models.ForeignKey("Pedido", on_delete=models.CASCADE, related_name="historial")
    estado_anterior = models.CharField(max_length=20)
    estado_nuevo = models.CharField(max_length=20)
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_cambio = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pedido {self.pedido.id}: {self.estado_anterior} -> {self.estado_nuevo}"

class PedidoLog(models.Model):
    pedido = models.ForeignKey("Pedido", on_delete=models.CASCADE, related_name="logs")
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=50)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.pedido} - {self.accion} por {self.usuario}"


# -------------------------------
# 📦 2. Modelo Principal: Pedido
# -------------------------------
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
        ordering = ["-fecha_pedido"]

    def save(self, *args, **kwargs):
        # Detectar si es un pedido nuevo antes de guardar
        is_new = self._state.adding
        estado_anterior = ""
        
        if not is_new:
            # Si ya existe, recuperamos el estado anterior para comparar
            original = Pedido.objects.get(pk=self.pk)
            estado_anterior = original.estado
        else:
            # Si es nuevo, asignamos el precio del producto automáticamente
            self.precio_unitario = self.producto.precio

        # --- Lógica de Stock ---
        if not is_new:
            # Si el pedido se cancela, le devolvemos el stock al producto
            if estado_anterior != 'cancelado' and self.estado == 'cancelado':
                self.producto.stock += self.cantidad
                self.producto.save()
            # Si se "descancela" (ej. de cancelado a pendiente), volvemos a restar
            elif estado_anterior == 'cancelado' and self.estado != 'cancelado':
                self.producto.stock -= self.cantidad
                self.producto.save()
        elif self.estado in ['pagado', 'entregado']:
             # Caso raro: se crea directamente como pagado
             self.producto.stock -= self.cantidad
             self.producto.save()

        # Guardamos el Pedido
        super().save(*args, **kwargs)

        # --- AUTOMATIZACIÓN DEL HISTORIAL ---
        # Esto asegura que SIEMPRE haya un registro en el timeline
        if is_new:
            HistorialPedido.objects.create(
                pedido=self,
                estado_anterior="",
                estado_nuevo=self.estado,
                usuario=self.usuario # Asumimos que el usuario lo creó
            )
        elif estado_anterior != self.estado:
            HistorialPedido.objects.create(
                pedido=self,
                estado_anterior=estado_anterior,
                estado_nuevo=self.estado,
                usuario=self.usuario # Nota: en cambios automáticos, el usuario será el dueño
            )

    @property
    def total(self):
        return (self.precio_unitario or 0) * (self.cantidad or 0)

    def __str__(self):
        return f"Pedido #{self.id} - {self.producto.nombre}"


# -------------------------------
# 🛒 3. Modelos del Carrito
# -------------------------------
class Carrito(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"Carrito de {self.usuario.username}"

    @property
    def total(self):
        return sum(item.subtotal for item in self.items.all())

class ItemCarrito(models.Model):
    carrito = models.ForeignKey(Carrito, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    @property
    def subtotal(self):
        return self.producto.precio * self.cantidad

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre}"