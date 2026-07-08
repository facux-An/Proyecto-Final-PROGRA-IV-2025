from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db import transaction
from django.core.cache import cache

from ventas.models import Carrito, ItemCarrito, Pedido, DetallePedido
from productos.models import Producto, CodigoDescuento
from ventas.views.helpers import descontar_stock, registrar_historial, registrar_log


def _invalidar_cache_carrito(user_id):
    """Borra el caché del contador del carrito para forzar una recarga inmediata."""
    cache.delete(f"carrito_count_user_{user_id}")


@login_required
def ver_carrito(request):
    """
    Vista principal del carrito.
    Muestra los productos agregados por el usuario autenticado.
    Inyecta datos de la barra de envío gratis desde ConfiguracionTienda.
    """
    from ventas.models import ConfiguracionTienda

    carrito, _ = Carrito.objects.get_or_create(usuario=request.user)

    # Datos de envío gratis (singleton del staff)
    config = ConfiguracionTienda.get()
    total_carrito = float(carrito.total)
    umbral = float(config.envio_gratis_umbral)

    if umbral > 0:
        porcentaje = min(round((total_carrito / umbral) * 100, 1), 100)
        falta = max(umbral - total_carrito, 0)
    else:
        porcentaje = 100
        falta = 0

    alcanzado = total_carrito >= umbral

    # ════════════════════════════════════════════════════════════════
    # MOTOR DE RECOMENDACIONES V2 — Psicología de Bajo Roce
    #
    # Principio: en el carrito el usuario ya decidió comprar.
    # Toda fricción cognitiva (pensar, comparar, dudar) aumenta
    # el abandono. El motor trabaja con DOS slots independientes:
    #
    # SLOT 1 — "El Cierre" (matemático)
    #   Busca el producto individual MÁS BARATO que supere el gap
    #   al umbral de envío gratis. Si faltan $6.600, recomendamos
    #   algo de $7.000 o $8.000, NUNCA el kit de $23.000.
    #   Mensaje: "Agregá solo este y tu envío es GRATIS".
    #
    # SLOT 2 — "El Impulso" (anclaje de precio bajo)
    #   Ignora el gap. Muestra el producto MÁS BARATO del catálogo
    #   que no esté ya en el carrito ni en el Slot 1.
    #   Psicología: "Ya que estoy pagando tanto... ¿qué son $X más?".
    #   Aumenta el ticket promedio sin generar dudas.
    #
    # Reglas de exclusión globales:
    #   - Nunca recomendar productos ya en el carrito.
    #   - Si hay un kit en el carrito, no recomendar otro kit.
    #   - Los dos slots siempre muestran productos DISTINTOS.
    # ════════════════════════════════════════════════════════════════
    rec_cierre = None    # Slot 1: cierra el gap al envío gratis
    rec_impulso = None   # Slot 2: compra por impulso, lo más barato

    if not alcanzado and config.envio_gratis_activo:
        ids_en_carrito = set(
            carrito.items.values_list("producto_id", flat=True)
        )

        # Regla de oro: si ya hay un kit, excluir kits de candidatos
        hay_kit_en_carrito = carrito.items.filter(producto__es_combo=True).exists()

        # Pool de candidatos: siempre preferir productos individuales
        # Los kits generan fricción cognitiva (¿qué incluye?, ¿lo necesito todo?)
        candidatos = list(
            Producto.objects
            .filter(stock__gt=0)
            .exclude(id__in=ids_en_carrito)
            .exclude(es_combo=True)  # preferir individuales en ambos slots
            .select_related("categoria")
            .prefetch_related("portadas")
            .order_by("precio")  # ascendente: el más barato primero
        )

        # Fallback: si no hay individuales y no hay kit en carrito, incluir kits
        if not candidatos and not hay_kit_en_carrito:
            candidatos = list(
                Producto.objects
                .filter(stock__gt=0, es_combo=True)
                .exclude(id__in=ids_en_carrito)
                .select_related("categoria")
                .prefetch_related("portadas")
                .order_by("precio")
            )

        # ── SLOT 1 — El Cierre ─────────────────────────────────────────────
        # El producto más barato cuyo precio_display >= falta.
        # Ordenado por precio ASC, el primero = menor costo extra para el cliente.
        cierre_pool = [
            p for p in candidatos
            if float(p.precio_display) >= falta
        ]
        if cierre_pool:
            rec_cierre = cierre_pool[0]

        # ── SLOT 2 — El Impulso ────────────────────────────────────────────
        # El producto más barato disponible, excluyendo el ya asignado al Slot 1.
        # Si no hay Slot 1, también puede ser el más barato del pool.
        id_cierre = rec_cierre.id if rec_cierre else None
        impulso_pool = [p for p in candidatos if p.id != id_cierre]
        if impulso_pool:
            rec_impulso = impulso_pool[0]

    # ── Cuánto pasa del umbral si agrega el producto de cierre ─────────────
    # Mensaje positivo: "Con este producto ya cubrís el envío y te sobran $X".
    overshoot_cierre = 0
    if rec_cierre:
        overshoot_cierre = max(0, float(rec_cierre.precio_display) - falta)

    alcanzado = total_carrito >= umbral

    # ── Cupón de descuento (guardado en sesión) ─────────────────────────────
    # Leer el código guardado en sesión (si el usuario ya lo aplicó antes)
    cupon_codigo = request.session.get('cupon_codigo')
    cupon_aplicado = None
    descuento_cupon = 0

    if cupon_codigo:
        try:
            cupon = CodigoDescuento.objects.get(codigo__iexact=cupon_codigo)
            if cupon.es_valido:
                cupon_aplicado = cupon
                descuento_cupon = float(cupon.calcular_descuento(total_carrito))
            else:
                # El cupón expió o se agotó desde que lo guardó: limpiar sesión
                del request.session['cupon_codigo']
                messages.warning(request, "🎟️ El cupón ya no es válido y fue eliminado.")
        except CodigoDescuento.DoesNotExist:
            del request.session['cupon_codigo']

    total_con_descuento = max(total_carrito - descuento_cupon, 0)

    context = {
        "carrito": carrito,
        # Barra de envío gratis
        "eg_activo": config.envio_gratis_activo,
        "eg_umbral": umbral,
        "eg_porcentaje": porcentaje,
        "eg_falta": falta,
        "eg_alcanzado": alcanzado,
        "eg_mensaje": config.envio_gratis_mensaje.replace("{umbral}", f"{umbral:,.0f}"),
        "eg_mensaje_logrado": config.envio_gratis_mensaje_logrado,
        # Recomendaciones V2 — dos slots independientes
        "rec_cierre": rec_cierre,
        "rec_impulso": rec_impulso,
        "rec_overshoot": int(overshoot_cierre),
        "eg_falta_int": int(falta),
        # Cupón de descuento
        "cupon_aplicado": cupon_aplicado,
        "descuento_cupon": descuento_cupon,
        "total_con_descuento": total_con_descuento,
    }

    return render(request, "ventas/carrito.html", context)


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

    _invalidar_cache_carrito(request.user.id)
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
    _invalidar_cache_carrito(request.user.id)

    messages.success(request, "🗑️ Producto eliminado del carrito.")
    return redirect("carrito:carrito_detail")


@login_required
def finalizar_compra(request):
    """
    Paso 1: Valida el carrito antes de ir a seleccionar método de pago.
    
    - Valida que el carrito no esté vacío.
    - Verifica stock de cada producto.
    - Aplica envío gratis si corresponde.
    - NO crea el Pedido aún (se crea al confirmar método de pago).
    - Redirige a seleccionar método de pago.
    """
    from ventas.models import ConfiguracionTienda

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

    # ✅ Verificar si aplica envío gratis
    config = ConfiguracionTienda.get()
    total_carrito = float(carrito.total)
    tiene_envio_gratis = (
        config.envio_gratis_activo
        and total_carrito >= float(config.envio_gratis_umbral)
    )

    if tiene_envio_gratis:
        # Envío gratis → forzar precio $0
        envio_precio = 0.0
        envio_nombre = "Envío Gratis (Promo Tienda Plus)"
    else:
        # Sin envío gratis → exigir que haya cotizado
        envio_precio = request.POST.get("envio_precio", 0)
        envio_nombre = request.POST.get("envio_nombre", "")

        if not envio_nombre or not envio_nombre.strip():
            messages.error(request, '🚚 Necesitás calcular el envío antes de continuar. Ingresá tu código postal.')
            return redirect("carrito:carrito_detail")

        try:
            envio_precio = float(envio_precio)
        except ValueError:
            envio_precio = 0.0

    # ✅ Guardar selección de envío en la sesión
    request.session["envio_cotizado"] = {
        "precio": envio_precio,
        "nombre": envio_nombre
    }

    # ✅ Carrito validado, redirige a datos de envío (Paso 1)
    messages.success(request, "✅ Carrito validado. Completá tus datos de envío.")
    return redirect("pagos:envio")


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
            _invalidar_cache_carrito(request.user.id)
            messages.success(request, f"Se agregó una unidad de {item.producto.nombre}.")
        else:
            messages.warning(request, "No hay más stock disponible.")
            
    elif accion == 'restar':
        if item.cantidad > 1:
            item.cantidad -= 1
            item.save()
            _invalidar_cache_carrito(request.user.id)
            messages.info(request, f"Se quitó una unidad de {item.producto.nombre}.")
        else:
            # Si es 1 y resta, opcionalmente podrías eliminarlo o dejarlo en 1
            messages.warning(request, "La cantidad mínima es 1. Usá el tacho para eliminar.")

    return redirect("carrito:carrito_detail")


import logging as _logging
_cotizar_logger = _logging.getLogger("ventas.carrito.cotizar")


@login_required
def api_cotizar_envio(request):
    """
    Endpoint AJAX que recibe un Código Postal y devuelve las opciones
    de envío cotizadas en tiempo real con Zipnova.

    GET /ventas/carrito/cotizar-envio/?cp=1004
    Siempre responde JSON (nunca un 500).
    """
    import traceback
    from django.http import JsonResponse
    from logistica.zipnova import cotizar_envio

    try:
        cp = request.GET.get("cp", "").strip()

        if not cp or len(cp) < 4:
            return JsonResponse({"ok": False, "error": "Ingresá un código postal válido (mínimo 4 dígitos)."})

        carrito = Carrito.objects.filter(usuario=request.user).first()

        if not carrito or not carrito.items.exists():
            _cotizar_logger.warning(
                f"[cotizar_envio] Carrito vacío para usuario={request.user} "
                f"(carrito={'None' if not carrito else carrito.id})"
            )
            return JsonResponse({"ok": False, "error": "Tu carrito está vacío."})

        items = carrito.items.select_related("producto")

        _cotizar_logger.info(
            f"[cotizar_envio] usuario={request.user} | cp={cp} | "
            f"items={items.count()} | carrito_id={carrito.id}"
        )

        resultado = cotizar_envio(cp, items)

        # Agregar subtotal para que el frontend pueda calcular el total con envío
        subtotal = float(sum(item.subtotal for item in items))
        resultado["subtotal_carrito"] = subtotal

        _cotizar_logger.info(
            f"[cotizar_envio] OK | opciones={len(resultado.get('opciones', []))} | error={resultado.get('error')}"
        )

        return JsonResponse(resultado)

    except Exception as exc:
        tb = traceback.format_exc()
        _cotizar_logger.error(f"[cotizar_envio] EXCEPCION NO MANEJADA:\n{tb}")
        return JsonResponse({
            "ok": False,
            "error": "Ocurrió un error interno al cotizar el envío. Por favor intentá de nuevo.",
        })


# ──────────────────────────────────────────────
# 🎟️ Motor de Cupones: Aplicar / Quitar
# ──────────────────────────────────────────────
@login_required
def aplicar_cupon(request):
    """
    Recibe un código de cupón vía POST y lo valida.
    Si es válido, lo guarda en la sesión para aplicarlo al total del carrito.
    NO incrementa usos_actuales aquí; eso se hace al confirmar la compra.
    """
    if request.method != 'POST':
        return redirect('carrito:carrito_detail')

    codigo = request.POST.get('cupon_codigo', '').strip().upper()

    if not codigo:
        messages.warning(request, "🎟️ Ingresá un código de cupón.")
        return redirect('carrito:carrito_detail')

    try:
        cupon = CodigoDescuento.objects.get(codigo__iexact=codigo)
    except CodigoDescuento.DoesNotExist:
        messages.error(request, "❌ El código de cupón no existe.")
        return redirect('carrito:carrito_detail')

    if not cupon.es_valido:
        messages.error(request, "❌ El cupón no es válido (puede estar expirado, agotado o desactivado).")
        return redirect('carrito:carrito_detail')

    # Guardar el código en sesión para aplicarlo en la vista del carrito y al checkout
    request.session['cupon_codigo'] = cupon.codigo
    messages.success(request, f"🎉 ¡Cupón {cupon.codigo} aplicado! Descuento de {cupon.get_tipo_descuento_display()} por {cupon.valor}.")
    return redirect('carrito:carrito_detail')


@login_required
def quitar_cupon(request):
    """
    Elimina el cupón activo de la sesión.
    """
    if 'cupon_codigo' in request.session:
        del request.session['cupon_codigo']
        messages.info(request, "🔄 Cupón eliminado del carrito.")
    return redirect('carrito:carrito_detail')