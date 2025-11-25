from django.urls import path
from . import views
from .views import subir_portada
app_name = 'productos'

urlpatterns = [
    path('', views.ProductoListView.as_view(), name='producto_list'),
    path('crear/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('editar/<int:pk>/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('borrar/<int:pk>/', views.ProductoDeleteView.as_view(), name='producto_delete'),
    path('<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),
    path("<int:producto_id>/subir-portada/", subir_portada, name="subir_portada"),
]
