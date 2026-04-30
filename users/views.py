from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random

from .forms import (
    UserRegisterForm,
    RecuperarPasswordForm,
    VerificarCodigoForm,
    NuevaPasswordForm,
)
from .models import User


def register_view(request):
    """Vista para registrar un nuevo usuario."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='users.backends.EmailBackend')
            messages.success(request, f'¡Cuenta creada exitosamente! Bienvenido {user.username}.')
            return redirect('home')
    else:
        form = UserRegisterForm()
    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """
    Vista para iniciar sesión.
    Permite autenticarse con username o email gracias
    al EmailBackend configurado en AUTHENTICATION_BACKENDS.

    Cómo funciona:
    - authenticate() recibe username y password, los pasa a cada backend
      configurado en AUTHENTICATION_BACKENDS hasta que uno retorne un User.
    - login() crea la sesión del usuario en el servidor y guarda
      el session_id en una cookie del navegador.
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'¡Bienvenido {user.username}!')
            next_url = request.GET.get('next', 'home')
            return redirect(next_url)
        else:
            messages.error(request, 'Usuario/correo o contraseña incorrectos.')
    return render(request, 'users/login.html')


def logout_view(request):
    """
    Vista para cerrar sesión.

    Cómo funciona:
    - logout() elimina la sesión del usuario del servidor
      y borra la cookie de sesión del navegador.
    """
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


@login_required
def home_view(request):
    """Vista principal después de iniciar sesión."""
    return render(request, 'users/home.html')


# ──────────────────────────────────────────────────────────
# Vistas de recuperación de contraseña por código de correo
# ──────────────────────────────────────────────────────────
#
# FLUJO COMPLETO:
# 1. recuperar_password_view → El usuario ingresa su email.
#    Se verifica que exista en la BD, se genera un código
#    aleatorio de 6 dígitos, se guarda en la sesión y se
#    envía al correo usando send_mail() de Django.
#
# 2. verificar_codigo_view → El usuario ingresa el código
#    que recibió. Se compara con el guardado en la sesión.
#    Si coincide, se marca como verificado en la sesión.
#
# 3. nueva_password_view → El usuario define su nueva
#    contraseña. Se usa set_password() que hashea la
#    contraseña automáticamente con PBKDF2 de Django.
#    Nunca se guarda en texto plano.
# ──────────────────────────────────────────────────────────


def recuperar_password_view(request):
    """
    Paso 1: Solicitar correo electrónico.

    - Verifica que el email exista en la base de datos.
    - Genera un código aleatorio de 6 dígitos con random.randint().
    - Guarda el código y el email en la sesión de Django (server-side,
      seguro, no accesible desde el navegador).
    - Envía el código al correo usando send_mail().

    Cómo funciona send_mail():
    - send_mail(subject, message, from_email, recipient_list)
    - Usa la configuración SMTP definida en settings.py
    - Se conecta a smtp.gmail.com:587 con TLS
    - Se autentica con EMAIL_HOST_USER y EMAIL_HOST_PASSWORD
    - Envía el correo y cierra la conexión
    """
    if request.method == 'POST':
        form = RecuperarPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']

            # Verificar que el correo exista en la base de datos
            if not User.objects.filter(email=email).exists():
                messages.error(request, 'No existe una cuenta con ese correo electrónico.')
                return render(request, 'users/recuperar_password.html', {'form': form})

            # Generar código aleatorio de 6 dígitos
            codigo = str(random.randint(100000, 999999))

            # Guardar código y email en la sesión (almacenamiento temporal seguro)
            request.session['recovery_email'] = email
            request.session['recovery_code'] = codigo

            # Enviar código por correo electrónico
            try:
                send_mail(
                    subject='Código de recuperación de contraseña',
                    message=f'Tu código de verificación es: {codigo}\n\n'
                            f'Este código es válido para un solo uso.\n'
                            f'Si no solicitaste este cambio, ignora este mensaje.',
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[email],
                    fail_silently=False,
                )
                messages.success(request, 'Se ha enviado un código de verificación a tu correo.')
                return redirect('verificar_codigo')
            except Exception:
                messages.error(
                    request,
                    'Error al enviar el correo. Verifica la configuración SMTP en settings.py.'
                )
    else:
        form = RecuperarPasswordForm()

    return render(request, 'users/recuperar_password.html', {'form': form})


def verificar_codigo_view(request):
    """
    Paso 2: Verificar el código de 6 dígitos.

    - Lee el código guardado en la sesión.
    - Lo compara con el que ingresó el usuario.
    - Si coincide, marca la sesión como 'code_verified' = True
      y redirige al formulario de nueva contraseña.
    - Si no coincide, muestra un mensaje de error.
    """
    # Protección: si no hay email en sesión, el usuario no pasó por el paso 1
    if 'recovery_email' not in request.session:
        messages.warning(request, 'Primero debes solicitar un código de recuperación.')
        return redirect('recuperar_password')

    if request.method == 'POST':
        form = VerificarCodigoForm(request.POST)
        if form.is_valid():
            codigo_ingresado = form.cleaned_data['codigo']
            codigo_guardado = request.session.get('recovery_code')

            if codigo_ingresado == codigo_guardado:
                # Código correcto: marcar como verificado
                request.session['code_verified'] = True
                messages.success(request, 'Código verificado correctamente. Define tu nueva contraseña.')
                return redirect('nueva_password')
            else:
                messages.error(request, 'El código ingresado es incorrecto. Intenta de nuevo.')
    else:
        form = VerificarCodigoForm()

    email = request.session.get('recovery_email', '')
    return render(request, 'users/verificar_codigo.html', {'form': form, 'email': email})


def nueva_password_view(request):
    """
    Paso 3: Establecer nueva contraseña.

    - Verifica que el usuario haya pasado por los pasos 1 y 2.
    - Usa set_password() para actualizar la contraseña.

    Cómo funciona set_password():
    - Recibe la contraseña en texto plano.
    - La hashea automáticamente usando PBKDF2 (algoritmo por defecto de Django).
    - Guarda el hash en el campo password del modelo User.
    - NUNCA se almacena la contraseña en texto plano.
    """
    # Protección: verificar que el código fue validado
    if not request.session.get('code_verified'):
        messages.warning(request, 'Primero debes verificar tu código de recuperación.')
        return redirect('recuperar_password')

    if request.method == 'POST':
        form = NuevaPasswordForm(request.POST)
        if form.is_valid():
            email = request.session.get('recovery_email')
            nueva_password = form.cleaned_data['password1']

            try:
                user = User.objects.get(email=email)
                # set_password() hashea la contraseña automáticamente
                user.set_password(nueva_password)
                user.save()

                # Limpiar datos de recuperación de la sesión
                del request.session['recovery_email']
                del request.session['recovery_code']
                del request.session['code_verified']

                messages.success(request, '¡Contraseña actualizada exitosamente! Ya puedes iniciar sesión.')
                return redirect('login')
            except User.DoesNotExist:
                messages.error(request, 'Error: no se encontró el usuario.')
                return redirect('recuperar_password')
    else:
        form = NuevaPasswordForm()

    return render(request, 'users/nueva_password.html', {'form': form})
