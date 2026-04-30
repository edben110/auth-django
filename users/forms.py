from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegisterForm(UserCreationForm):
    """
    Formulario de registro basado en UserCreationForm.

    Agrega el correo como campo obligatorio y aplica clases Bootstrap para
    mantener el estilo visual definido en los templates.
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre de usuario'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
        }

    def __init__(self, *args, **kwargs):
        """Personaliza los widgets de password que vienen de UserCreationForm."""
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Contraseña'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmar contraseña'})


# ──────────────────────────────────────────────────────────
# Formularios para recuperación de contraseña
# ──────────────────────────────────────────────────────────

class RecuperarPasswordForm(forms.Form):
    """
    Paso 1: El usuario ingresa su correo electrónico.
    Se verifica que exista en la base de datos antes de enviar el código.
    """
    email = forms.EmailField(
        label='Correo electrónico',
        widget=forms.EmailInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingresa tu correo registrado',
        }),
    )


class VerificarCodigoForm(forms.Form):
    """
    Paso 2: El usuario ingresa el código de 6 dígitos
    que recibió en su correo electrónico.
    """
    codigo = forms.CharField(
        label='Código de verificación',
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'class': 'form-control form-control-lg text-center',
            'placeholder': '000000',
            'maxlength': '6',
            'style': 'letter-spacing: 8px; font-size: 1.5rem; font-weight: bold;',
        }),
    )


class NuevaPasswordForm(forms.Form):
    """
    Paso 3: El usuario define su nueva contraseña.
    Se valida que ambas contraseñas coincidan.
    """
    password1 = forms.CharField(
        label='Nueva contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Ingresa tu nueva contraseña',
        }),
    )
    password2 = forms.CharField(
        label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control form-control-lg',
            'placeholder': 'Repite tu nueva contraseña',
        }),
    )

    def clean(self):
        """Valida que ambas contraseñas sean iguales."""
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Las contraseñas no coinciden.')
        return cleaned_data
