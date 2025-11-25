from django.db import models
from django.urls import reverse
from categorias.models import Categoria
from django.utils import timezone
from django.utils.html import mark_safe
from cloudinary_storage.storage import MediaCloudinaryStorage
from django.utils.safestring import mark_safe

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)

    # ✅ Forzamos Cloudinary como storage
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

    # ✅ Miniatura para admin
    def portada_preview(self):
        if self.portada:
            return mark_safe(
                f'<img src="{self.portada.url}" width="80" height="80" '
                f'style="object-fit:cover;border-radius:4px;" />'
            )
        return "Sin imagen"
    portada_preview.short_description = "Portada"
