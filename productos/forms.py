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
        
class ProductoPortadaForm(forms.Form):
    portada = forms.ImageField(required=True)

    def clean_portada(self):
        file = self.cleaned_data["portada"]
        # Tamaño
        max_size = int(os.getenv("MAX_UPLOAD_SIZE", "5242880"))  # 5MB
        if file.size > max_size:
            raise forms.ValidationError("La imagen supera el tamaño máximo permitido (5 MB).")
        # Formatos
        allowed = os.getenv("ALLOWED_IMAGE_FORMATS", "jpg,jpeg,png,webp").split(",")
        content_type = file.content_type.lower()
        if not any(content_type.endswith(fmt) or f"image/{fmt}" in content_type for fmt in allowed):
            raise forms.ValidationError("Formato no permitido. Usa JPG, JPEG, PNG o WEBP.")
        return file