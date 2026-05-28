import os
import django
from django.core.files import File

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_plus.settings')
django.setup()

from productos.models import Producto

def update_banners():
    base_dir = r"c:\Users\fandr\Desktop\biblioteca_plus\media\imagenes_lanzamiento"
    
    kits_data = [
        {"nombre": "Kit Hogar Sin Pelos", "banner": "banner_kit_hogar.jpg"},
        {"nombre": "Kit Gato Feliz", "banner": "banner_kit_gatito.jpg"},
        {"nombre": "Kit Salud Renal", "banner": "banner_kit_renal.jpg"}
    ]
    
    for data in kits_data:
        try:
            kit = Producto.objects.get(nombre__icontains=data["nombre"])
            img_path = os.path.join(base_dir, data["banner"])
            if os.path.exists(img_path):
                with open(img_path, 'rb') as f:
                    kit.portada.save(data["banner"], File(f), save=True)
                kit.en_oferta = True
                kit.es_combo = True
                kit.save()
                print(f"OK: {kit.nombre} actualizado con banner.")
            else:
                print(f"WARN: Banner no existe {img_path}")
        except Producto.DoesNotExist:
            print(f"ERROR: No se encontro el kit {data['nombre']}")

if __name__ == '__main__':
    update_banners()
