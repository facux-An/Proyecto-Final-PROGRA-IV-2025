from django.db import models
from django.urls import reverse
from categorias.models import Categoria
from django.utils import timezone

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    portada = models.ImageField(upload_to="productos/", blank=True, null=True)

    categoria = models.ForeignKey(
        Categoria,
        on_delete=models.CASCADE,
        related_name='productos',
        null=True,
        blank=True
    )

    creado = models.DateTimeField(default=timezone.now)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['nombre']
        verbose_name = 'Producto'
        verbose_name_plural = 'Productos'

    def __str__(self):
        return self.nombre

    def hay_stock(self, cantidad=1):
        return self.stock >= cantidad

    def get_absolute_url(self):
        return reverse('productos:producto_detail', args=[self.pk])
