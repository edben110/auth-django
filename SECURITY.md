# Documentación de Seguridad - Autenticación y Hashing de Contraseñas

## 📋 Resumen Ejecutivo

Este proyecto implementa un sistema de autenticación seguro basado en Django que cumple con los estándares de ciberseguridad más rigurosos para proteger las contraseñas de los usuarios.

**Estado**: ✅ TODAS LAS PRUEBAS DE SEGURIDAD PASAN (15/15 tests)

---

## 🔐 Principios de Seguridad Implementados

### 1. Contraseñas NUNCA en Texto Plano

**Evidencia de Test**: `test_password_is_hashed_not_plain_text`

```python
# ✅ CORRECTO
user = User()
user.set_password('PlainTextPassword')
user.save()
# La contraseña se guarda como: pbkdf2_sha256$720000$...

# ❌ INCORRECTO (NO HACER ESTO)
user = User()
user.password = 'PlainTextPassword'
user.save()
# La contraseña estaría en texto plano: ¡INSEGURO!
```

**Algoritmo**: PBKDF2 (Password-Based Key Derivation Function 2)
- **Iterations**: 720,000 (por defecto en Django 5.1)
- **Salt**: Único aleatorio para cada usuario
- **Hash Function**: SHA-256

### 2. Autenticación Segura con `authenticate()`

**Evidencia de Tests**: 
- `test_authenticate_with_username`
- `test_authenticate_with_email`
- `test_authenticate_with_wrong_password`

```python
from django.contrib.auth import authenticate, login

# El usuario puede autenticarse con username O email
user = authenticate(
    request=request,
    username='user@example.com',  # O username
    password='UserPassword123!'
)

if user is not None:
    login(request, user)
    # Django automáticamente:
    # 1. Valida la contraseña vs el hash usando check_password()
    # 2. Crea una sesión segura del lado servidor
    # 3. Guarda session_id en una cookie httpOnly del navegador
```

### 3. Verificación de Contraseña Segura

**Evidencia de Tests**:
- `test_password_check_password_method`
- `test_password_salt_uniqueness`

```python
# Las contraseñas se compraran de forma segura
user = User.objects.get(username='testuser')

# ✅ La contraseña se valida automáticamente contra el hash
if user.check_password('UserPassword123!'):
    print('Contraseña correcta')
else:
    print('Contraseña incorrecta')

# Cada usuario tiene un SALT ÚNICO
# Dos usuarios con la MISMA contraseña tienen DIFERENTES hashes
user1.password  # pbkdf2_sha256$720000$xyz123$... (diferente salt)
user2.password  # pbkdf2_sha256$720000$abc789$... (diferente salt)
```

### 4. Cambio de Contraseña Seguro

**Evidencia de Tests**: `test_set_password_replaces_hash`

```python
from django.contrib.auth import update_session_auth_hash

# Cambiar contraseña
user = request.user
user.set_password('NuevaContraseña123!')
user.save()

# ✅ IMPORTANTE: Mantener la sesión activa después del cambio
# Sin esto, el usuario sería desconectado
update_session_auth_hash(request, user)
```

### 5. Validadores de Contraseña

**Evidencia de Tests**:
- `test_validate_password_too_short`
- `test_validate_password_all_numeric`
- `test_validate_password_strong`

Configuración en [config/settings.py](config/settings.py#L106-L119):

```python
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        # Rechaza contraseñas similares a: username, email, first_name, last_name
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        # Por defecto: mínimo 8 caracteres
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        # Rechaza contraseñas comunes (password, 123456, etc.)
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        # Rechaza contraseñas puramente numéricas (1234567890)
    },
]
```

---

## 🚀 Implementación Segura en el Proyecto

### Registro de Usuario

**Archivo**: [users/views.py](users/views.py#L24-L32)

```python
def register_view(request):
    """Vista para registrar un nuevo usuario."""
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()  # UserCreationForm llama internamente a set_password()
            login(request, user)
            return redirect('home')
```

**Form**: [users/forms.py](users/forms.py#L5-L22)
- Extiende `UserCreationForm` que implementa `set_password()`
- Valida que password1 == password2
- Aplica `AUTH_PASSWORD_VALIDATORS`

### Login

**Archivo**: [users/views.py](users/views.py#L35-L50)

```python
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        # authenticate() usa el EmailBackend + ModelBackend
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)  # Crea sesión segura
            return redirect('home')
```

### Recuperación de Contraseña

**Archivo**: [users/views.py](users/views.py#L107-L250)

Flujo seguro de 3 pasos:
1. **nueva_password_view** (Paso 1): Usuario solicita código
2. **verificar_codigo_view** (Paso 2): Usuario verifica código de email
3. **nueva_password_view** (Paso 3): Usuario establece nueva contraseña

```python
def nueva_password_view(request):
    # ... código de validación ...
    user = User.objects.get(email=email)
    user.set_password(nueva_password)  # ✅ SEGURO: hashea automáticamente
    user.save()
    
    # Limpiar datos sensibles de la sesión
    del request.session['recovery_email']
    del request.session['recovery_code']
    del request.session['code_verified']
```

### Backend de Autenticación Personalizado

**Archivo**: [users/backends.py](users/backends.py)

```python
class EmailBackend(ModelBackend):
    """Permite login con email además de username."""
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            user = User.objects.get(email=username)
        except User.DoesNotExist:
            user = User.objects.get(username=username)
        
        # ✅ check_password() valida contra el hash de forma segura
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
```

---

## ✅ Pruebas de Seguridad

### Ejecutar Todas las Pruebas

```bash
python manage.py test users.tests.UserModelSecurityTests -v 2
```

### Resultados Recientes

```
Ran 15 tests in 30.521s
OK

✅ test_password_is_hashed_not_plain_text
✅ test_password_check_password_method
✅ test_authenticate_with_username
✅ test_authenticate_with_email
✅ test_authenticate_with_wrong_password
✅ test_authenticate_nonexistent_user
✅ test_set_password_replaces_hash
✅ test_password_salt_uniqueness
✅ test_validate_password_too_short
✅ test_validate_password_all_numeric
✅ test_validate_password_all_alpha
✅ test_validate_password_strong
✅ test_password_not_in_session
✅ test_multiple_failed_login_attempts
✅ test_never_save_password_directly
```

---

## 📊 Verificación de Hashing en Base de Datos

### Inspeccionar Hash Guardado

```python
from users.models import User

user = User.objects.get(username='testuser')
print(f"Hash guardado: {user.password}")
# Salida: pbkdf2_sha256$720000$abcdef123456$hashedpasswordhere...

# El hash tiene 4 partes:
# pbkdf2_sha256 - Algoritmo usado
# 720000 - Número de iteraciones
# abcdef123456 - SALT único aleatorio
# hashedpasswordhere... - Resultado del hash
```

### Verificar que NO está en Texto Plano

```python
# ❌ Esto NUNCA debería ser verdadero:
user.password == "MyPlainPassword123"  # False

# ✅ Esto SIEMPRE debería ser verdadero:
user.check_password("MyPlainPassword123")  # True
user.password.startswith("pbkdf2_sha256$")  # True
```

---

## 🛡️ Checklist de Seguridad

### Requisitos Cumplidos

- ✅ Usar sistema nativo de autenticación de Django
- ✅ NO guardar contraseñas en texto plano
- ✅ NO crear funciones manuales de encriptación
- ✅ Usar `set_password()` al crear/cambiar contraseñas
- ✅ Usar `check_password()` / `authenticate()` para validar
- ✅ Verificar que BD almacena hashes, no texto plano
- ✅ Implementar validadores de contraseña
- ✅ Crear pruebas automatizadas de seguridad
- ✅ Usar PBKDF2 con 720,000 iteraciones
- ✅ Usar SALT único para cada usuario
- ✅ Mantener sesión activa después de cambio de contraseña
- ✅ NO almacenar contraseña en sesión
- ✅ EmailBackend para login con email o username

### Prohibido

- ❌ `user.password = "plain_text"` - Guardar sin hashear
- ❌ Crear funciones propias de cifrado
- ❌ Mostrar contraseñas en templates/logs
- ❌ Enviar contraseñas por correo
- ❌ Almacenar contraseña en sesión

---

## 🔍 Configuración de Seguridad Adicional

### settings.py

```python
# Modelo de usuario personalizado
AUTH_USER_MODEL = 'users.User'

# Backends de autenticación (orden importa)
AUTHENTICATION_BACKENDS = [
    'users.backends.EmailBackend',        # Intenta con email primero
    'django.contrib.auth.backends.ModelBackend',  # Luego con username
]

# Redirecciones seguras
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Configuración SMTP para recuperación de contraseña
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

---

## 📚 Referencias Oficiales de Django

- [Django Authentication System](https://docs.djangoproject.com/en/5.1/topics/auth/)
- [Password Management](https://docs.djangoproject.com/en/5.1/topics/auth/passwords/)
- [PBKDF2 Algorithm](https://docs.djangoproject.com/en/5.1/topics/auth/#how-django-stores-passwords)
- [Password Validators](https://docs.djangoproject.com/en/5.1/topics/auth/passwords/#password-validation)

---

## 🚨 Recomendaciones para Producción

### 1. Variables de Entorno

```bash
# NUNCA hardcodear credenciales
SECRET_KEY=<usar variable de entorno>
DEBUG=False
EMAIL_HOST_USER=tu-email@gmail.com
EMAIL_HOST_PASSWORD=<contraseña de app de 16 caracteres>
DATABASE_URL=postgresql://...
```

### 2. HTTPS Obligatorio

```python
# settings.py
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

### 3. Rate Limiting

Implementar rate limiting para:
- Endpoints de login
- Endpoints de recuperación de contraseña
- APIs

### 4. Logging y Monitoreo

```python
# Loguear intentos fallidos de login
import logging
logger = logging.getLogger('security')
logger.warning(f"Failed login attempt: {username}")
```

### 5. Autenticación Multifactor (MFA)

Considerar implementar:
- 2FA con códigos TOTP
- Autenticación por email
- WebAuthn/FIDO2

---

## 📞 Soporte

Para preguntas sobre seguridad de autenticación:
1. Revisa la documentación oficial de Django
2. Ejecuta las pruebas: `python manage.py test users.tests`
3. Inspecciona los hashes en la BD

---

**Última actualización**: 30/04/2026
**Versión de Django**: 5.1
**Estado de Seguridad**: ✅ VALIDADO
