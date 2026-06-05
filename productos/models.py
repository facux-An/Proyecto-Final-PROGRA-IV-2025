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
        """Retorna el precio a mostrar: oferta si está activa, sino el normal."""
        if self.oferta_activa and self.precio_oferta:
            return self.precio_oferta
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

    class Meta:
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
