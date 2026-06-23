from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import traceback
import mercadopago
import json
import logging

from ventas.models import Carrito, Pedido, DetallePedido
from ventas.views.helpers import descontar_stock, registrar_historial, registrar_log
from ventas.forms import DatosEnvioForm

logger = logging.getLogger(__name__)


# =============================================================
# PASO 1 DEL CHECKOUT: Datos de Envío
# =============================================================
@method_decorator(login_required, name='dispatch')
class DatosEnvioView(TemplateView):
    template_name = "pagos/envio.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrito = Carrito.objects.filter(usuario=self.request.user).first()

        if not carrito or not carrito.items.exists():
            return context

        # Pre-rellenar con datos de sesión si el usuario vuelve atrás
        datos_guardados = self.request.session.get('datos_envio', {})
        form = DatosEnvioForm(initial=datos_guardados)

        envio_cotizado = self.request.session.get('envio_cotizado', {})
        costo_envio = envio_cotizado.get('precio', 0.0)
        subtotal = sum(item.subtotal for item in carrito.items.all())

        context['form'] = form
        context['carrito'] = carrito
        context['subtotal'] = subtotal
        context['costo_envio'] = costo_envio
        context['total_a_pagar'] = float(subtotal) + float(costo_envio)
        return context

    def post(self, request, *args, **kwargs):
        carrito = Carrito.objects.filter(usuario=request.user).first()

        if not carrito or not carrito.items.exists():
            messages.warning(request, "🛒 Tu carrito está vacío.")
            return redirect("carrito:carrito_detail")

        form = DatosEnvioForm(request.POST)

        if form.is_valid():
            # Guardar en sesión (NO crear Pedido todavía)
            request.session['datos_envio'] = form.cleaned_data
            messages.success(request, "✅ Datos de envío guardados. Elegí tu método de pago.")
            return redirect("pagos:metodo")

        # Si hay errores, re-renderizar con los errores
        context = self.get_context_data()
        context['form'] = form
        return self.render_to_response(context)


# =============================================================
# PASO 2 DEL CHECKOUT: Selección de Método de Pago
# =============================================================


@method_decorator(login_required, name='dispatch')
class MetodoPagoView(TemplateView):
    template_name = "pagos/metodo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Obtener total del carrito
        carrito = Carrito.objects.filter(usuario=self.request.user).first()
        subtotal = sum(item.subtotal for item in carrito.items.all()) if carrito else 0
        
        # Obtener datos de envío cotizados en la sesión
        envio_cotizado = self.request.session.get("envio_cotizado", {})
        costo_envio = envio_cotizado.get("precio", 0.0)
        
        context["subtotal"] = subtotal
        context["costo_envio"] = costo_envio
        context["total_a_pagar"] = float(subtotal) + float(costo_envio)
        context["total_con_descuento"] = round((float(subtotal) + float(costo_envio)) * 0.90, 2)
        return context

    def post(self, request, *args, **kwargs):
        metodo = request.POST.get("metodo")
        if not metodo:
            messages.warning(request, "⚠️ Debés elegir un método de pago.")
            return self.get(request, *args, **kwargs)

        # Obtener carrito
        carrito = get_object_or_404(Carrito, usuario=request.user)

        if not carrito.items.exists():
            messages.warning(request, "🛒 Tu carrito está vacío.")
            return redirect("carrito:carrito_detail")

        try:
            with transaction.atomic():
                # Calcular total del carrito
                subtotal = sum(item.subtotal for item in carrito.items.all())
                
                # Datos de envío
                datos_envio = request.session.get('datos_envio', {})
                envio_cotizado = request.session.get("envio_cotizado", {})
                costo_envio = envio_cotizado.get("precio", 0.0)
                metodo_envio = envio_cotizado.get("nombre", "")
                
                total_base = float(subtotal) + float(costo_envio)

                # Aplicar descuento del 10% si el cliente eligió transferencia bancaria
                if metodo.lower() == "transferencia":
                    total_final = round(total_base * 0.90, 2)
                else:
                    total_final = total_base
                
                # Crear cabecera (Pedido)
                pedido = Pedido.objects.create(
                    usuario=request.user,
                    estado="pendiente",
                    metodo_pago=None,
                    total=total_final,
                    costo_envio=costo_envio,
                    metodo_envio=metodo_envio,
                    nombre_envio=datos_envio.get('nombre_envio', ''),
                    email_envio=datos_envio.get('email_envio', ''),
                    telefono_envio=datos_envio.get('telefono_envio', ''),
                    direccion_envio=datos_envio.get('direccion_envio', ''),
                    numero_envio=datos_envio.get('numero_envio', ''),
                    piso_envio=datos_envio.get('piso_envio', ''),
                    depto_envio=datos_envio.get('depto_envio', ''),
                    ciudad_envio=datos_envio.get('ciudad_envio', ''),
                    provincia_envio=datos_envio.get('provincia_envio', ''),
                    codigo_postal_envio=datos_envio.get('codigo_postal_envio', ''),
                    notas_envio=datos_envio.get('notas_envio', ''),
                )
                
                # Crear detalles + descontar stock
                for item in carrito.items.select_related("producto"):
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=item.producto,
                        cantidad=item.cantidad,
                        precio_unitario=item.producto.precio_display
                    )
                    # Descontar stock
                    descontar_stock(item.producto, item.cantidad)
                
                # Registrar en historial
                registrar_historial(pedido, "", "pendiente", request.user)
                registrar_log(pedido, request.user, "Carrito convertido a Pedido")
                
        except Exception as e:
            messages.error(request, f"❌ Error al crear el pedido: {str(e)}")
            print(f"🔴 ERROR creando Pedido en post(): {str(e)}")
            traceback.print_exc()
            return redirect("carrito:carrito_detail")

        # ✅ PASO 2: Procesar según el método elegido
        if metodo.lower() == "mercadopago":
            return self._procesar_mercadopago(request, pedido, carrito)

        # LÓGICA OTROS MÉTODOS (Efectivo/Transferencia)
        return self._procesar_pedido_directo(request, pedido, carrito, metodo)

    def _procesar_mercadopago(self, request, pedido, carrito):
        """
        Procesa pago en Mercado Pago.
        El Pedido ya está creado con su método_pago = None.
        Aquí solo se prepara la integración con MP.
        """
        try:
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            items_mp = []
            
            # Obtenemos items desde DetallePedido (ya fueron creados en post())
            for detalle in pedido.detalles.select_related("producto"):
                items_mp.append({
                    "title": detalle.producto.nombre,
                    "quantity": detalle.cantidad,
                    "unit_price": float(detalle.precio_unitario),
                    "currency_id": "ARS",
                })
                
            # ✅ Agregar el costo de envío como un ítem más si es mayor a 0
            if pedido.costo_envio and float(pedido.costo_envio) > 0:
                items_mp.append({
                    "title": f"Envío: {pedido.metodo_envio}",
                    "quantity": 1,
                    "unit_price": float(pedido.costo_envio),
                    "currency_id": "ARS",
                })

            preference_data = {
                "items": items_mp,
                "back_urls": {
                    "success": f"{settings.SITE_URL}/ventas/pagos/confirmacion/?status=approved&pedido_id={pedido.id}",
                    "failure": f"{settings.SITE_URL}/ventas/pagos/error/?status=failure&pedido_id={pedido.id}",
                    "pending": f"{settings.SITE_URL}/ventas/pagos/pendiente/?status=pending&pedido_id={pedido.id}"
                },
                "auto_return": "approved",
                "external_reference": str(pedido.id),
            }

            preference_response = sdk.preference().create(preference_data)
            init_point = preference_response.get("response", {}).get("init_point")

            if init_point:
                # Actualizar método de pago
                pedido.metodo_pago = "Mercado Pago"
                pedido.save()
                
                # Vaciar carrito
                carrito.items.all().delete()
                
                return redirect(init_point)
            
            messages.error(request, "❌ No se pudo conectar con Mercado Pago.")
            return redirect("carrito:carrito_detail")

        except Exception as e:
            print(f"\n🔴 ERROR EN _procesar_mercadopago: {str(e)}")
            traceback.print_exc()
            logger.error(f"Error procesando Mercado Pago: {str(e)}", exc_info=True)
            
            messages.error(request, f"❌ Error en la plataforma de pago: {str(e)}")
            return redirect("carrito:carrito_detail")

    def _procesar_pedido_directo(self, request, pedido, carrito, metodo):
        """
        Procesa pago directo (transferencia/efectivo).
        El Pedido ya está creado, solo actualiza el método y redirige.
        """
        try:
            # Actualizar metodo_pago
            pedido.metodo_pago = metodo
            
            # Si es transferencia, marca estado especial
            if metodo.lower() == "transferencia":
                pedido.estado = "pendiente_transferencia"
                registrar_historial(pedido, "pendiente", "pendiente_transferencia", request.user)
                registrar_log(pedido, request.user, "Pago por transferencia iniciado")
            else:
                registrar_log(pedido, request.user, f"Pago por {metodo} seleccionado")
            
            pedido.save()
            
            # Vaciar carrito
            carrito.items.all().delete()
            
            # Guardar en sesión para referencia
            request.session["metodo_pago"] = metodo
            request.session["pedido_id"] = pedido.id
            
            messages.success(request, f"✅ Pedido realizado. Método: {metodo}.")
            return redirect("pagos:confirmacion")
        
        except Exception as e:
            print(f"\n🔴 ERROR EN _procesar_pedido_directo: {str(e)}")
            print(f"Tipo de error: {type(e).__name__}")
            traceback.print_exc()
            logger.error(f"Error procesando pedido directo: {str(e)}", exc_info=True)
            
            messages.error(request, f"❌ Error: {str(e)}")
            return redirect("carrito:carrito_detail")



class ConfirmacionPagoView(TemplateView):
    template_name = "pagos/confirmacion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # ✅ NUEVO: Obtener el pedido desde la URL o sesión
        pedido_id = self.request.GET.get("pedido_id") or self.request.session.get("pedido_id")
        
        if not pedido_id:
            context["error"] = "No se encontró información del pedido."
            return context
        
        try:
            pedido = Pedido.objects.prefetch_related("detalles__producto").get(
                id=pedido_id,
                usuario=user
            )
        except Pedido.DoesNotExist:
            context["error"] = "Pedido no encontrado."
            return context
        
        # Recuperar el método de pago (desde MP, o desde la sesión)
        status = self.request.GET.get("status")
        
        if status == "approved":
            # ✅ Pago aprobado en Mercado Pago
            pedido.estado = "pagado"
            pedido.save()
            registrar_historial(pedido, "pendiente", "pagado", user)
            context["metodo_display"] = "Mercado Pago"
            context["pagado"] = True
        else:
            # Otros métodos (transferencia/efectivo)
            context["metodo_display"] = pedido.metodo_pago or "No definido"
            # Los estados son: pendiente, pendiente_transferencia, etc.
            context["pagado"] = pedido.estado in ["pagado", "entregado"]
        
        # ✅ Mostrar detalles del pedido
        context["pedido"] = pedido
        context["total_final"] = pedido.total  # Ya está calculado en la BD
        
        return context


@method_decorator(login_required, name='dispatch')
class ReintentarPagoMP(TemplateView):
    """
    Permite que un cliente reintente el pago de un pedido que quedó
    en estado 'pendiente' con método 'Mercado Pago'.

    Flujo seguro:
      1. Verifica que el pedido exista, sea del usuario autenticado
         y esté en estado 'pendiente' con MP como método de pago.
      2. Construye una nueva preferencia de MP usando los DetallePedido
         ya guardados en la base de datos (NO se toca el stock ni se
         crea ningún pedido nuevo).
      3. Redirige al init_point de MP, igual que en el flujo original.
    """

    def get(self, request, pedido_id, *args, **kwargs):
        # ── Obtener y validar el pedido ──────────────────────────────────
        pedido = get_object_or_404(
            Pedido,
            id=pedido_id,
            usuario=request.user,          # Seguridad: solo el dueño
            estado="pendiente",             # Solo pedidos aún pendientes
            metodo_pago="Mercado Pago",    # Solo si ya había elegido MP
        )

        detalles = pedido.detalles.select_related("producto").all()
        if not detalles.exists():
            messages.error(request, "❌ El pedido no tiene productos. Contactá con soporte.")
            return redirect("pedidos:list")

        # ── Construir la preferencia de Mercado Pago ─────────────────────
        try:
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

            items_mp = []
            for detalle in detalles:
                items_mp.append({
                    "title": detalle.producto.nombre,
                    "quantity": detalle.cantidad,
                    "unit_price": float(detalle.precio_unitario),
                    "currency_id": "ARS",
                })

            # Agregar envio si aplica
            if pedido.costo_envio and float(pedido.costo_envio) > 0:
                items_mp.append({
                    "title": f"Envío: {pedido.metodo_envio or 'Envío'}",
                    "quantity": 1,
                    "unit_price": float(pedido.costo_envio),
                    "currency_id": "ARS",
                })

            preference_data = {
                "items": items_mp,
                "back_urls": {
                    "success": f"{settings.SITE_URL}/ventas/pagos/confirmacion/?status=approved&pedido_id={pedido.id}",
                    "failure": f"{settings.SITE_URL}/ventas/pagos/error/?status=failure&pedido_id={pedido.id}",
                    "pending": f"{settings.SITE_URL}/ventas/pagos/pendiente/?status=pending&pedido_id={pedido.id}",
                },
                "auto_return": "approved",
                "external_reference": str(pedido.id),  # El mismo pedido — el webhook lo actualizará
            }

            preference_response = sdk.preference().create(preference_data)
            init_point = preference_response.get("response", {}).get("init_point")

            if init_point:
                registrar_log(pedido, request.user, "Reintento de pago via Mercado Pago")
                return redirect(init_point)

            messages.error(request, "❌ No se pudo conectar con Mercado Pago. Intentá más tarde.")
            return redirect("pedidos:list")

        except Exception as e:
            logger.error(f"Error en ReintentarPagoMP (pedido {pedido.id}): {str(e)}", exc_info=True)
            messages.error(request, f"❌ Error al reintentar el pago: {str(e)}")
            return redirect("pedidos:list")


@csrf_exempt
def mercado_pago_webhook(request):
    """
    Webhook de Mercado Pago.
    Actualiza el estado del pedido cuando MP notifica el resultado del pago.
    """
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            pago_id = data.get("data", {}).get("id")

            if pago_id:
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                payment_info = sdk.payment().get(pago_id)

                if payment_info["status"] == 200:
                    pago = payment_info["response"]
                    pedido_id = pago.get("external_reference")  # ✅ Es el pedido.id
                    status = pago.get("status")

                    try:
                        pedido = Pedido.objects.get(id=pedido_id)
                        
                        # Mapear estado de MP a nuestro sistema
                        estado_nuevo = {
                            "approved": "pagado",
                            "pending": "pendiente",
                            "rejected": "cancelado",
                            "cancelled": "cancelado",
                        }.get(status, status)
                        
                        estado_anterior = pedido.estado
                        pedido.estado = estado_nuevo
                        pedido.metodo_pago = "Mercado Pago"
                        pedido.save()
                        
                        # Registrar cambio
                        registrar_historial(pedido, estado_anterior, estado_nuevo, None)
                        registrar_log(pedido, None, f"Webhook MP: {status} → {estado_nuevo}")
                    
                    except Pedido.DoesNotExist:
                        pass

            return JsonResponse({"status": "ok"})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Método no permitido"}, status=405)

class PagoErrorView(TemplateView):
    template_name = "pagos/error.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Si venís desde MP, podés leer el status y motivo
        context["status"] = self.request.GET.get("status", "failure")
        context["detail"] = self.request.GET.get("message", "El pago fue rechazado o cancelado.")
        return context


class PagoPendienteView(TemplateView):
    template_name = "pagos/pendiente.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Estado típico: "pending"
        context["status"] = self.request.GET.get("status", "pending")
        context["detail"] = "Tu pago está en revisión. Te notificaremos cuando se apruebe."
        return context