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

    def __str__(self):
        return self.nombre

    def hay_stock(self, cantidad=1):
        return self.stock >= cantidad

    def get_absolute_url(self):
        return reverse("productos:producto_detail", args=[self.pk])

    def portada_preview(self):
        # Muestra la primera “portada múltiple” si existe; sino la portada única
        primera = self.portadas.first()
        url = primera.imagen.url if primera else (self.portada.url if self.portada else None)
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
