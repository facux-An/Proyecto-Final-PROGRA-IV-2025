from django.urls import path, include

urlpatterns = [
    path('carrito/', include(('ventas.urls_carrito', 'carrito'), namespace='carrito')),
]
