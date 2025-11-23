from django.shortcuts import redirect, get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.contrib import messages
from django.http import JsonResponse
from django.conf import settings
import mercadopago,json
from ventas.models import Carrito, Pedido
from ventas.views.helpers import descontar_stock
from django.views.decorators.csrf import csrf_exempt
import mercadopago


@method_decorator(login_required, name='dispatch')
class MetodoPagoView(TemplateView):
    template_name = "pagos/metodo.html"

    def post(self, request, *args, **kwargs):
        metodo = request.POST.get("metodo")
        if not metodo:
            messages.warning(request, "⚠️ Debés elegir un método de pago.")
            return self.get(request, *args, **kwargs)

        carrito = get_object_or_404(Carrito, usuario=request.user)

        if not carrito.items.exists():
            messages.warning(request, "🛒 Tu carrito está vacío.")
            return redirect("carrito:carrito_detail")

        pedidos_creados = []

        for item in carrito.items.select_related("producto"):
            producto = item.producto
            if producto.stock < item.cantidad:
                messages.error(request, f"❌ Stock insuficiente para {producto.nombre}.")
                return redirect("carrito:carrito_detail")

            pedido = Pedido.objects.create(
                producto=producto,
                usuario=request.user,
                cantidad=item.cantidad,
                metodo_pago=metodo,
            )
            descontar_stock(producto, item.cantidad)
            pedidos_creados.append(pedido)

        carrito.items.all().delete()

        # Si el método es MercadoPago, generar preferencia y redirigir
        if metodo.lower() == "mercadopago":
            sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

            # Usamos el primer pedido como referencia
            pedido = pedidos_creados[0]
            preference_data = {
                "items": [{
                    "title": pedido.producto.nombre,
                    "quantity": pedido.cantidad,
                    "unit_price": float(pedido.precio_unitario),
                }],
                "back_urls": {
                    "success": "http://127.0.0.1:8000/ventas/pagos/confirmacion/",
                    "failure": "http://127.0.0.1:8000/ventas/pagos/error/",
                    "pending": "http://127.0.0.1:8000/ventas/pagos/pendiente/"
                },
                "auto_return": "approved",
                "external_reference": str(pedido.id),
            }

            preference_response = sdk.preference().create(preference_data)
            init_point = preference_response["response"]["init_point"]

            return redirect(init_point)

        # Otros métodos (efectivo, transferencia)
        request.session["metodo_pago"] = metodo
        messages.success(request, f"✅ Compra realizada con éxito usando {metodo}.")
        return redirect("pagos:confirmacion")


@method_decorator(login_required, name='dispatch')
class ConfirmacionPagoView(TemplateView):
    template_name = "pagos/confirmacion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        pedido_id = self.request.GET.get("external_reference")
        status = self.request.GET.get("status")

        if pedido_id and status:
            try:
                # Consultar estado real del pago en Mercado Pago
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                payment_info = sdk.payment().search({"external_reference": pedido_id})

                if payment_info["response"]["results"]:
                    pago = payment_info["response"]["results"][0]
                    estado_pago = pago.get("status")

                    if estado_pago == "approved":
                        pedido = Pedido.objects.get(id=pedido_id, usuario=self.request.user)
                        pedido.estado = "pagado"
                        pedido.metodo_pago = "MercadoPago"
                        pedido.save()
                        context["metodo"] = "MercadoPago"
                    else:
                        # Si no está aprobado, mostramos el estado real
                        context["metodo"] = estado_pago.capitalize()
                else:
                    context["metodo"] = "No definido"
            except Pedido.DoesNotExist:
                context["metodo"] = "No definido"
        else:
            # Para métodos distintos a Mercado Pago
            context["metodo"] = self.request.session.get("metodo_pago", "No definido")

        return context
@csrf_exempt
def mercado_pago_webhook(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # ID del pago enviado por Mercado Pago
            pago_id = data.get("data", {}).get("id")

            if pago_id:
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)
                payment_info = sdk.payment().get(pago_id)

                if payment_info["status"] == 200:
                    pago = payment_info["response"]
                    external_reference = pago.get("external_reference")
                    status = pago.get("status")

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