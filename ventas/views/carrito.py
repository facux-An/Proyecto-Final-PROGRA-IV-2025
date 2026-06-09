from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.contrib import messages
from django.db import transaction
from django.core.cache import cache

from ventas.models import Carrito, ItemCarrito, Pedido, DetallePedido
from productos.models import Producto
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
    # MOTOR DE RECOMENDACIONES INTELIGENTE
    # Lógica basada en la estrategia de upsell de Tienda Plus.
    # Objetivo: recomendar 1-2 productos que cubran la brecha al umbral
    # de envío gratis, priorizando los que NO están ya en el carrito.
    # ════════════════════════════════════════════════════════════════
    productos_recomendados = []
    recomendacion_modo = None   # 'solo' | 'combo' | 'combo_parcial'
    if not alcanzado and config.envio_gratis_activo:
        ids_en_carrito = set(
            carrito.items.values_list("producto_id", flat=True)
        )

        # ── REGLA DE ORO: si el carrito ya tiene un kit/combo, NUNCA recomendar otro kit ──
        # Lógica: ofrecer dos kits similares es incoherente y frustrante para el cliente.
        hay_kit_en_carrito = carrito.items.filter(producto__es_combo=True).exists()

        candidatos = list(
            Producto.objects
            .filter(stock__gt=0)
            .exclude(id__in=ids_en_carrito)
            .exclude(es_combo=hay_kit_en_carrito)   # excluir kits si ya hay uno en carrito
            .select_related("categoria")
            .prefetch_related("portadas")
            .order_by("precio")
        )

        # ── NIVEL 1: Producto individual que cierre la brecha con "Overshoot Gamificado" ──
        # La estrategia psicológica es que el precio NO sea exacto al gap.
        # El cliente tiene que sentir que "hackeó el sistema" pasando el umbral por un margen pequeño.
        # Rango objetivo: el producto cuesta entre falta y falta * 2.0
        # Scoring: premiamos el overshoot de 100 a 2000 pesos (la "zona dulce" psicológica).
        candidatos_cierre_solo = [
            p for p in candidatos
            if float(p.precio_display) >= falta and float(p.precio_display) <= falta * 2.0
        ]

        if candidatos_cierre_solo:
            def overshoot_score(p):
                overshoot = float(p.precio_display) - falta
                # Score mínimo (mejor) en el rango 100-2000 pesos de overshoot
                # Fuera de esa zona, penalizamos progresivamente
                if 100 <= overshoot <= 2000:
                    return overshoot  # dentro de la zona dulce, el menor exceso gana
                elif overshoot < 100:
                    return 2000 + (100 - overshoot) * 5   # muy exacto: penalizar (parece armado)
                else:
                    return overshoot  # mucho exceso: penalizar por sobrepropuesta

            candidatos_cierre_solo.sort(key=overshoot_score)
            estrella = candidatos_cierre_solo[0]

            # Complementario: enriquece la oferta visualmente.
            # Rol: mostrar variedad, no cerrar el gap por sí solo.
            # Prioridad 1: distinta categoría + precio <= estrella (no sobreproponer)
            # Prioridad 2: si no hay de distinta cat, cualquier producto más barato que la estrella
            # Prioridad 3: si tampoco, el siguiente más barato disponible
            precio_estrella = float(estrella.precio_display)
            complementarios = [
                p for p in candidatos
                if p.id != estrella.id
                and p.categoria_id != estrella.categoria_id
                and float(p.precio_display) <= precio_estrella
            ]
            if not complementarios:
                # Fallback 2: misma categoría permitida pero precio <= estrella
                complementarios = [
                    p for p in candidatos
                    if p.id != estrella.id
                    and float(p.precio_display) <= precio_estrella
                ]
            if not complementarios:
                # Fallback 3: cualquier otro producto disponible (sin restricción de precio)
                complementarios = [p for p in candidatos if p.id != estrella.id]

            complementarios.sort(key=lambda p: float(p.precio_display))
            productos_recomendados = [estrella] + complementarios[:1]
            recomendacion_modo = 'solo'

        else:
            # ── NIVEL 2: No hay cierre solo → buscar el par combinado con menor overshoot ──
            mejor_par = None
            mejor_exceso = float('inf')
            lista = sorted(candidatos, key=lambda p: float(p.precio_display))
            for i, p1 in enumerate(lista):
                for p2 in lista[i+1:]:
                    suma = float(p1.precio_display) + float(p2.precio_display)
                    if suma >= falta:
                        exceso = suma - falta
                        if exceso < mejor_exceso:
                            mejor_exceso = exceso
                            mejor_par = [p1, p2]
                        break
            if mejor_par:
                productos_recomendados = mejor_par
                recomendacion_modo = 'combo'
            elif candidatos:
                # ── NIVEL 3: Ningún par cubre — mostrar el más cercano al gap ──
                candidatos.sort(key=lambda p: abs(float(p.precio_display) - falta))
                productos_recomendados = candidatos[:2]
                recomendacion_modo = 'combo_parcial'

    alcanzado = total_carrito >= umbral

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
        # Recomendaciones de upsell
        "productos_recomendados": productos_recomendados,
        "recomendacion_modo": recomendacion_modo,
        "eg_falta_int": int(falta),
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