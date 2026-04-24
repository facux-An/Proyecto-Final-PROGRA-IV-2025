"""
⚠️  ARCHIVO DEPRECATED - NO USAR

Este archivo contiene código antiguo y duplicado que fue refactorizado.
Todas las vistas se han movido a los submódulos:
- ventas/views/carrito.py → Carritos y compras
- ventas/views/pedidos.py → Gestión de pedidos
- ventas/views/pagos.py → Procesamiento de pagos
- ventas/views/panel.py → Panel de administración
- ventas/views/helpers.py → Funciones de utilidad

No importes desde este archivo. Usa los submódulos en su lugar.

EJEMPLO CORRECTO:
    from ventas.views import carrito
    carrito.ver_carrito(request)

EJEMPLO INCORRECTO (❌):
    from ventas.views import ver_carrito  # ❌ NO EXISTE
"""

# Se mantiene este archivo vacío por compatibilidad histórica.
# Las vistas fueron refactorizadas en submódulos bajo ventas/views/



