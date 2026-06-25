from django.contrib import admin
from .models import Producto


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'nombre',
        'categoria',
        'precio',
        'precio_oferta',
        'en_oferta',
        'es_combo',
        'stock',
        'hay_stock',
        'portada_preview',
    )
    list_filter = ('categoria', 'en_oferta', 'es_combo', 'destacado', 'creado')
    search_fields = ('nombre', 'descripcion', 'categoria__nombre')
    ordering = ('nombre',)
    date_hierarchy = 'creado'
    list_editable = ('en_oferta', 'es_combo', 'precio_oferta')

    fieldsets = (
        ('Información del Producto', {
            'fields': ('nombre', 'descripcion', 'categoria', 'precio', 'stock', 'destacado', 'portada', 'video_tiktok_url'),
        }),
        ('🏷️ Ofertas y Kits', {
            'fields': ('en_oferta', 'precio_oferta', 'fecha_fin_oferta', 'etiqueta_oferta', 'es_combo', 'productos_incluidos'),
            'description': 'Configuración de ofertas, descuentos y kits combo. El countdown en la landing usa la fecha de fin.',
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

