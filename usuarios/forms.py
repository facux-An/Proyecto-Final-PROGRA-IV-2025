from django import forms
from django.contrib.auth.models import User
from .models import PerfilUsuario

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'})
        }

class PerfilForm(forms.ModelForm):
    class Meta:
        model = PerfilUsuario
        fields = ['dni_cuit', 'telefono', 'calle', 'numero', 'piso', 'depto', 'ciudad', 'provincia', 'codigo_postal']
        widgets = {
            'dni_cuit': forms.TextInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'calle': forms.TextInput(attrs={'class': 'form-control'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'piso': forms.TextInput(attrs={'class': 'form-control'}),
            'depto': forms.TextInput(attrs={'class': 'form-control'}),
            'ciudad': forms.TextInput(attrs={'class': 'form-control'}),
            'provincia': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo_postal': forms.TextInput(attrs={'class': 'form-control'})
        }
