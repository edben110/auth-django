# Ejemplos Prácticos de Uso Seguro de Autenticación

## 📌 Ejemplos de Código

### 1. Crear Usuario de Forma Segura

```python
from users.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

# ✅ FORMA CORRECTA

def create_user_safe(username, email, password):
    \"\"\"Crear usuario con contraseña hasheada de forma segura.\"\"\"
    
    # Validar la contraseña según políticas de la app
    try:
        validate_password(password, user=None)
    except ValidationError as e:
        raise ValueError(f"Contraseña inválida: {e.messages}")
    
    # Crear usuario
    user = User.objects.create(
        username=username,
        email=email,
        first_name="",
        last_name=""
    )
    
    # ✅ IMPORTANTE: Usar set_password()
    user.set_password(password)
    user.save()
    
    return user


# ❌ NUNCA HACER ESTO
def create_user_insecure(username, email, password):
    \"\"\"Ejemplo de forma INSEGURA (NO USAR).\"\"\"
    user = User.objects.create(
        username=username,
        email=email,
        password=password  # ❌ GUARDARÁ EN TEXTO PLANO
    )
    # ¡La contraseña se guardará sin hashear en la BD!
    return user
```

---

### 2. Autenticar Usuario

```python
from django.contrib.auth import authenticate, login

# ✅ FORMA CORRECTA

def login_user_safe(request, username, password):
    \"\"\"Autenticar usuario de forma segura.\"\"\"
    
    # authenticate() compara automáticamente la contraseña
    # con el hash guardado en la BD
    user = authenticate(
        request=request,
        username=username,  # Puede ser username o email
        password=password
    )
    
    if user is not None:
        # ✅ login() crea una sesión segura del lado servidor
        login(request, user)
        return {'success': True, 'message': f'Bienvenido {user.username}!'}
    else:
        return {
            'success': False,
            'message': 'Usuario o contraseña incorrectos'
        }


# ❌ NUNCA HACER ESTO
def login_user_insecure(request, username, password):
    \"\"\"Ejemplo de login INSEGURO (NO USAR).\"\"\"
    try:
        user = User.objects.get(username=username)
        
        # ❌ Comparación directa: INSEGURO
        if user.password == password:  # NUNCA HACER ESTO
            login(request, user)
            return True
    except User.DoesNotExist:
        pass
    
    return False
    # Problemas:
    # 1. Las contraseñas estarían en texto plano
    # 2. Comparación no es time-safe (vulnerable a timing attacks)
    # 3. check_password() no se usa
```

---

### 3. Cambiar Contraseña Segura

```python
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.password_validation import validate_password

# ✅ FORMA CORRECTA

def change_password_safe(request, old_password, new_password):
    \"\"\"Cambiar contraseña manteniendo la sesión activa.\"\"\"
    
    user = request.user
    
    # Verificar que la contraseña antigua es correcta
    if not user.check_password(old_password):
        return {'success': False, 'message': 'Contraseña actual incorrecta'}
    
    # Validar la nueva contraseña
    try:
        validate_password(new_password, user=user)
    except ValidationError as e:
        return {'success': False, 'message': str(e)}
    
    # ✅ Cambiar contraseña con set_password()
    user.set_password(new_password)
    user.save()
    
    # ✅ IMPORTANTE: Mantener la sesión activa
    # Sin esto, el usuario sería desconectado después de cambiar contraseña
    update_session_auth_hash(request, user)
    
    return {'success': True, 'message': 'Contraseña actualizada correctamente'}


# ❌ NUNCA HACER ESTO
def change_password_insecure(request, new_password):
    \"\"\"Cambiar contraseña de forma INSEGURA (NO USAR).\"\"\"
    
    user = request.user
    
    # ❌ Asignar directamente sin set_password()
    user.password = new_password  # NUNCA HACER ESTO
    user.save()
    
    # Problema: La contraseña se guarda en texto plano
    # Además, el usuario sería desconectado (sin update_session_auth_hash)
```

---

### 4. Verificar Contraseña

```python
# ✅ FORMA CORRECTA

def verify_password(user, password):
    \"\"\"Verificar si la contraseña de un usuario es correcta.\"\"\"
    return user.check_password(password)

# Ejemplo de uso:
user = User.objects.get(username='john')
if verify_password(user, 'MyPassword123'):
    print('Contraseña correcta')
else:
    print('Contraseña incorrecta')


# ❌ NUNCA HACER ESTO
def verify_password_insecure(user, password):
    \"\"\"Verificación INSEGURA (NO USAR).\"\"\"
    return user.password == password  # ❌ Comparación directa
    # Problemas:
    # 1. Si passwords están en texto plano, esto expone la comparación
    # 2. No es time-safe (vulnerable a timing attacks)
    # 3. El hash nunca será igual al texto plano
```

---

### 5. Crear Vista de Registro (Django)

```python
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth import login
from users.models import User

# ✅ FORMA CORRECTA

class UserRegisterForm(UserCreationForm):
    \"\"\"Formulario de registro que hereda de UserCreationForm.\"\"\"
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    # UserCreationForm automáticamente:
    # 1. Valida que password1 == password2
    # 2. Aplica AUTH_PASSWORD_VALIDATORS
    # 3. Llama a set_password() en form.save()


class RegisterView(View):
    def get(self, request):
        form = UserRegisterForm()
        return render(request, 'register.html', {'form': form})
    
    def post(self, request):
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # ✅ Automáticamente hashea la contraseña
            login(request, user)  # ✅ Crea sesión segura
            return redirect('home')
        return render(request, 'register.html', {'form': form})


# ❌ NUNCA HACER ESTO
class RegisterViewInsecure(View):
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        
        # ❌ Crear usuario sin set_password()
        user = User.objects.create(
            username=username,
            password=password,  # NUNCA HACER ESTO
            email=email
        )
        
        # Problema: La contraseña se guarda en texto plano
```

---

### 6. Personalizar Backend de Autenticación

```python
from django.contrib.auth.backends import ModelBackend
from users.models import User

# ✅ FORMA CORRECTA (Ya implementada)

class EmailBackend(ModelBackend):
    \"\"\"Permite autenticación con email o username.\"\"\"
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Intentar primero con email
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            try:
                # Luego con username
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None
        
        # ✅ check_password() valida de forma segura
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# ❌ NUNCA HACER ESTO
class EmailBackendInsecure(ModelBackend):
    \"\"\"Backend INSEGURO (NO USAR).\"\"\"
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            return None
        
        # ❌ Comparación directa: INSEGURO
        if user.password == password:  # NUNCA HACER ESTO
            return user
        
        return None
```

---

### 7. Validar Contraseña Antes de Guardar

```python
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

# ✅ FORMA CORRECTA

def validate_and_set_password(user, password):
    \"\"\"Validar y establecer contraseña de forma segura.\"\"\"
    
    # Validar según politicas de la app
    try:
        validate_password(password, user=user)
    except ValidationError as e:
        raise ValueError(f"Contraseña inválida: {e.messages}")
    
    # ✅ set_password() hashea automáticamente
    user.set_password(password)
    user.save()
    
    return user


# ❌ NUNCA HACER ESTO
def set_password_insecure(user, password):
    \"\"\"Establecer contraseña sin validar (NO USAR).\"\"\"
    
    # ❌ Sin validación de políticas
    # ❌ Sin set_password()
    user.password = password
    user.save()
    
    # Problemas:
    # 1. Sin validación de fortaleza
    # 2. Contraseña en texto plano
    # 3. Sin hash
```

---

### 8. Manejo de Errores de Autenticación

```python
from django.contrib.auth import authenticate
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
import logging

logger = logging.getLogger('security')

# ✅ FORMA CORRECTA

@require_http_methods(["POST"])
def api_login(request):
    \"\"\"API segura de login con manejo de errores.\"\"\"
    
    username = request.POST.get('username', '').strip()
    password = request.POST.get('password', '')
    
    if not username or not password:
        return JsonResponse(
            {'error': 'Username y password requeridos'},
            status=400
        )
    
    user = authenticate(
        request=request,
        username=username,
        password=password
    )
    
    if user is not None:
        login(request, user)
        return JsonResponse({'success': True})
    else:
        # ✅ NO revelar si el usuario existe o no
        logger.warning(f"Intento de login fallido: {username}")
        return JsonResponse(
            {'error': 'Credenciales inválidas'},
            status=401
        )


# ❌ NUNCA HACER ESTO
@require_http_methods(["POST"])
def api_login_insecure(request):
    \"\"\"API INSEGURA (NO USAR).\"\"\"
    
    username = request.POST.get('username')
    password = request.POST.get('password')
    
    # ❌ Revelar si el usuario existe
    if not User.objects.filter(username=username).exists():
        return JsonResponse({'error': 'Usuario no existe'}, status=404)
    
    user = User.objects.get(username=username)
    
    # ❌ Comparación insegura
    if user.password == password:  # NUNCA HACER ESTO
        login(request, user)
        return JsonResponse({'success': True})
    else:
        # ❌ Revelar que la contraseña es incorrecta
        return JsonResponse({'error': 'Contraseña incorrecta'}, status=401)
```

---

## 🧪 Pruebas Unitarias

```python
from django.test import TestCase
from users.models import User

class UserSecurityTest(TestCase):
    
    def test_password_hashing(self):
        \"\"\"Verificar que las contraseñas se hashean.\"\"\"
        user = User.objects.create(username='test')
        user.set_password('TestPassword123!')
        user.save()
        
        # ✅ La contraseña no es igual al texto plano
        self.assertNotEqual(user.password, 'TestPassword123!')
        
        # ✅ check_password retorna True
        self.assertTrue(user.check_password('TestPassword123!'))
        
        # ✅ check_password retorna False con contraseña incorrecta
        self.assertFalse(user.check_password('WrongPassword'))
    
    def test_authentication(self):
        \"\"\"Verificar que authenticate() funciona correctamente.\"\"\"
        user = User.objects.create(username='test', email='test@example.com')
        user.set_password('TestPassword123!')
        user.save()
        
        # ✅ Autenticar con username
        auth_user = authenticate(username='test', password='TestPassword123!')
        self.assertEqual(auth_user.id, user.id)
        
        # ✅ Autenticar con email
        auth_user = authenticate(username='test@example.com', password='TestPassword123!')
        self.assertEqual(auth_user.id, user.id)
        
        # ✅ Fallar con contraseña incorrecta
        auth_user = authenticate(username='test', password='WrongPassword')
        self.assertIsNone(auth_user)
```

---

## 📊 Comparativa de Seguridad

| Operación | ✅ SEGURO | ❌ INSEGURO |
|-----------|----------|-----------|
| **Crear** | `user.set_password(pwd)` | `user.password = pwd` |
| **Verificar** | `user.check_password(pwd)` | `user.password == pwd` |
| **Autenticar** | `authenticate(...)` | `user.password == pwd` |
| **Cambiar** | `set_password() + update_session_auth_hash()` | `user.password = new_pwd` |
| **Guardar** | Con hash PBKDF2 | En texto plano |
| **Salt** | Único por usuario | Sin salt |

---

## 🚀 Resumen

✅ **Usar siempre**:
- `set_password()` para crear/cambiar contraseñas
- `check_password()` para verificar contraseñas
- `authenticate()` para login
- `update_session_auth_hash()` después de cambios
- `UserCreationForm` para registros

❌ **NUNCA usar**:
- Asignación directa: `user.password = ...`
- Comparación directa: `user.password == ...`
- Crear funciones propias de hashing
- Almacenar contraseñas en sesión
- Mostrar contraseñas en logs/templates
