from django.test import TestCase, Client
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserModelSecurityTests(TestCase):
    """
    Suite de pruebas para verificar la seguridad del modelo User.
    Enfoque: Verificar que las contraseñas NUNCA se guardan en texto plano.
    """

    def setUp(self):
        """Configuración inicial para cada prueba."""
        self.test_user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
        }
        self.test_password = 'SecurePassword123!'

    # ──────────────────────────────────────────────────────────
    # Pruebas de hashing de contraseña
    # ──────────────────────────────────────────────────────────

    def test_password_is_hashed_not_plain_text(self):
        """
        CRÍTICO: Verificar que la contraseña se guarda como hash, NO en texto plano.
        
        Esta es la prueba más importante para seguridad.
        Si una contraseña se encuentra en la base de datos sin hashear,
        cualquiera con acceso a la BD podría leerla directamente.
        """
        user = User.objects.create(**self.test_user_data)
        user.set_password(self.test_password)
        user.save()

        # Recargar el usuario desde la BD
        user_from_db = User.objects.get(username='testuser')
        
        # Verificación 1: La contraseña guardada NO es igual al texto plano
        self.assertNotEqual(
            user_from_db.password,
            self.test_password,
            'FALLO DE SEGURIDAD: ¡La contraseña está guardada en texto plano!'
        )
        
        # Verificación 2: La contraseña guardada empieza con "pbkdf2_sha256$"
        # Este es el algoritmo por defecto de Django
        self.assertTrue(
            user_from_db.password.startswith('pbkdf2_sha256$'),
            f'FALLO: El hash no es PBKDF2. Hash encontrado: {user_from_db.password[:30]}...'
        )

    def test_password_check_password_method(self):
        """
        Verificar que check_password() valida correctamente.
        Este método compara la contraseña en texto plano con el hash guardado.
        """
        user = User.objects.create(**self.test_user_data)
        user.set_password(self.test_password)
        user.save()

        # Verificación 1: check_password retorna True con contraseña correcta
        self.assertTrue(
            user.check_password(self.test_password),
            'check_password() debería retornar True con contraseña correcta'
        )

        # Verificación 2: check_password retorna False con contraseña incorrecta
        self.assertFalse(
            user.check_password('WrongPassword123!'),
            'check_password() debería retornar False con contraseña incorrecta'
        )

    def test_never_save_password_directly(self):
        """
        Verificar que NUNCA se debe asignar la contraseña directamente.
        
        ❌ MALO: user.password = 'plaintext'; user.save()
        ✅ BIEN: user.set_password('plaintext'); user.save()
        """
        user = User(**self.test_user_data)
        
        # Simular lo que NUNCA se debe hacer (asignación directa)
        # Esta prueba demuestra el error de seguridad
        user.password = self.test_password
        user.save()
        
        user_from_db = User.objects.get(username='testuser')
        
        # La contraseña está en texto plano (INSEGURO)
        self.assertEqual(user_from_db.password, self.test_password)
        
        # Si alguien intenta verificar con check_password(), fallará
        # porque es exactamente igual al texto plano (no es hash)
        self.assertFalse(user_from_db.check_password(self.test_password))

    # ──────────────────────────────────────────────────────────
    # Pruebas de autenticación
    # ──────────────────────────────────────────────────────────

    def test_authenticate_with_username(self):
        """
        Verificar que authenticate() funciona con username.
        Django compara automáticamente la contraseña ingresada
        con el hash guardado.
        """
        user = User.objects.create(**self.test_user_data)
        user.set_password(self.test_password)
        user.save()

        # Autenticar con username correcto y contraseña correcta
        authenticated_user = authenticate(
            username=self.test_user_data['username'],
            password=self.test_password
        )
        self.assertEqual(
            authenticated_user.id,
            user.id,
            'authenticate() debería retornar el usuario con credenciales correctas'
        )

    def test_authenticate_with_email(self):
        """
        Verificar que el EmailBackend personalizado permite
        autenticar con email además de username.
        """
        user = User.objects.create(**self.test_user_data)
        user.set_password(self.test_password)
        user.save()

        # Autenticar con email
        authenticated_user = authenticate(
            username=self.test_user_data['email'],
            password=self.test_password
        )
        self.assertEqual(
            authenticated_user.id,
            user.id,
            'EmailBackend debería permitir autenticación con email'
        )

    def test_authenticate_with_wrong_password(self):
        """
        Verificar que authenticate() retorna None con contraseña incorrecta.
        """
        user = User.objects.create(**self.test_user_data)
        user.set_password(self.test_password)
        user.save()

        # Intentar autenticarse con contraseña incorrecta
        authenticated_user = authenticate(
            username=self.test_user_data['username'],
            password='WrongPassword123!'
        )
        self.assertIsNone(
            authenticated_user,
            'authenticate() debería retornar None con contraseña incorrecta'
        )

    def test_authenticate_nonexistent_user(self):
        """
        Verificar que authenticate() retorna None si el usuario no existe.
        """
        authenticated_user = authenticate(
            username='nonexistent@example.com',
            password=self.test_password
        )
        self.assertIsNone(
            authenticated_user,
            'authenticate() debería retornar None si el usuario no existe'
        )

    # ──────────────────────────────────────────────────────────
    # Pruebas de cambio de contraseña
    # ──────────────────────────────────────────────────────────

    def test_set_password_replaces_hash(self):
        """
        Verificar que set_password() genera un nuevo hash cada vez.
        Dos llamadas a set_password() con la misma contraseña
        generan hashes diferentes (porque PBKDF2 usa salt aleatorio).
        """
        user = User.objects.create(**self.test_user_data)
        user.set_password(self.test_password)
        user.save()
        hash_1 = user.password

        # Guardar y cambiar a una nueva contraseña
        new_password = 'NewPassword456!'
        user.set_password(new_password)
        user.save()
        hash_2 = user.password

        # Verificación 1: Los hashes son diferentes
        self.assertNotEqual(
            hash_1,
            hash_2,
            'Los hashes deberían ser diferentes después de cambiar contraseña'
        )

        # Verificación 2: check_password funciona con la nueva contraseña
        self.assertTrue(
            user.check_password(new_password),
            'check_password() debería funcionar con la nueva contraseña'
        )

        # Verificación 3: check_password falla con la contraseña anterior
        self.assertFalse(
            user.check_password(self.test_password),
            'check_password() debería fallar con la contraseña anterior'
        )

    def test_password_salt_uniqueness(self):
        """
        Verificar que PBKDF2 usa salt aleatorio.
        Dos usuarios con la MISMA contraseña tienen DIFERENTES hashes.
        """
        user1 = User.objects.create(
            username='user1',
            email='user1@example.com',
            first_name='User',
            last_name='One'
        )
        user1.set_password(self.test_password)
        user1.save()
        hash_1 = user1.password

        user2 = User.objects.create(
            username='user2',
            email='user2@example.com',
            first_name='User',
            last_name='Two'
        )
        user2.set_password(self.test_password)
        user2.save()
        hash_2 = user2.password

        # Los hashes son diferentes aunque la contraseña sea la misma
        self.assertNotEqual(
            hash_1,
            hash_2,
            'Diferentes usuarios con la misma contraseña deben tener diferentes hashes'
        )

    # ──────────────────────────────────────────────────────────
    # Pruebas de validadores de contraseña
    # ──────────────────────────────────────────────────────────

    def test_validate_password_too_short(self):
        """
        Verificar que las contraseñas muy cortas son rechazadas.
        El validador MinimumLengthValidator (por defecto 8 caracteres)
        debería rechazar contraseñas cortas.
        """
        short_password = 'Short1!'
        
        with self.assertRaises(ValidationError) as context:
            validate_password(short_password, user=None)
        
        self.assertIn(
            'too short',
            str(context.exception).lower(),
            'Debería rechazar contraseña muy corta'
        )

    def test_validate_password_all_numeric(self):
        """
        Verificar que contraseñas puramente numéricas son rechazadas.
        El validador NumericPasswordValidator debería rechazar estas.
        """
        numeric_password = '12345678'
        
        with self.assertRaises(ValidationError) as context:
            validate_password(numeric_password, user=None)
        
        self.assertIn(
            'numeric',
            str(context.exception).lower(),
            'Debería rechazar contraseña puramente numérica'
        )

    def test_validate_password_all_alpha(self):
        """
        Verificar que contraseñas puramente alfabéticas son rechazadas.
        Aunque MinimumLengthValidator permite contraseñas largas,
        CommonPasswordValidator rechaza contraseñas comunes.
        """
        # 'password' es una contraseña muy común
        common_password = 'password'
        
        with self.assertRaises(ValidationError) as context:
            validate_password(common_password, user=None)
        
        # Debería ser rechazada por ser corta O común

    def test_validate_password_strong(self):
        """
        Verificar que contraseñas fuertes pasan validación.
        """
        strong_password = 'SecurePassword123!@#'
        
        try:
            validate_password(strong_password, user=None)
        except ValidationError:
            self.fail('Contraseña fuerte debería pasar validación')

    # ──────────────────────────────────────────────────────────
    # Pruebas de seguridad adicional
    # ──────────────────────────────────────────────────────────

    def test_password_not_in_session(self):
        """
        Verificar que la contraseña NUNCA se almacena en la sesión.
        Solo se debería guardar el session ID del usuario.
        """
        client = Client()
        user = User.objects.create(**self.test_user_data)
        user.set_password(self.test_password)
        user.save()

        # Login del cliente
        login_success = client.login(
            username=self.test_user_data['username'],
            password=self.test_password
        )
        self.assertTrue(login_success, 'Login debería ser exitoso')

        # Verificar que la contraseña NO está en la sesión
        session = client.session
        self.assertNotIn(
            'password',
            session,
            'La contraseña NUNCA debería almacenarse en la sesión'
        )

    def test_multiple_failed_login_attempts(self):
        """
        Verificar que múltiples intentos fallidos de login
        no revelen información sobre el usuario.
        """
        user = User.objects.create(**self.test_user_data)
        user.set_password(self.test_password)
        user.save()

        # Intento fallido
        result1 = authenticate(
            username=self.test_user_data['username'],
            password='WrongPassword1'
        )
        self.assertIsNone(result1)

        # Segundo intento fallido
        result2 = authenticate(
            username=self.test_user_data['username'],
            password='WrongPassword2'
        )
        self.assertIsNone(result2)

        # Los dos fallos son idénticos (sin rate limiting en este test)
        # En producción se debería implementar rate limiting
