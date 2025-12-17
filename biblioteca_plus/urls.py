# biblioteca_plus/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from biblioteca_plus import views
from ventas.views.pagos import ConfirmacionPagoView
from django.views.static import serve
urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Admin
    path('admin/', admin.site.urls),

    # Apps principales
    path('categorias/', include('categorias.urls')),
    path('productos/', include('productos.urls')),

    # Ventas (incluye submódulos carrito/pedidos/panel)
    path('ventas/', include('ventas.urls')),

    # Usuarios
    path('usuarios/', include('usuarios.urls')),

    # Autenticación
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path("pagos/confirmacion/", ConfirmacionPagoView.as_view(), name="confirmacion"),
    path("ventas/pagos/", include("ventas.urls_pagos")),

]

# Media en desarrollo (solo funciona con DEBUG=True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Red de seguridad para archivos media en producción (Render)
    urlpatterns += [
        path('media/<path:path>', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
