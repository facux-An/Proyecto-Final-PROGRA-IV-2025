"""
Motor de cotización de envíos con Zipnova (ex Zippin).

Este módulo es la ÚNICA pieza del sistema que habla con la API externa.
Si mañana cambiamos de proveedor (ej. EnvioPack), solo tocamos este archivo.
El resto del proyecto (vistas, templates) no se entera.
"""
import base64
import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# ============================================================
# CONFIGURACIÓN
# ============================================================
ZIPNOVA_API_URL = "https://api.zipnova.com.ar/v2/shipments/quote"
TIMEOUT_SECONDS = 12  # Si Zipnova no responde en 12s, cortamos

# Mapeo de service_type.code → info amigable para el frontend
SERVICE_LABELS = {
    "standard_delivery": {
        "nombre": "Envío a domicilio",
        "icono": "bi-house-door-fill",
        "descripcion": "Recibilo en tu puerta",
    },
    "pickup_point": {
        "nombre": "Retiro en punto de entrega",
        "icono": "bi-shop",
        "descripcion": "Retirá en sucursal cercana",
    },
    "express_delivery": {
        "nombre": "Envío express",
        "icono": "bi-lightning-charge-fill",
        "descripcion": "Entrega rápida a domicilio",
    },
}


def _get_auth_header():
    """Construye el header Basic Auth codificado en Base64."""
    token = settings.ZIPNOVA_API_TOKEN
    secret = settings.ZIPNOVA_API_SECRET
    credentials = base64.b64encode(f"{token}:{secret}".encode()).decode()
    return {
        "Authorization": f"Basic {credentials}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


def cotizar_envio(codigo_postal_destino, items_carrito):
    """
    Cotiza el envío real consultando la API de Zipnova.

    Args:
        codigo_postal_destino: str - CP del cliente (ej. "1425")
        items_carrito: QuerySet de ItemCarrito con select_related("producto")

    Returns:
        dict con la siguiente estructura:
        {
            "ok": True/False,
            "opciones": [
                {
                    "servicio": "standard_delivery",
                    "nombre": "Envío a domicilio",
                    "icono": "bi-house-door-fill",
                    "descripcion": "Recibilo en tu puerta",
                    "transportista": "Correo Argentino",
                    "logo": "https://...",
                    "precio": 7589.0,
                    "plazo_min": 3,
                    "plazo_max": 5,
                    "fecha_estimada": "2026-05-28",
                    "tags": ["cheapest"]
                },
                ...
            ],
            "error": None  # o string con mensaje de error
        }
    """
    # Calcular peso total y dimensiones del paquete más grande
    peso_total = 0
    largo_max = 0
    ancho_max = 0
    alto_total = 0  # Apilamos verticalmente
    valor_declarado = 0

    for item in items_carrito:
        producto = item.producto
        peso_total += producto.peso_gramos * item.cantidad
        largo_max = max(largo_max, producto.largo_cm)
        ancho_max = max(ancho_max, producto.ancho_cm)
        alto_total += producto.alto_cm * item.cantidad
        valor_declarado += float(producto.precio) * item.cantidad

    # Mínimos de seguridad (Zipnova exige weight >= 10g)
    peso_total = max(peso_total, 10)
    largo_max = max(largo_max, 1)
    ancho_max = max(ancho_max, 1)
    alto_total = max(alto_total, 1)

    body = {
        "account_id": int(settings.ZIPNOVA_ACCOUNT_ID),
        "origin": {
            "zipcode": settings.ZIPNOVA_ORIGIN_ZIPCODE,
        },
        "destination": {
            "zipcode": str(codigo_postal_destino),
            "city": "Argentina",
            "state": "Argentina",
        },
        "declared_value": round(valor_declarado, 2),
        "packages": [
            {
                "weight": peso_total,
                "length": largo_max,
                "width": ancho_max,
                "height": alto_total,
                "classification_id": 1,
            }
        ],
    }

    try:
        response = requests.post(
            ZIPNOVA_API_URL,
            headers=_get_auth_header(),
            json=body,
            timeout=TIMEOUT_SECONDS,
        )

        if response.status_code != 200:
            error_data = response.json()
            error_msg = error_data.get("message", "Error desconocido de Zipnova")
            logger.error(f"Zipnova API error {response.status_code}: {error_msg}")
            return {"ok": False, "opciones": [], "error": error_msg}

        data = response.json()
        results = data.get("results", {})
        opciones = []

        for code, info in results.items():
            if not info.get("selectable"):
                continue

            service_type = info.get("service_type", {})
            service_code = service_type.get("code", code)
            labels = SERVICE_LABELS.get(service_code, {
                "nombre": service_type.get("name", code),
                "icono": "bi-box-seam",
                "descripcion": "",
            })

            carrier = info.get("carrier", {})
            amounts = info.get("amounts", {})
            delivery_time = info.get("delivery_time", {})

            # Fecha estimada legible
            fecha_estimada = delivery_time.get("estimated_delivery", "")
            if fecha_estimada:
                fecha_estimada = fecha_estimada[:10]  # "2026-05-28"

            opciones.append({
                "servicio": service_code,
                "nombre": labels["nombre"],
                "icono": labels["icono"],
                "descripcion": labels["descripcion"],
                "transportista": carrier.get("name", ""),
                "logo": carrier.get("logo", ""),
                "precio": amounts.get("price_incl_tax", 0),
                "plazo_min": delivery_time.get("min", 0),
                "plazo_max": delivery_time.get("max", 0),
                "fecha_estimada": fecha_estimada,
                "tags": info.get("tags", []),
            })

        # Ordenar por precio (más barato primero)
        opciones.sort(key=lambda x: x["precio"])

        return {"ok": True, "opciones": opciones, "error": None}

    except requests.Timeout:
        logger.error("Zipnova API timeout")
        return {"ok": False, "opciones": [], "error": "El servicio de envíos tardó demasiado. Intentá de nuevo."}
    except requests.ConnectionError:
        logger.error("Zipnova API connection error")
        return {"ok": False, "opciones": [], "error": "No se pudo conectar con el servicio de envíos."}
    except Exception as e:
        logger.error(f"Zipnova unexpected error: {e}")
        return {"ok": False, "opciones": [], "error": "Error inesperado al cotizar el envío."}
