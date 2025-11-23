from django.urls import path
from ventas.views.carrito import (
    ver_carrito,
    agregar_al_carrito,
    eliminar_item,
    finalizar_compra,
    carrito_checkout,
)

app_name = "carrito"

urlpatterns = [
    # Vista principal del carrito
    path("", ver_carrito, name="carrito_detail"),

    # Agregar producto al carrito
    path("agregar/<int:producto_id>/", agregar_al_carrito, name="carrito_add"),

    # Eliminar producto del carrito
    path("eliminar/<int:item_id>/", eliminar_item, name="carrito_remove"),

    # Finalizar compra → crea pedidos y descuenta stock
    path("finalizar/", finalizar_compra, name="carrito_finalize"),

    # Checkout → redirige a selección de método de pago
    path("checkout/", carrito_checkout, name="carrito_checkout"),
]
