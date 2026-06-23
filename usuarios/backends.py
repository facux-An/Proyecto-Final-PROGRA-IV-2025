from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

UserModel = get_user_model()

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Permite autenticarse usando tanto el nombre de usuario como el email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        if not username:
            return None
            
        try:
            # Buscar el usuario por username O por email ignorando mayúsculas/minúsculas
            user = UserModel.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            # Ejecuta el hash de la contraseña de todos modos para mitigar ataques de tiempo
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # Si hay varios usuarios con el mismo email, devolvemos el primero
            user = UserModel.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).order_by('id').first()
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
            
        return None
