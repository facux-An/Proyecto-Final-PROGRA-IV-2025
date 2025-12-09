# ventas/views/resumen.py

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.db.models import Sum
from ventas.models import Pedido

@login_required
def resumen(request):
    usuario = request.user
    estados = ['pendiente', 'pagado', 'enviado', 'entregado', 'cancelado']

    # Filtros opcionales
    estado_f = request.GET.get("estado")
    desde = request.GET.get("desde")
    hasta = request.GET.get("hasta")

    qs_user = Pedido.objects.filter(usuario=usuario)

    if estado_f:
        qs_user = qs_user.filter(estado=estado_f)
    if desde:
        qs_user = qs_user.filter(fecha_pedido__date__gte=desde)
    if hasta:
        qs_user = qs_user.filter(fecha_pedido__date__lte=hasta)

    total_pedidos = qs_user.count()
    stats_estados = {estado: qs_user.filter(estado=estado).count() for estado in estados}

    # Top productos por cantidad
    top_productos = (
        qs_user.values("producto__nombre")
        .annotate(total_cantidad=Sum("cantidad"))
        .order_by("-total_cantidad")[:5]
    )

    # Volumen total (si tenés precio_unitario en el modelo)
    volumen_total = (
        qs_user.aggregate(monto=Sum("cantidad"))
    ).get("monto") or 0

    context = {
        "total_pedidos": total_pedidos,
        "stats_estados": stats_estados,
        "estados": estados,
        "top_productos": top_productos,
        "volumen_total": volumen_total,
        "f_estado": estado_f or "",
        "f_desde": desde or "",
        "f_hasta": hasta or "",
    }
    return render(request, "ventas/resumen.html", context)
