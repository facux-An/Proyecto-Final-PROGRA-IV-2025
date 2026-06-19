from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import PerfilUsuario

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)
    else:
        # Si el usuario se guarda y no tenía perfil (por ejemplo usuarios antiguos), se crea.
        PerfilUsuario.objects.get_or_create(usuario=instance)
