from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from ventas.models import Pedido
from productos.models import Producto
from ventas.views.helpers import registrar_historial, registrar_log
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cancela pedidos de Mercado Pago que llevan más de 24hs pendientes y libera su stock.'

    def handle(self, *args, **options):
        # Límite de tiempo: 24 horas hacia atrás
        limite_tiempo = timezone.now() - timedelta(hours=24)

        # Buscar pedidos atrapados
        pedidos_atrapados = Pedido.objects.filter(
            estado='pendiente',
            metodo_pago='Mercado Pago',
            fecha_pedido__lt=limite_tiempo
        )

        cantidad_cancelados = 0

        for pedido in pedidos_atrapados:
            try:
                # Cancelar pedido
                estado_anterior = pedido.estado
                pedido.estado = 'cancelado'
                pedido.save()

                # Devolver el stock de cada detalle
                for detalle in pedido.detalles.all():
                    producto = detalle.producto
                    producto.stock += detalle.cantidad
                    producto.save()
                    self.stdout.write(f"Stock recuperado: +{detalle.cantidad} de '{producto.nombre}'")

                # Registrar Logs
                registrar_historial(pedido, estado_anterior, 'cancelado', None)
                registrar_log(pedido, None, "Cancelación automática por abandono (>24h). Stock liberado.")
                
                cantidad_cancelados += 1
                self.stdout.write(self.style.SUCCESS(f"Pedido #{pedido.id} cancelado con éxito."))
                
            except Exception as e:
                logger.error(f"Error liberando stock del pedido {pedido.id}: {e}")
                self.stdout.write(self.style.ERROR(f"Error en pedido #{pedido.id}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"✅ Proceso finalizado. {cantidad_cancelados} pedidos cancelados."))
