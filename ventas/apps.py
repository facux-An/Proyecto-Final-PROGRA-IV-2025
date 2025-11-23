from django.apps import AppConfig

class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'
    # Mantener el label antiguo para que las migraciones sigan funcionando
    
