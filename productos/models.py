from django.db import models
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.urls import reverse
from cloudinary_storage.storage import MediaCloudinaryStorage


class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    
    # Campo para la Vitrina Dinámica
    destacado = models.BooleanField(default=False, verbose_name="Destacado en Home")

    # ----- OFERTAS Y KITS -----
    precio_oferta = models.DecimalField(
        "Precio de oferta", max_digits=10, decimal_places=2,
        null=True, blank=True,
        help_text="Precio con descuento. Dejar vacío si no tiene oferta."
    )
    en_oferta = models.BooleanField(
        "En oferta", default=False,
        help_text="Activar para mostrar este producto como oferta."
    )
    en_carrusel = models.BooleanField(
        "Mostrar en Carrusel", default=False,
        help_text="Activar para que el producto aparezca en el slider gigante del Home."
    )
    fecha_fin_oferta = models.DateTimeField(
        "Oferta válida hasta", null=True, blank=True,
        help_text="Fecha y hora en que expira la oferta. Se usa para el countdown."
    )
    es_combo = models.BooleanField(
        "Es Kit/Combo", default=False,
        help_text="Marcar si este producto es un kit que incluye varios items."
    )
    etiqueta_oferta = models.CharField(
        "Etiqueta", max_length=30, blank=True,
        help_text="Texto del badge. Ej: '🏠 COMBO -15%', '🔥 2x1', 'NOVEDAD'"
    )
    productos_incluidos = models.TextField(
        "Productos incluidos en el kit", blank=True,
        help_text="Descripción de lo que incluye. Ej: 'Cepillo Deslanador + Rodillo Quitapelusas'"
    )

    # ----- LOGÍSTICA (Zipnova) -----
    peso_gramos = models.PositiveIntegerField(
        "Peso (gramos)", default=500,
        help_text="Peso del producto en gramos. Ej: 500 = medio kilo."
    )
    largo_cm = models.PositiveIntegerField("Largo (cm)", default=20)
    ancho_cm = models.PositiveIntegerField("Ancho (cm)", default=15)
    alto_cm = models.PositiveIntegerField("Alto (cm)", default=10)

    # ----- VIDEOS -----
    video_tiktok_url = models.URLField(
        "Enlace de TikTok", blank=True, null=True,
        help_text="Pega el enlace del video de TikTok (Ej: https://www.tiktok.com/@usuario/video/1234567)"
    )

    # Portada principal existente (opcional, la podés seguir usando)
    portada = models.ImageField(
        storage=MediaCloudinaryStorage(),
        upload_to="productos/portadas/",
        blank=True,
        null=True
    )

    categoria = models.ForeignKey(
        "categorias.Categoria",
        on_delete=models.CASCADE,
        related_name="productos",
        null=True,
        blank=True
    )

    creado = models.DateTimeField(default=timezone.now)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["nombre"]
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        # 🚀 Optimización de Base de Datos: Índices B-Tree
        indexes = [
            models.Index(fields=['nombre'], name='idx_producto_nombre'),
            models.Index(fields=['precio'], name='idx_producto_precio'),
            models.Index(fields=['stock'], name='idx_producto_stock'),
        ]

    def __str__(self):
        return self.nombre

    def hay_stock(self, cantidad=1):
        return self.stock >= cantidad

    @property
    def porcentaje_descuento(self):
        """Calcula el porcentaje de descuento si tiene oferta."""
        if self.precio_oferta and self.precio and self.precio > 0:
            return int(((self.precio - self.precio_oferta) / self.precio) * 100)
        return 0

    @property
    def ahorro_monetario(self):
        """Calcula cuánto dinero se ahorra con la oferta."""
        if self.oferta_activa and self.precio_oferta and self.precio > self.precio_oferta:
            return self.precio - self.precio_oferta
        return 0

    @property
    def oferta_activa(self):
        """Verifica si la oferta está activa (en_oferta=True y no expirada)."""
        if not self.en_oferta:
            return False
        if self.fecha_fin_oferta is None:
            return True  # Oferta sin fecha de expiración = siempre activa
        return self.fecha_fin_oferta > timezone.now()

    @property
    def precio_display(self):
        """
        Devuelve el precio final a mostrar al cliente, con la siguiente prioridad:
        1. Campaña de descuento activa (CampaniaDescuento) → descuento masivo automático.
        2. Oferta manual del producto (precio_oferta + en_oferta activo).
        3. Precio base normal.
        """
        from django.apps import apps
        CampaniaDescuento = apps.get_model('productos', 'CampaniaDescuento')
        from django.utils import timezone
        now = timezone.now()

        # --- Prioridad 1: Campaña activa ---
        campania = (
            CampaniaDescuento.objects
            .filter(
                activa=True,
                productos=self,
                fecha_inicio__lte=now,
                fecha_fin__gte=now,
            )
            .first()
        )
        if campania:
            if campania.tipo_descuento == 'porcentaje':
                descuento = self.precio * (campania.valor / 100)
                return round(self.precio - descuento, 2)
            else:  # monto_fijo
                return max(round(self.precio - campania.valor, 2), 0)

        # --- Prioridad 2: Oferta manual ---
        if self.oferta_activa and self.precio_oferta:
            return self.precio_oferta

        # --- Prioridad 3: Precio base ---
        return self.precio

    def get_absolute_url(self):
        return reverse("productos:producto_detail", args=[self.pk])

    @property
    def imagen_principal_url(self):
        primera = self.portadas.first()
        if primera and primera.imagen:
            return primera.imagen.url
        if self.portada:
            return self.portada.url
        return None

    @property
    def tiktok_video_id(self):
        """Extrae el ID numérico del video desde el enlace completo de TikTok."""
        if self.video_tiktok_url:
            import re
            match = re.search(r'/video/(\d+)', self.video_tiktok_url)
            if match:
                return match.group(1)
        return None

    def portada_preview(self):
        # Muestra la primera “portada múltiple” si existe; sino la portada única
        url = self.imagen_principal_url
        if url:
            return mark_safe(
                f'<img src="{url}" width="80" height="80" style="object-fit:cover;border-radius:4px;" />'
            )
        return "Sin imagen"
    portada_preview.short_description = "Portada"


class PortadaProducto(models.Model):
    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name="portadas"
    )
    imagen = models.ImageField(
        storage=MediaCloudinaryStorage(),
        upload_to="productos/portadas/"
    )
    orden = models.PositiveIntegerField(
        default=0,
        help_text="Orden de visualización (0 es la portada principal)."
    )

    class Meta:
        ordering = ['orden', 'id']
        verbose_name = "Portada de producto"
        verbose_name_plural = "Portadas de producto"

    def __str__(self):
        return f"Portada de {self.producto.nombre}"

    def imagen_preview(self):
        if self.imagen:
            return mark_safe(
                f'<img src="{self.imagen.url}" width="80" height="80" style="object-fit:cover;border-radius:4px;" />'
            )
        return "Sin imagen"
    imagen_preview.short_description = "Imagen"


# ──────────────────────────────────────────────
# 🔥 Motor de Ofertas: Campaña Automática Global
# ──────────────────────────────────────────────
class CampaniaDescuento(models.Model):
    """
    Ofertas masivas automáticas (Ej: Black Friday, Liquidación).
    El descuento se refleja directamente en la vidriera, tachando el precio original.
    La prioridad es superior a cualquier oferta manual del producto.
    """
    TIPO_CHOICES = [
        ('porcentaje', 'Porcentaje (%)'),
        ('monto_fijo', 'Monto Fijo ($)'),
    ]

    nombre = models.CharField(
        "Nombre de la campaña", max_length=100,
        help_text="Ej: Black Friday, Liquidación de Invierno, Promo Día del Gato"
    )
    tipo_descuento = models.CharField(
        "Tipo de descuento", max_length=20,
        choices=TIPO_CHOICES, default='porcentaje'
    )
    valor = models.DecimalField(
        "Valor del descuento", max_digits=10, decimal_places=2,
        help_text="Si el tipo es Porcentaje, ingresá 20 para un 20% OFF. Si es Monto Fijo, ingresá la cifra en pesos."
    )
    fecha_inicio = models.DateTimeField("Inicio de la campaña")
    fecha_fin = models.DateTimeField("Fin de la campaña")
    activa = models.BooleanField(
        "¿Activa?", default=True,
        help_text="Debe estar activa Y dentro del rango de fechas para aplicarse."
    )
    productos = models.ManyToManyField(
        Producto,
        related_name="campanias",
        blank=True,
        help_text="Seleccioná los productos a los que aplica esta campaña."
    )

    class Meta:
        verbose_name = "Campaña de Descuento"
        verbose_name_plural = "Campañas de Descuento"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_descuento_display()} - {self.valor})"

    @property
    def esta_vigente(self):
        """Retorna True si la campaña está activa Y dentro del rango de fechas actual."""
        from django.utils import timezone
        now = timezone.now()
        return self.activa and self.fecha_inicio <= now <= self.fecha_fin


# ──────────────────────────────────────────────
# 🎟️ Motor de Cupones: Código de Descuento Privado
# ──────────────────────────────────────────────
class CodigoDescuento(models.Model):
    """
    Cupones privados para influencers, clientes VIP o promociones especiales.
    NO muestran el precio tachado en la vidriera.
    Se aplican manualmente en el carrito/checkout por el cliente.
    """
    TIPO_CHOICES = [
        ('porcentaje', 'Porcentaje (%)'),
        ('monto_fijo', 'Monto Fijo ($)'),
    ]

    codigo = models.CharField(
        "Código", max_length=50, unique=True,
        help_text="Ej: FELIPE20, INFLUENCER10. Sin espacios, preferí mayúsculas."
    )
    tipo_descuento = models.CharField(
        "Tipo de descuento", max_length=20,
        choices=TIPO_CHOICES, default='porcentaje'
    )
    valor = models.DecimalField(
        "Valor del descuento", max_digits=10, decimal_places=2,
        help_text="Si el tipo es Porcentaje, ingresá 15 para un 15% OFF. Si es Monto Fijo, ingresá la cifra en pesos."
    )
    fecha_inicio = models.DateTimeField("Válido desde")
    fecha_fin = models.DateTimeField("Válido hasta")
    uso_maximo = models.PositiveIntegerField(
        "Usos máximos", default=100,
        help_text="Cantidad máxima de veces que este código puede ser usado. 0 = sin límite."
    )
    usos_actuales = models.PositiveIntegerField(
        "Usos actuales", default=0, editable=False
    )
    activo = models.BooleanField(
        "¿Activo?", default=True,
        help_text="Apagá el toggle para desactivar el cupón sin borrarlo."
    )

    class Meta:
        verbose_name = "Código de Descuento"
        verbose_name_plural = "Códigos de Descuento"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.codigo} ({self.get_tipo_descuento_display()} - {self.valor})"

    @property
    def es_valido(self):
        """Verifica todas las condiciones de validez del cupón."""
        from django.utils import timezone
        now = timezone.now()
        if not self.activo:
            return False
        if not (self.fecha_inicio <= now <= self.fecha_fin):
            return False
        if self.uso_maximo > 0 and self.usos_actuales >= self.uso_maximo:
            return False
        return True

    def calcular_descuento(self, total):
        """Calcula el monto de descuento a aplicar sobre un total dado.
        
        Nota: casteamos valor a float para evitar TypeError al operar
        con float (total del carrito) y Decimal (valor del campo DB).
        """
        total = float(total)
        valor = float(self.valor)
        if self.tipo_descuento == 'porcentaje':
            return round(total * (valor / 100), 2)
        else:  # monto_fijo
            return min(valor, total)  # No puede descontar más que el total

