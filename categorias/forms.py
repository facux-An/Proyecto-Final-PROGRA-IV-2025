from django import forms
from .models import Categoria
import os

class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nombre', 'descripcion', 'imagen']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre de la categoría'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Describe la categoría (opcional)'
            }),
            'imagen': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
                'id': 'id_imagen'
            }),
        }

    def clean_imagen(self):
        """Validar tamaño y formato de la imagen."""
        file = self.cleaned_data.get('imagen')
        
        if not file:
            return file  # Imagen es opcional
        
        # Validar tamaño máximo (5 MB por defecto)
        max_size = int(os.getenv('MAX_UPLOAD_SIZE', '5242880'))
        if file.size > max_size:
            raise forms.ValidationError(
                f'La imagen supera el tamaño máximo permitido (5 MB). '
                f'Tamaño actual: {file.size / 1024 / 1024:.2f} MB'
            )
        
        # Validar formatos permitidos
        allowed = os.getenv('ALLOWED_IMAGE_FORMATS', 'jpg,jpeg,png,webp').split(',')
        content_type = file.content_type.lower()
        
        if not any(content_type == f'image/{fmt}' for fmt in allowed):
            raise forms.ValidationError(
                f'Formato no permitido: {content_type}. '
                f'Usa: JPG, JPEG, PNG o WEBP'
            )
        
        return file
