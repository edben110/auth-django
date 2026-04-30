from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

User = get_user_model()


class EmailBackend(ModelBackend):
    """
    Backend de autenticación personalizado.
    Permite iniciar sesión usando el correo electrónico
    además del nombre de usuario estándar.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Busca al usuario por email y, si no existe, por username.

        Django llama este metodo desde authenticate(). Si las credenciales
        son validas y el usuario esta activo, se retorna el objeto User.
        """
        try:
            # Intentar buscar por email primero
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            try:
                # Si no se encuentra por email, buscar por username
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        """Recupera el usuario autenticado a partir del id guardado en sesion."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
