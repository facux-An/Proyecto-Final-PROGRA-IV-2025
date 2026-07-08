from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Producto, CampaniaDescuento, CodigoDescuento


# ──────────────────────────────────────────────
# 📦 Admin: Producto (sin cambios en funcionalidad)
# ──────────────────────────────────────────────
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
        ('🏷️ Ofertas y Kits (Manual)', {
            'fields': ('en_oferta', 'precio_oferta', 'fecha_fin_oferta', 'etiqueta_oferta', 'es_combo', 'productos_incluidos'),
            'description': '⚠️ Las Campañas Automáticas tienen PRIORIDAD sobre estas ofertas manuales.',
        }),
        ('📦 Logística (Envío)', {
            'fields': ('peso_gramos', 'largo_cm', 'ancho_cm', 'alto_cm'),
            'description': 'Datos necesarios para calcular el costo de envío con Zipnova.',
        }),
    )

    def hay_stock(self, obj):
        return "✅ Sí" if obj.stock > 0 else "❌ No"
    hay_stock.short_description = "Disponible"


# ──────────────────────────────────────────────
# 🔥 Admin: Campaña de Descuento Automática
# ──────────────────────────────────────────────
@admin.register(CampaniaDescuento)
class CampaniaDescuentoAdmin(admin.ModelAdmin):
    list_display = (
        'nombre',
        'tipo_descuento',
        'valor',
        'fecha_inicio',
        'fecha_fin',
        'activa',
        'estado_vigencia',
        'cantidad_productos',
    )
    list_filter = ('activa', 'tipo_descuento')
    search_fields = ('nombre',)
    list_editable = ('activa',)
    # filter_horizontal permite mover productos entre dos listas (mucho más cómodo que un <select> múltiple)
    filter_horizontal = ('productos',)

    fieldsets = (
        ('📋 Información de la Campaña', {
            'fields': ('nombre', 'tipo_descuento', 'valor', 'activa'),
            'description': (
                'Tipos: <b>Porcentaje</b> = escribe 20 para 20% OFF. '
                '<b>Monto Fijo</b> = escribe la cifra en pesos a descontar.'
            ),
        }),
        ('📅 Vigencia', {
            'fields': ('fecha_inicio', 'fecha_fin'),
            'description': 'La campaña solo se aplica si está <b>Activa</b> Y la fecha actual está dentro de este rango.',
        }),
        ('🛍️ Productos Aplicables', {
            'fields': ('productos',),
            'description': 'Usá las flechas para mover productos al panel de "Elegidos". Solo esos verán el precio tachado.',
        }),
    )

    def estado_vigencia(self, obj):
        """Muestra un badge visual de si la campaña está vigente ahora mismo."""
        if obj.esta_vigente:
            return format_html('<span style="color:green; font-weight:bold;">✅ Vigente</span>')
        elif not obj.activa:
            return format_html('<span style="color:gray;">⏸️ Pausada</span>')
        elif timezone.now() < obj.fecha_inicio:
            return format_html('<span style="color:orange;">⏳ Próxima</span>')
        else:
            return format_html('<span style="color:red;">❌ Expirada</span>')
    estado_vigencia.short_description = "Estado"

    def cantidad_productos(self, obj):
        count = obj.productos.count()
        return f"{count} producto{'s' if count != 1 else ''}"
    cantidad_productos.short_description = "Productos"


# ──────────────────────────────────────────────
# 🎟️ Admin: Código de Descuento (Cupones)
# ──────────────────────────────────────────────
@admin.register(CodigoDescuento)
class CodigoDescuentoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo',
        'tipo_descuento',
        'valor',
        'fecha_inicio',
        'fecha_fin',
        'uso_maximo',
        'usos_actuales',
        'progreso_usos',
        'activo',
        'estado_validez',
    )
    list_filter = ('activo', 'tipo_descuento')
    search_fields = ('codigo',)
    list_editable = ('activo',)
    # usos_actuales nunca se edita a mano; se incrementa automáticamente al confirmar compra
    readonly_fields = ('usos_actuales',)

    fieldsets = (
        ('🎟️ Configuración del Cupón', {
            'fields': ('codigo', 'tipo_descuento', 'valor', 'activo'),
            'description': (
                'El <b>código</b> es lo que el cliente escribe en el carrito. '
                'Usá mayúsculas y sin espacios. Ej: FELIPE20'
            ),
        }),
        ('📅 Vigencia', {
            'fields': ('fecha_inicio', 'fecha_fin'),
        }),
        ('📊 Control de Uso', {
            'fields': ('uso_maximo', 'usos_actuales'),
            'description': (
                '<b>Usos máximos = 0</b> significa usos ilimitados. '
                '<b>Usos actuales</b> es de solo lectura y se incrementa automáticamente.'
            ),
        }),
    )

    def progreso_usos(self, obj):
        """Muestra una barra de progreso visual de cuántos usos quedan."""
        if obj.uso_maximo == 0:
            return format_html('<span style="color:blue;">♾️ Ilimitado</span>')
        porcentaje = min(round((obj.usos_actuales / obj.uso_maximo) * 100), 100)
        color = 'green' if porcentaje < 75 else ('orange' if porcentaje < 100 else 'red')
        return format_html(
            '<div style="width:100px; background:#eee; border-radius:4px; overflow:hidden;">'
            '<div style="width:{p}%; background:{c}; height:12px; border-radius:4px;"></div></div>'
            ' <small>{u}/{m}</small>',
            p=porcentaje, c=color, u=obj.usos_actuales, m=obj.uso_maximo
        )
    progreso_usos.short_description = "Usos"

    def estado_validez(self, obj):
        """Muestra si el cupón es válido ahora mismo."""
        if obj.es_valido:
            return format_html('<span style="color:green; font-weight:bold;">✅ Válido</span>')
        elif not obj.activo:
            return format_html('<span style="color:gray;">⏸️ Pausado</span>')
        elif timezone.now() > obj.fecha_fin:
            return format_html('<span style="color:red;">❌ Expirado</span>')
        elif obj.uso_maximo > 0 and obj.usos_actuales >= obj.uso_maximo:
            return format_html('<span style="color:red;">🚫 Agotado</span>')
        else:
            return format_html('<span style="color:orange;">⏳ Próximo</span>')
    estado_validez.short_description = "Validez"
