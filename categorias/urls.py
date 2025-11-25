from django.urls import path
from .views import (
    CategoriaListView,
    CategoriaDetailView,
    CategoriaCreateView,
    CategoriaUpdateView,
    CategoriaDeleteView,
)

app_name = 'categorias'

urlpatterns = [
    # Listado principal
    path('', CategoriaListView.as_view(), name='categoria_list'),

    # Crear nueva categoría
    path('crear/', CategoriaCreateView.as_view(), name='categoria_create'),

    # Detalle de categoría
    path('<int:pk>/', CategoriaDetailView.as_view(), name='categoria_detail'),

    # Editar categoría existente
    path('<int:pk>/editar/', CategoriaUpdateView.as_view(), name='categoria_update'),

    # Eliminar categoría existente
    path('<int:pk>/eliminar/', CategoriaDeleteView.as_view(), name='categoria_delete'),
]
