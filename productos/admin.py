from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'categoria',
        'precio',
        'stock',
        'peso_gramos',
        'hay_stock',
        'creado',
        'actualizado',
        'portada_preview',
    )
    list_filter = ('categoria', 'creado', 'actualizado')
    search_fields = ('nombre', 'descripcion', 'categoria__nombre')
    ordering = ('nombre',)
    date_hierarchy = 'creado'

    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'descripcion', 'categoria', 'precio', 'stock', 'destacado', 'portada'),
        }),
        ('📦 Logística (Envío)', {
            'fields': ('peso_gramos', 'largo_cm', 'ancho_cm', 'alto_cm'),
            'description': 'Datos necesarios para calcular el costo de envío con Zipnova. Medí el producto ya empaquetado.',
        }),
    )

    # Mostrar stock como badge en admin
    def hay_stock(self, obj):
        return "✅ Sí" if obj.stock > 0 else "❌ No"
    hay_stock.short_description = "Disponible"
