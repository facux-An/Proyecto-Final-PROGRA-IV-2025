from ventas.models import HistorialPedido, PedidoLog


def descontar_stock(producto, cantidad):
    """
    Descuenta stock de un producto.
    Evita valores negativos en caso de error de lógica.
    """
    if cantidad < 0:
        raise ValueError("La cantidad a descontar no puede ser negativa.")
    if producto.stock < cantidad:
        raise ValueError(f"Stock insuficiente para {producto.nombre}. Disponible: {producto.stock}")

    producto.stock -= cantidad
    producto.save()


def registrar_historial(pedido, estado_anterior, estado_nuevo, usuario):
    """
    Registra un cambio de estado en el historial del pedido.
    """
    HistorialPedido.objects.create(
        pedido=pedido,
        estado_anterior=estado_anterior,
        estado_nuevo=estado_nuevo,
        usuario=usuario
    )


def registrar_log(pedido, usuario, accion):
    """
    Registra una acción realizada sobre un pedido (crear, eliminar, entregar, etc.).
    """
    PedidoLog.objects.create(
        pedido=pedido,
        usuario=usuario,
        accion=accion
    )
