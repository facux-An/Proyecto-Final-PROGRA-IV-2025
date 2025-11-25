from django.urls import path
from ventas.views.pagos import (
    MetodoPagoView,
    ConfirmacionPagoView,
    PagoErrorView,
    PagoPendienteView,
    mercado_pago_webhook,
)

app_name = "pagos"

urlpatterns = [
    path("metodo/", MetodoPagoView.as_view(), name="metodo"),
    path("confirmacion/", ConfirmacionPagoView.as_view(), name="confirmacion"),
    path("error/", PagoErrorView.as_view(), name="error"),
    path("pendiente/", PagoPendienteView.as_view(), name="pendiente"),
    path("webhook/", mercado_pago_webhook, name="webhook"),  
]
