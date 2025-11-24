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
        'hay_stock',
        'creado',
        'actualizado',
        'imagen_portada',
    )
    list_filter = ('categoria', 'creado', 'actualizado')
    search_fields = ('portada','nombre', 'categoria__nombre')
    ordering = ('nombre',)
    date_hierarchy = 'creado'

    # Mostrar stock como badge en admin
    def hay_stock(self, obj):
        return "✅ Sí" if obj.stock > 0 else "❌ No"
    hay_stock.short_description = "Disponible"
