from django.db import models
from django.conf import settings

class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    
    # Datos Personales extra
    dni_cuit = models.CharField("DNI / CUIT", max_length=20, blank=True, null=True)
    telefono = models.CharField("Teléfono / WhatsApp", max_length=30, blank=True, null=True)
    
    # Direcciones
    calle = models.CharField("Calle", max_length=150, blank=True, null=True)
    numero = models.CharField("Número", max_length=20, blank=True, null=True)
    piso = models.CharField("Piso", max_length=20, blank=True, null=True)
    depto = models.CharField("Depto", max_length=20, blank=True, null=True)
    ciudad = models.CharField("Ciudad / Localidad", max_length=100, blank=True, null=True)
    provincia = models.CharField("Provincia", max_length=100, blank=True, null=True)
    codigo_postal = models.CharField("Código Postal", max_length=20, blank=True, null=True)
    pais = models.CharField("País", max_length=100, default="Argentina", blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.usuario.username}"
