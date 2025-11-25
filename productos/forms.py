from django import forms
from .models import Producto
import os
class ProductoForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ['nombre', 'descripcion', 'categoria', 'precio', 'stock', 'portada']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'portada': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }
        
class ProductoPortadaForm(forms.ModelForm):
    class Meta:
        model = Producto
        fields = ["portada"]

    def clean_portada(self):
        file = self.cleaned_data.get("portada")

        if not file:
            raise forms.ValidationError("Debes subir una imagen.")

        # ✅ Validar tamaño máximo
        max_size = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))  # 5 MB por defecto
        if file.size > max_size:
            raise forms.ValidationError("La imagen supera el tamaño máximo permitido (5 MB).")

        # ✅ Validar formatos permitidos
        allowed = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,webp").split(",")
        content_type = file.content_type.lower()

        if not any(content_type == f"image/{fmt}" for fmt in allowed):
            raise forms.ValidationError("Formato no permitido. Usa JPG, JPEG, PNG o WEBP.")

        return file