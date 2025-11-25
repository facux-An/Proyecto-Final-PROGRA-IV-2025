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

        if carrito:
            total = sum(
                item.producto.precio * item.cantidad
                for item in carrito.items.select_related("producto")
            )
            context["total_a_pagar"] = total
        else:
            context["total_a_pagar"] = 0

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

        # Validar stock antes de continuar
        for item in carrito.items.select_related("producto"):
            producto = item.producto
            if producto.stock < item.cantidad:
                messages.error(request, f"❌ Stock insuficiente para {producto.nombre}.")
                return redirect("carrito:carrito_detail")

        # Si el método es MercadoPago, generar preferencia y redirigir
        if metodo.lower() == "mercadopago":
            try:
                sdk = mercadopago.SDK(settings.MERCADOPAGO_ACCESS_TOKEN)

                items = []
                for item in carrito.items.select_related("producto"):
                    items.append({
                        "title": item.producto.nombre,
                        "quantity": item.cantidad,
                        "unit_price": float(item.producto.precio),
                        "currency_id": "ARS",
                    })

                preference_data = {
                    "items": items,
                    "back_urls": {
                        "success": f"{settings.SITE_URL}/ventas/pagos/confirmacion/",
                        "failure": f"{settings.SITE_URL}/ventas/pagos/error/",
                        "pending": f"{settings.SITE_URL}/ventas/pagos/pendiente/"
                    },
                    "auto_return": "approved",
                    "external_reference": str(request.user.id),
                }

                preference_response = sdk.preference().create(preference_data)
                print("Respuesta completa de Mercado Pago:", preference_response)

                response = preference_response.get("response", {})
                init_point = response.get("init_point")

                if not init_point:
                    messages.error(request, f"❌ Error al generar preferencia: {response}")
                    return redirect("carrito:carrito_detail")

                messages.info(request, f"🔗 Enlace generado: {init_point}")
                return redirect(init_point)

            except Exception as e:
                print("Error al crear preferencia:", str(e))
                traceback.print_exc()
                messages.error(request, f"❌ Error inesperado: {str(e)}")
                return redirect("carrito:carrito_detail")

        # Otros métodos (efectivo, transferencia): crear pedidos directamente
        pedidos_creados = []
        for item in carrito.items.select_related("producto"):
            producto = item.producto
            pedido = Pedido.objects.create(
                producto=producto,
                usuario=request.user,
                cantidad=item.cantidad,
                metodo_pago=metodo,
                estado="pendiente",
            )
            descontar_stock(producto, item.cantidad)
            pedidos_creados.append(pedido)

        carrito.items.all().delete()

        request.session["metodo_pago"] = metodo
        messages.success(request, f"✅ Compra registrada con éxito usando {metodo}.")
        return redirect("pagos:confirmacion")



@method_decorator(login_required, name='dispatch')
class ConfirmacionPagoView(TemplateView):
    template_name = "pagos/confirmacion.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        user = self.request.user
        carrito = Carrito.objects.filter(usuario=user).first()
        status = self.request.GET.get("status")

        if status == "approved":
            if carrito and carrito.items.exists():
                pedidos_creados = []
                for item in carrito.items.select_related("producto"):
                    producto = item.producto
                    if producto.stock < item.cantidad:
                        messages.error(self.request, f"❌ Stock insuficiente para {producto.nombre}.")
                        context["metodo"] = "MercadoPago"
                        return context

                    pedido = Pedido.objects.create(
                        producto=producto,
                        usuario=user,
                        cantidad=item.cantidad,
                        metodo_pago="MercadoPago",
                        estado="pagado",
                    )
                    descontar_stock(producto, item.cantidad)
                    pedidos_creados.append(pedido)

                carrito.items.all().delete()
            context["metodo"] = "MercadoPago"
        else:
            context["metodo"] = self.request.session.get("metodo_pago", "No definido")

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