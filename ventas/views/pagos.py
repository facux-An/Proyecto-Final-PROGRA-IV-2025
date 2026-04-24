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

logger = logging.getLogger(__name__)


@method_decorator(login_required, name='dispatch')
class MetodoPagoView(TemplateView):
    template_name = "pagos/metodo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # ✅ NUEVO: Obtener total DESDE EL CARRITO (el Pedido aún no existe)
        carrito = Carrito.objects.filter(usuario=self.request.user).first()
        total = sum(item.subtotal for item in carrito.items.all()) if carrito else 0
        
        context["total_a_pagar"] = total
        return context

    def post(self, request, *args, **kwargs):
        metodo = request.POST.get("metodo")
        if not metodo:
            messages.warning(request, "⚠️ Debés elegir un método de pago.")
            return self.get(request, *args, **kwargs)

        # ✅ Obtener carrito (aún no fue vaciado)
        carrito = get_object_or_404(Carrito, usuario=request.user)

        if not carrito.items.exists():
            messages.warning(request, "🛒 Tu carrito está vacío.")
            return redirect("carrito:carrito_detail")

        # ✅ PASO 1: Crear el Pedido con sus Detalles de forma ATÓMICA
        try:
            with transaction.atomic():
                # Calcular total del carrito
                total = sum(item.subtotal for item in carrito.items.all())
                
                # Crear cabecera (Pedido)
                pedido = Pedido.objects.create(
                    usuario=request.user,
                    estado="pendiente",
                    metodo_pago=None,  # Se asigna en _procesar_*
                    total=total
                )
                
                # Crear detalles + descontar stock
                for item in carrito.items.select_related("producto"):
                    DetallePedido.objects.create(
                        pedido=pedido,
                        producto=item.producto,
                        cantidad=item.cantidad,
                        precio_unitario=item.producto.precio
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