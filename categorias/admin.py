from django.contrib import admin
from .models import Categoria

# Filtro por año de creación
class FechaCreacionFiltro(admin.SimpleListFilter):
    title = 'Año de creación'
    parameter_name = 'fecha_creacion__year'

    def lookups(self, request, model_admin):
        años = Categoria.objects.dates('fecha_creacion', 'year')
        return [(a.year, str(a.year)) for a in años]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_creacion__year=self.value())
        return queryset


# Filtro por mes de creación
class MesCreacionFiltro(admin.SimpleListFilter):
    title = 'Mes de creación'
    parameter_name = 'fecha_creacion__month'

    def lookups(self, request, model_admin):
        meses = Categoria.objects.dates('fecha_creacion', 'month')
        return [(m.month, m.strftime('%B')) for m in meses]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(fecha_creacion__month=self.value())
        return queryset


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'fecha_creacion', 'cantidad_productos')
    search_fields = ('nombre',)
    list_filter = (FechaCreacionFiltro, MesCreacionFiltro)
    ordering = ('nombre',)
    date_hierarchy = 'fecha_creacion'

    def cantidad_productos(self, obj):
        return obj.productos.count()
    cantidad_productos.short_description = "Productos asociados"
