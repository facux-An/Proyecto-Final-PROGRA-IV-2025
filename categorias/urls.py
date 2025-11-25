from django.urls import path
from .views import (
    CategoriaListView,
    CategoriaCreateView,
    CategoriaUpdateView,
    CategoriaDeleteView,
    CategoriaDetailView,
)

app_name = 'categorias'

urlpatterns = [
    
    path('', CategoriaListView.as_view(), name='categoria_list'),
    path('<int:pk>/', CategoriaDetailView.as_view(), name='categoria_detail'),
    path('crear/', CategoriaCreateView.as_view(), name='categoria_create'),
    path('editar/<int:pk>/', CategoriaUpdateView.as_view(), name='categoria_update'),
    path("<int:pk>/eliminar/", CategoriaDeleteView.as_view(), name="categoria_delete"),
]
