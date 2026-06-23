from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import threading
import datetime
from .models import PerfilUsuario

@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        PerfilUsuario.objects.create(usuario=instance)
    else:
        # Si el usuario se guarda y no tenía perfil (por ejemplo usuarios antiguos), se crea.
        PerfilUsuario.objects.get_or_create(usuario=instance)


def enviar_correo_asincrono(email_msg):
    try:
        email_msg.send()
    except Exception as e:
        print(f"Error enviando correo de login: {e}")

@receiver(user_logged_in)
def enviar_alerta_login(sender, request, user, **kwargs):
    if not user.email:
        return

    try:
        ip = request.META.get('HTTP_X_FORWARDED_FOR')
        if ip:
            ip = ip.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR', 'Desconocida')

        context = {
            'usuario': user,
            'ip': ip,
            'fecha': datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Desconocido'),
        }

        html_content = render_to_string('usuarios/emails/alerta_login.html', context)
        text_content = strip_tags(html_content)

        asunto = "Nuevo inicio de sesión en tu cuenta de Tienda Plus"
        remitente = getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@tiendaplus.com')

        msg = EmailMultiAlternatives(asunto, text_content, remitente, [user.email])
        msg.attach_alternative(html_content, "text/html")

        threading.Thread(target=enviar_correo_asincrono, args=(msg,)).start()
        
    except Exception as e:
        print(f"Error preparando alerta de login: {e}")
