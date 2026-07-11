# biblioteca_plus/urls.py
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from biblioteca_plus import views
from ventas.views.pagos import ConfirmacionPagoView
# pyrefly: ignore [missing-import]
from django.views.static import serve

urlpatterns = [
    # Health Check (para UptimeRobot)
    path('ping/', views.health_check, name='health_check'),

    # Sentry Debug Route
    path('sentry-debug/', lambda request: 1 / 0, name='sentry_debug'),

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

    # 🚀 Autenticación de terceros (Allauth) - ESTE ES EL CABLE QUE FALTABA
    path('accounts/', include('allauth.urls')),

    # Autenticación Local
    path('login/', auth_views.LoginView.as_view(template_name='auth/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    
    # Recuperación de contraseña (Zoho SMTP)
    path('password_reset/', auth_views.PasswordResetView.as_view(
        template_name='auth/password_reset_form.html',
        html_email_template_name='auth/password_reset_email.html'
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='auth/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='auth/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='auth/password_reset_complete.html'), name='password_reset_complete'),
    
    # Pagos
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