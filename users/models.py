from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Modelo personalizado de usuario.
    Hereda de AbstractUser que ya incluye los campos:
    - username
    - password
    - email
    - first_name
    - last_name
    - is_staff
    - is_superuser
    """
    email = models.EmailField('correo electrónico', unique=True)

    class Meta:
        """Nombres legibles del modelo dentro del panel de administracion."""
        verbose_name = 'usuario'
        verbose_name_plural = 'usuarios'

    def __str__(self):
        """Representacion corta del usuario en admin, logs y consultas."""
        return self.username
