from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db import transaction

from ventas.models import Carrito, ItemCarrito, Pedido, DetallePedido
from productos.models import Producto
from ventas.views.helpers import descontar_stock, registrar_historial, registrar_log


@login_required
def ver_carrito(request):
    """
    Vista principal del carrito.
    Muestra los productos agregados por el usuario autenticado.
    """
    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    return render(request, "ventas/carrito.html", {"carrito": carrito})


@login_required
def agregar_al_carrito(request, producto_id):
    """
    Agrega un producto al carrito del usuario.
    - Solo acepta método POST.
    - Valida stock disponible.
    - Si el producto ya existe en el carrito, incrementa la cantidad.
    """
    if request.method != "POST":
        messages.warning(request, "⚠️ Usá el botón para agregar al carrito.")
        return redirect("productos:producto_list")

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)
    producto = get_object_or_404(Producto, id=producto_id)

    if producto.stock < 1:
        messages.error(request, f"❌ No hay stock disponible para {producto.nombre}.")
        return redirect("productos:producto_list")

    item, creado = ItemCarrito.objects.get_or_create(carrito=carrito, producto=producto)
    if not creado:
        item.cantidad += 1
        item.save()

    messages.success(request, f"✅ {producto.nombre} agregado al carrito.")
    next_url = request.META.get('HTTP_REFERER', 'productos:producto_detail')
    return redirect(next_url)


@login_required
def eliminar_item(request, item_id):
    """
    Elimina un producto del carrito del usuario.
    - Solo acepta método POST.
    - Valida que el item pertenezca al usuario autenticado.
    """
    if request.method != "POST":
        messages.warning(request, "⚠️ Usá el botón para eliminar.")
        return redirect("carrito:carrito_detail")

    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
    item.delete()

    messages.success(request, "🗑️ Producto eliminado del carrito.")
    return redirect("carrito:carrito_detail")


@login_required
def finalizar_compra(request):
    """
    Paso 1: Valida el carrito antes de ir a seleccionar método de pago.
    
    - Valida que el carrito no esté vacío.
    - Verifica stock de cada producto.
    - NO crea el Pedido aún (se crea al confirmar método de pago).
    - Redirige a seleccionar método de pago.
    """
    if request.method != "POST":
        messages.warning(request, "⚠️ Usá el botón para finalizar la compra.")
        return redirect("carrito:carrito_detail")

    carrito = get_object_or_404(Carrito, usuario=request.user)

    if not carrito.items.exists():
        messages.warning(request, "🛒 Tu carrito está vacío.")
        return redirect("carrito:carrito_detail")

    # ✅ Validar stock ANTES de pasar a métodos de pago
    for item in carrito.items.select_related("producto"):
        if item.producto.stock < item.cantidad:
            messages.error(request, f"❌ Stock insuficiente para {item.producto.nombre}.")
            return redirect("carrito:carrito_detail")

    # ✅ Carrito validado, redirige a seleccionar método de pago
    # El Pedido se creará DESPUÉS de confirmar el método
    messages.success(request, "✅ Carrito validado. Selecciona método de pago.")
    return redirect("pagos:metodo")


@login_required
def carrito_checkout(request):
    """
    Paso intermedio de checkout:
    - Aquí podrías validar stock, totales, etc.
    - Actualmente redirige directamente a la selección de método de pago.
    """
    return redirect("pagos:metodo")

@login_required
def modificar_cantidad(request, item_id, accion):
    """
    Suma o resta cantidad de un item en el carrito.
    accion: 'sumar' o 'restar'
    """
    item = get_object_or_404(ItemCarrito, id=item_id, carrito__usuario=request.user)
    
    if accion == 'sumar':
        if item.producto.stock > item.cantidad:
            item.cantidad += 1
            item.save()
            messages.success(request, f"Se agregó una unidad de {item.producto.nombre}.")
        else:
            messages.warning(request, "No hay más stock disponible.")
            
    elif accion == 'restar':
        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
            messages.info(request, f"Se quitó una unidad de {item.producto.nombre}.")
        else:
            # Si es 1 y resta, opcionalmente podrías eliminarlo o dejarlo en 1
            messages.warning(request, "La cantidad mínima es 1. Usá el tacho para eliminar.")

    return redirect("carrito:carrito_detail")