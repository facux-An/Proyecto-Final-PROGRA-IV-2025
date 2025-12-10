from django import forms
from .models import Producto
import os


# ✅ Widget personalizado para múltiples archivos
class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'stock']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class ProductoPortadaForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["portada"]

    def clean_portada(self):
        file = self.cleaned_data.get("portada")

        if not file:
            raise forms.ValidationError("Debes subir una imagen.")

        # ✅ Validar tamaño máximo (por defecto 5 MB)
        max_size = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))
        if file.size > max_size:
            raise forms.ValidationError("La imagen supera el tamaño máximo permitido (5 MB).")

        # ✅ Validar formatos permitidos
        allowed = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,webp").split(",")
        content_type = file.content_type.lower()

        if not any(content_type == f"image/{fmt}" for fmt in allowed):
            raise forms.ValidationError("Formato no permitido. Usa JPG, JPEG, PNG o WEBP.")

        return file


# ✅ Formulario para subir hasta 5 portadas múltiples
class PortadasMultiplesForm(forms.Form):
    portadas = forms.FileField(
        widget=MultiFileInput(attrs={'class': 'form-control'}),
        required=False
    )

    def clean_portadas(self):
        files = self.files.getlist("portadas") if "portadas" in self.files else []

        # Validar cantidad máxima
        if len(files) > 5:
            raise forms.ValidationError("Podés subir hasta 5 imágenes de portada.")

        # Validar tamaño y formato
        max_size = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))  # 5 MB por defecto
        allowed = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,webp").split(",")

        for f in files:
            if f.size > max_size:
                raise forms.ValidationError(f"La imagen {f.name} supera el tamaño máximo permitido (5 MB).")
            ct = f.content_type.lower()
            if not any(ct == f"image/{fmt}" for fmt in allowed):
                raise forms.ValidationError(f"Formato no permitido en {f.name}. Usa JPG, JPEG, PNG o WEBP.")

        return files
