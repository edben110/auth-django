from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm


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
    """Vista para cerrar sesión."""
    logout(request)
    messages.info(request, 'Has cerrado sesión correctamente.')
    return redirect('login')


@login_required
def home_view(request):
    """Vista principal después de iniciar sesión."""
    return render(request, 'users/home.html')
