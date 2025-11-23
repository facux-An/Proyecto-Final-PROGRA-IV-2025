from django.urls import path
from ventas.views.pagos import MetodoPagoView, ConfirmacionPagoView

app_name = "pagos"

urlpatterns = [
    path("metodo/", MetodoPagoView.as_view(), name="metodo"),
    path("confirmacion/", ConfirmacionPagoView.as_view(), name="confirmacion"),
]
