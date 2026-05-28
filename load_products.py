import os
import django
from django.core.files import File
from datetime import timedelta
from django.utils import timezone
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_plus.settings')
django.setup()

from productos.models import Producto
from categorias.models import Categoria

def load():
    print("Iniciando carga de productos...")
    
    # Asegurar que existe una categoría
    cat, _ = Categoria.objects.get_or_create(nombre="Accesorios de Gatos", defaults={"descripcion": "Accesorios"})

    # Rutas base
    base_dir = r"c:\Users\fandr\Desktop\biblioteca_plus\media\imagenes_lanzamiento"
    
    productos_data = [
        # --- KITS ---
        {
            "nombre": "Kit Hogar Sin Pelos",
            "descripcion": "Kit completo para eliminar pelos de mascotas de ropa y muebles.",
            "precio": Decimal("25000"),
            "precio_oferta": Decimal("19900"),
            "stock": 50,
            "destacado": True,
            "en_oferta": True,
            "es_combo": True,
            "etiqueta_oferta": "COMBO -20%",
            "productos_incluidos": "Cepillo a Vapor + Rodillo Quitapelusas",
            "peso_gramos": 800,
            "fecha_fin_oferta": timezone.now() + timedelta(days=7),
            "image_filename": "kit_hogar_sin_pelos_usuario.jpg"
        },
        {
            "nombre": "Kit Salud Renal",
            "descripcion": "Fuente de agua automática con filtros de repuesto para mantener a tu gato hidratado.",
            "precio": Decimal("45000"),
            "precio_oferta": Decimal("38000"),
            "stock": 30,
            "destacado": True,
            "en_oferta": True,
            "es_combo": True,
            "etiqueta_oferta": "PACK SALUD",
            "productos_incluidos": "Fuente Automática + 4 Filtros",
            "peso_gramos": 1200,
            "fecha_fin_oferta": timezone.now() + timedelta(days=14),
            "image_filename": "kit_salud_renal_combined.png"
        },
        {
            "nombre": "Kit Gato Feliz",
            "descripcion": "Rascador y juguete interactivo para que tu gato no se aburra.",
            "precio": Decimal("32000"),
            "precio_oferta": Decimal("26500"),
            "stock": 40,
            "destacado": True,
            "en_oferta": True,
            "es_combo": True,
            "etiqueta_oferta": "DIVERSIÓN",
            "productos_incluidos": "Rascador Sisal + Juguete Interactivo",
            "peso_gramos": 2500,
            "fecha_fin_oferta": timezone.now() + timedelta(days=5),
            "image_filename": "kit_gato_feliz_1779987900802.png"
        },
        # --- INDIVIDUALES ---
        {
            "nombre": "Cepillo a Vapor Premium",
            "descripcion": "Cepillo a vapor deslanador para mascotas.",
            "precio": Decimal("18000"),
            "precio_oferta": Decimal("14500"),
            "stock": 100,
            "destacado": False,
            "en_oferta": True,
            "es_combo": False,
            "etiqueta_oferta": "-19% OFF",
            "peso_gramos": 400,
            "fecha_fin_oferta": timezone.now() + timedelta(days=10),
            "image_filename": "producto_cepillo_vapor_usuario.jpg"
        },
        {
            "nombre": "Pelota Interactiva",
            "descripcion": "Juguete interactivo con pelota para gatos.",
            "precio": Decimal("8500"),
            "precio_oferta": None,
            "stock": 150,
            "destacado": False,
            "en_oferta": False,
            "es_combo": False,
            "etiqueta_oferta": "",
            "peso_gramos": 200,
            "image_filename": "producto_juguete_usuario.jpg"
        },
        {
            "nombre": "Rascador de Sisal",
            "descripcion": "Rascador de tamaño mediano ideal para departamentos.",
            "precio": Decimal("25000"),
            "precio_oferta": Decimal("21000"),
            "stock": 60,
            "destacado": False,
            "en_oferta": True,
            "es_combo": False,
            "etiqueta_oferta": "OFERTA",
            "peso_gramos": 2000,
            "fecha_fin_oferta": timezone.now() + timedelta(days=3),
            "image_filename": "producto_rascador_1779987958108.png"
        },
        {
            "nombre": "Fuente de Agua GADNIC",
            "descripcion": "Fuente automática de acero inoxidable.",
            "precio": Decimal("38000"),
            "precio_oferta": None,
            "stock": 8,
            "destacado": False,
            "en_oferta": False,
            "es_combo": False,
            "etiqueta_oferta": "",
            "peso_gramos": 1000,
            "image_filename": "producto_fuente_agua_1779987999594.png"
        },
        {
            "nombre": "Rodillo Quitapelusas",
            "descripcion": "Rodillo para remover pelo de mascotas de la ropa.",
            "precio": Decimal("5000"),
            "precio_oferta": None,
            "stock": 200,
            "destacado": False,
            "en_oferta": False,
            "es_combo": False,
            "etiqueta_oferta": "",
            "peso_gramos": 150,
            "image_filename": "producto_rodillo_1779988012382.png"
        }
    ]

    for data in productos_data:
        image_filename = data.pop("image_filename")
        img_path = os.path.join(base_dir, image_filename)
        
        # Crear o actualizar producto
        p, created = Producto.objects.update_or_create(
            nombre=data["nombre"],
            defaults={**data, "categoria": cat}
        )
        
        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                p.portada.save(image_filename, File(f), save=True)
            print(f"OK: {p.nombre} cargado con imagen.")
        else:
            print(f"WARN: {p.nombre} creado sin imagen ({image_filename} no existe).")

if __name__ == '__main__':
    load()
