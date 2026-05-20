import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'biblioteca_plus.settings')
django.setup()

from categorias.forms import CategoriaForm
from categorias.models import Categoria

# Crear instancia del formulario
form = CategoriaForm()

# Verificar campos
print("=== CAMPOS DEL FORMULARIO CATEGORIAFORM ===")
print(f"Campos incluidos: {list(form.fields.keys())}")
print()

# Verificar cada campo
for field_name, field in form.fields.items():
    print(f"Campo: {field_name}")
    print(f"  - Tipo: {type(field).__name__}")
    print(f"  - Widget: {type(field.widget).__name__}")
    print(f"  - Required: {field.required}")
    print()

# Verificar que el modelo tiene los campos
print("=== CAMPOS DEL MODELO CATEGORIA ===")
for field in Categoria._meta.get_fields():
    if not field.many_to_one and not field.one_to_many and not field.many_to_many:
        print(f"  - {field.name}: {field.get_internal_type()}")
