from django.urls import path
from . import views

app_name = "productos"

urlpatterns = [
    path("", views.ProductoListView.as_view(), name="producto_list"),
    path("crear/", views.ProductoCreateView.as_view(), name="producto_create"),
    path("editar/<int:pk>/", views.ProductoUpdateView.as_view(), name="producto_update"),
    path("borrar/<int:pk>/", views.ProductoDeleteView.as_view(), name="producto_delete"),
    path("destacar/<int:pk>/", views.toggle_destacado, name="toggle_destacado"),
    path("<int:pk>/", views.ProductoDetailView.as_view(), name="producto_detail"),
    path("<int:producto_id>/subir-portada/", views.subir_portada, name="subir_portada"),
    # ── Gestión granular de portadas (AJAX, solo staff) ──────────────────
    path("portada/<int:portada_id>/eliminar/", views.eliminar_portada, name="eliminar_portada"),
    path("<int:producto_id>/reordenar-portadas/", views.reordenar_portadas, name="reordenar_portadas"),
]
