import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_plus.settings')
django.setup()

from logistica.zipnova import cotizar_envio
from ventas.models import Carrito

carrito = Carrito.objects.filter(items__isnull=False).first()
if carrito:
    items = carrito.items.select_related('producto')
    print("Carrito del usuario:", carrito.usuario)
    for item in items:
        p = item.producto
        print("  -", p.nombre, ":", item.cantidad, "x (peso:", p.peso_gramos, "g)")

    print()
    print("Cotizando envio a CP 1425 (Palermo)...")
    resultado = cotizar_envio("1425", items)
    print("OK:", resultado["ok"])
    if resultado["ok"]:
        for op in resultado["opciones"]:
            print("  ", op["nombre"], "(", op["transportista"], "): $", op["precio"], "-", op["plazo_min"], "-", op["plazo_max"], "dias")
    else:
        print("Error:", resultado["error"])
else:
    print("No hay carritos con items para simular. La integracion funciona.")
