# pyrefly: ignore [missing-import]
from django.db import models
# pyrefly: ignore [missing-import]
from django.conf import settings
from productos.models import Producto


# ────────────────────────────────────────────
# ⚙️ 0. Configuración de la Tienda (Singleton)
# ────────────────────────────────────────────
class ConfiguracionTienda(models.Model):
    """
    Modelo singleton: solo existe 1 registro en la base de datos.
    Permite al staff modificar parámetros de la tienda sin tocar código.
    """
    # Envío gratis
    envio_gratis_activo = models.BooleanField(
        "Promo envío gratis activa",
        default=True,
        help_text="Si está activo, se muestra la barra de progreso en el carrito."
    )
    envio_gratis_umbral = models.DecimalField(
        "Monto mínimo para envío gratis ($)",
        max_digits=10, decimal_places=2, default=29000,
        help_text="El cliente obtiene envío gratis cuando su carrito supera este monto."
    )
    envio_gratis_mensaje = models.CharField(
        "Mensaje de la barra",
        max_length=200,
        default="¡Envío GRATIS en compras mayores a ${umbral}!",
        help_text="Usá {umbral} para insertar el monto. Ej: ¡Envío GRATIS en compras mayores a ${umbral}!"
    )
    envio_gratis_mensaje_logrado = models.CharField(
        "Mensaje cuando se alcanza",
        max_length=200,
        default="🎉 ¡Desbloqueaste envío GRATIS!",
        help_text="Lo que ve el cliente cuando alcanza el monto."
    )

    class Meta:
        verbose_name = "Configuración de la Tienda"
        verbose_name_plural = "Configuración de la Tienda"

    def __str__(self):
        return "Configuración General"

    def save(self, *args, **kwargs):
        # Forzar que solo exista 1 registro (singleton)
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        """Obtiene la configuración. Si no existe, la crea con valores por defecto."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

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
        ("pendiente_transferencia", "Pendiente de Transferencia"),
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
    estado = models.CharField(max_length=30, choices=ESTADOS, default="pendiente")
    
    # CACHÉ DEL TOTAL: Para no saturar la DB sumando los detalles todo el tiempo
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # ----- DATOS DE ENVÍO -----
    nombre_envio = models.CharField("Nombre completo", max_length=120, blank=True, null=True)
    email_envio = models.EmailField("Email de contacto", blank=True, null=True)
    telefono_envio = models.CharField("Teléfono / WhatsApp", max_length=30, blank=True, null=True)
    direccion_envio = models.CharField("Calle", max_length=255, blank=True, null=True)
    numero_envio = models.CharField("Número", max_length=20, blank=True, null=True)
    piso_envio = models.CharField("Piso", max_length=20, blank=True, null=True)
    depto_envio = models.CharField("Depto", max_length=20, blank=True, null=True)
    ciudad_envio = models.CharField("Ciudad / Localidad", max_length=100, blank=True, null=True)
    provincia_envio = models.CharField("Provincia", max_length=100, blank=True, null=True)
    codigo_postal_envio = models.CharField("Código Postal", max_length=10, blank=True, null=True)
    notas_envio = models.TextField("Notas para el envío", blank=True, null=True,
                                   help_text="Ej: Timbre 2B, dejar en portería, etc.")
    
    # Datos calculados por Zipnova
    metodo_envio = models.CharField("Método de envío", max_length=150, blank=True, null=True)
    costo_envio = models.DecimalField("Costo de envío", max_digits=10, decimal_places=2, default=0)

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
    estado_anterior = models.CharField(max_length=30, blank=True)
    estado_nuevo = models.CharField(max_length=30)
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
        # Usa precio_display para respetar los descuentos activos.
        if self.cantidad is not None and self.producto and self.producto.precio_display is not None:
            return self.cantidad * self.producto.precio_display
        return 0