# Tienda Plus 🛒🚀

Plataforma de E-commerce desarrollada en **Django (Python)** diseñada con una arquitectura moderna de alta escalabilidad, baja latencia y tolerancia a fallos.

## 🌐 Arquitectura de Producción (High Performance)

Este proyecto está desplegado en un entorno real de producción optimizado para soportar picos de tráfico (ej. campañas virales o Black Friday) minimizando los cuellos de botella.

*   **Hosting Web:** Desplegado en **Fly.io** (Región: São Paulo `gru`) mediante Docker containers. El servidor utiliza **Gunicorn** configurado con 2 workers y 4 threads (`--workers 2 --threads 4 --worker-class gthread`) permitiendo concurrencia real y eliminando errores 502/504 bajo carga intensa.
*   **Base de Datos:** **Neon Serverless Postgres** (Región: AWS sa-east-1, São Paulo). La proximidad geográfica entre la base de datos y la aplicación (ambas en São Paulo) garantiza una latencia de red de ~1 milisegundo en cada consulta SQL. Cuenta con Connection Pooling nativo (PgBouncer) activado.
*   **Almacenamiento de Medios (CDN):** **Cloudinary**. Libera al servidor de la carga de procesar imágenes y las entrega a los usuarios de manera ultra-rápida desde los bordes de la red (Edge CDN).

## 🛠️ Stack Tecnológico

*   **Backend:** Python 3.10, Django 5.2
*   **Base de Datos:** SQLite (Desarrollo) / PostgreSQL (Producción)
*   **Frontend:** HTML5, CSS3 nativo, Bootstrap 5 (con `defer` y `preconnect` hints para optimizar el renderizado inicial). Javascript Vanilla para interacciones DOM y prevención de "Spam Clicks".
*   **Integraciones:** 
    *   **MercadoPago SDK:** Procesamiento seguro de pagos (Webhooks y API).
    *   **Google OAuth2 (django-allauth):** Inicio de sesión con un clic (Social Login).
    *   **Zipnova (ex Zippin):** Cotización y gestión logística de envíos en tiempo real.

## ⚡ Optimizaciones de Rendimiento Clave

1.  **Caché en Memoria RAM (`LocMemCache`):** La vista principal (Home) utiliza caché con un TTL (Time-To-Live) de 10 minutos para las consultas pesadas. El número del carrito de compras también se cachea y se invalida automáticamente usando el sistema de Signals de Django ante mutaciones (Add/Remove).
2.  **Optimización de Queries (ORM):** Uso extensivo de `select_related` y `prefetch_related` para evitar el problema de "N+1 queries" en las vistas de listado de productos y detalles, reduciendo el tráfico de red con Neon.
3.  **UX Anti-Spam (Frontend):** Inyección de un script global interceptor en `base.html` que desactiva botones de `submit` y muestra barras de carga al instante de hacer clic, previniendo múltiples requests simultáneos por impaciencia del usuario.

---
*Desarrollado y optimizado por Facundo Andrada.*
