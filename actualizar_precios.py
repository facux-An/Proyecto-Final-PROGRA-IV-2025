"""
Script de actualización de precios — Esquema Gamificado 2026
Ejecutar con: venv/Scripts/python actualizar_precios.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_plus.settings')
django.setup()

from productos.models import Producto

# Cada tupla: (fragmento del nombre, nuevo precio base)
# Los kits mantienen su precio_oferta si lo tienen, solo actualizamos precio base
cambios = [
    ('Sacapelusa 60 Hojas',        5790),
    ('Repuesto Sacapelusa x2',     6490),
    ('Sacapelusa + Repuesto',      8900),
    ('Pelota Inteligente',        11200),
    ('Rascador',                  15200),
    # Kits
    ('Hogar Impecable - Cl',      14900),
    ('Hogar Impecable - Pr',      18400),
    ('Gato Activo',               23500),
]

print("=" * 60)
print("ACTUALIZACION DE PRECIOS — Tienda Plus (Esquema Gamificado)")
print("=" * 60)

total_actualizados = 0
for nombre_parcial, nuevo_precio in cambios:
    qs = Producto.objects.filter(nombre__icontains=nombre_parcial)
    if qs.exists():
        for p in qs:
            precio_anterior = p.precio
            p.precio = nuevo_precio
            p.save(update_fields=['precio'])
            total_actualizados += 1
            print(f"  OK  {p.nombre}")
            print(f"       Precio anterior: ${precio_anterior:,.0f}  ->  Nuevo: ${nuevo_precio:,.0f}")
    else:
        print(f"  [!] NO ENCONTRADO: {nombre_parcial!r} — verificar nombre exacto en el admin")

print("=" * 60)
print(f"Total actualizados: {total_actualizados} productos")
print("=" * 60)

# Mostrar todos los productos y sus precios actuales
print("\nREVISION FINAL — Stock actual con nuevos precios:")
for p in Producto.objects.all().order_by('precio'):
    kit_label = "[KIT]" if p.es_combo else "[IND]"
    oferta_label = f" (oferta: ${p.precio_oferta:,.0f})" if p.precio_oferta else ""
    print(f"  {kit_label} {p.nombre[:45]:45} ${p.precio:,.0f}{oferta_label}")
