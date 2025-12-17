from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import traceback
import mercadopago
import json

from ventas.models import Carrito, Pedido
from ventas.views.helpers import descontar_stock


@method_decorator(login_required, name='dispatch')
class MetodoPagoView(TemplateView):
    template_name = "pagos/metodo.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        carrito = Carrito.objects.filter(usuario=self.request.user).first()
        
        # Calculamos el total usando el método del modelo si existe, sino con esta lógica
        total = 0
        if carrito:
            total = sum(item.subtotal for item in carrito.items.all()) # Usamos subtotal que ya definiste en el carrito
        
        context["total_a_pagar"] = total
        return context

    def post(self, request, *args, **kwargs):
        metodo = request.POST.get("metodo")
        if not metodo:
            messages.warning(request, "⚠️ Debés elegir un método de pago.")
            return self.get(request, *args, **kwargs)

        carrito = get_object_or_404(Carrito, usuario=request.user)

        if not carrito.items.exists():
            messages.warning(request, "🛒 Tu carrito está vacío.")
            return redirect("carrito:carrito_detail")

        # Validar stock antes de cualquier proceso de pago
        for item in carrito.items.select_related("producto"):
            if item.producto.stock < item.cantidad:
                messages.error(request, f"❌ Stock insuficiente para {item.producto.nombre}.")
                return redirect("carrito:carrito_detail")

        # LÓGICA MERCADO PAGO
        if metodo.lower() == "mercadopago":
            return self._procesar_mercadopago(request, carrito)

        # LÓGICA OTROS MÉTODOS (Efectivo/Transferencia)
        return self._procesar_pedido_directo(request, carrito, metodo)

    def _procesar_mercadopago(self, request, carrito):
        try:
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
            items_mp = []
            for item in carrito.items.select_related("producto"):
                items_mp.append({
                    "title": item.producto.nombre,
                    "quantity": item.cantidad,
                    "unit_price": float(item.producto.precio),
                    "currency_id": "ARS",
                })

            preference_data = {
                "items": items_mp,
                "back_urls": {
                    "success": f"{settings.SITE_URL}/ventas/pagos/confirmacion/",
                    "failure": f"{settings.SITE_URL}/ventas/pagos/error/",
                    "pending": f"{settings.SITE_URL}/ventas/pagos/pendiente/"
                },
                "auto_return": "approved",
                "external_reference": str(request.user.id),
            }

            preference_response = sdk.preference().create(preference_data)
            init_point = preference_response.get("response", {}).get("init_point")

            if init_point:
                return redirect(init_point)
            
            messages.error(request, "❌ No se pudo conectar con Mercado Pago.")
            return redirect("carrito:carrito_detail")

        except Exception as e:
            messages.error(request, f"❌ Error en la plataforma de pago: {str(e)}")
            return redirect("carrito:carrito_detail")

    def _procesar_pedido_directo(self, request, carrito, metodo):
        for item in carrito.items.select_related("producto"):
            Pedido.objects.create(
                producto=item.producto,
                usuario=request.user,
                cantidad=item.cantidad,
                metodo_pago=metodo,
                estado="pendiente",
            )
            descontar_stock(item.producto, item.cantidad)

        carrito.items.all().delete()
        request.session["metodo_pago"] = metodo
        messages.success(request, f"✅ Pedido realizado con éxito usando {metodo}.")
        return redirect("pagos:confirmacion")



class ConfirmacionPagoView(TemplateView):
    template_name = "pagos/confirmacion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Recuperamos el método de pago (desde la URL si es MP, o desde la sesión)
        status = self.request.GET.get("status")
        if status == "approved":
            context["metodo_display"] = "Mercado Pago"
            context["pagado"] = True
        else:
            context["metodo_display"] = self.request.session.get("metodo_pago", "No definido").capitalize()
            context["pagado"] = False

        # Traemos los pedidos recientes del usuario (creados en los últimos 5 minutos)
        # Esto es para mostrar el resumen en esta pantalla.
        from django.utils import timezone
        import datetime
        hace_5_min = timezone.now() - datetime.timedelta(minutes=5)
        
        pedidos = Pedido.objects.filter(usuario=user, fecha_pedido__gte=hace_5_min).select_related('producto')
        context["pedidos"] = pedidos
        
        # Calculamos el total de esos pedidos
        total = sum(p.cantidad * p.producto.precio for p in pedidos)
        context["total_final"] = total
        
        return context


@csrf_exempt
def mercado_pago_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            pago_id = data.get("data", {}).get("id")

            if pago_id:
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                payment_info = sdk.payment().get(pago_id)

                if payment_info["status"] == 200:
                    pago = payment_info["response"]
                    external_reference = pago.get("external_reference")
                    status = pago.get("status")

                    # Este webhook solo actualiza si el pedido ya existe
                    try:
                        pedido = Pedido.objects.get(id=external_reference)
                        pedido.estado = "pagado" if status == "approved" else status
                        pedido.metodo_pago = "MercadoPago"
                        pedido.save()
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