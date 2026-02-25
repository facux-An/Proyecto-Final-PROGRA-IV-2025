from django.urls import path
from ventas.views import pedidos

urlpatterns = [
    # Listado de mis pedidos
    path('', pedidos.PedidoListView.as_view(), name='list'),
    
    # Crear nuevo pedido (si aplica)
    path('nuevo/', pedidos.PedidoCreateView.as_view(), name='create'),
    
    # Detalle de un pedido específico (El Ticket)
    path('<int:pk>/', pedidos.PedidoDetailView.as_view(), name='detail'),
    
    # --- ESTA ES LA LÍNEA QUE FALTABA O ESTABA MAL ---
    # Seguimiento / Historial
    path('<int:pk>/historial/', pedidos.PedidoHistorialView.as_view(), name='historial'),
    
    # Edición (Staff)
    path('editar/<int:pk>/', pedidos.PedidoUpdateView.as_view(), name='update'),
]