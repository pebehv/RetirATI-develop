# Create your tests here.
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Profile, Publication, Comment, UserSettings
from django.urls import reverse
from django.utils import timezone
import tempfile
from PIL import Image

# Función auxiliar para crear un usuario y perfil de prueba
def create_test_user(username, email, password):    
    user = User.objects.create_user(username=username, email=email, password=password)
    return user, user.profile

class UsuarioBasicoTest(TestCase):
    def setUp(self):
        self.user1, self.profile1 = create_test_user('usuario1', 'user1@example.com', 'testpass123')
        self.user2, self.profile2 = create_test_user('usuario2', 'user2@example.com', 'testpass123')

    def test_creacion_usuario_basico(self):
        """
        Prueba unitaria que verifica que:
        1. Se puede crear un usuario.
        2. Se crea automáticamente un perfil.
        3. Podemos actualizar y verificar los campos del perfil.
        """
        # Actualizar los campos del perfil
        self.profile1.biography = 'Biografía de prueba actualizada'
        self.profile1.birth_date = timezone.now().date()
        self.profile1.national_id = '12345678'
        self.profile1.favorite_color = 'Azul'
        self.profile1.save()

        # Verificar usuario
        self.assertEqual(User.objects.count(), 2) # setUp crea 2 usuarios
        self.assertEqual(self.user1.username, 'usuario1')
        
        # Verificar perfil
        self.assertEqual(Profile.objects.count(), 2)
        self.assertEqual(self.profile1.user.username, 'usuario1')
        self.assertEqual(self.profile1.biography, 'Biografía de prueba actualizada')
        self.assertEqual(self.profile1.national_id, '12345678')
        self.assertEqual(str(self.profile1), f"{self.user1.username}'s Profile")

    def test_sistema_amigos(self):
        """
        Prueba unitaria que verifica:
        1. Que un perfil puede agregar a otro como amigo.
        2. Que la relación es simétrica (si A es amigo de B, entonces B es amigo de A).
        3. Que el contador de amigos se incrementa correctamente.
        """
        # Establecer relación de amistad
        self.profile1.friends.add(self.profile2)
        
        # Verificar que usuario1 tiene a usuario2 como amigo
        self.assertEqual(self.profile1.friends.count(), 1)
        self.assertEqual(self.profile1.friends.first(), self.profile2)
        
        # Verificar que la relación es simétrica (usuario2 también tiene a usuario1 como amigo)
        self.assertEqual(self.profile2.friends.count(), 1)
        self.assertEqual(self.profile2.friends.first(), self.profile1)
        
        # Verificar nombres para mayor claridad
        self.assertEqual(self.profile1.friends.first().user.username, 'usuario2')
        self.assertEqual(self.profile2.friends.first().user.username, 'usuario1')

    def test_sistema_seguimiento(self):
        """
        Prueba unitaria que verifica:
        1. Que un perfil puede seguir a otro.
        2. Que la relación no es simétrica.
        3. Que los contadores de 'following' y 'followers' se actualizan.
        """
        # profile1 sigue a profile2
        self.profile1.following.add(self.profile2)

        # Verificar que profile1 está siguiendo a profile2
        self.assertEqual(self.profile1.following.count(), 1)
        self.assertIn(self.profile2, self.profile1.following.all())

        # Verificar que profile2 tiene un seguidor (profile1)
        self.assertEqual(self.profile2.followers.count(), 1)
        self.assertIn(self.profile1, self.profile2.followers.all())

        # Verificar que la relación no es simétrica (profile2 no sigue a profile1)
        self.assertEqual(self.profile2.following.count(), 0)

class AuthViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123'
        }

    def test_register_view_success(self):
        """Prueba el registro de un nuevo usuario exitosamente."""
        response = self.client.post(reverse('funATIAPP:register'), {
            'email': self.user_data['email'],
            'password': self.user_data['password'],
            'password_confirm': self.user_data['password']
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')
        self.assertTrue(User.objects.filter(email=self.user_data['email']).exists())

    def test_login_logout_view(self):
        """Prueba el flujo completo de login y logout."""
        # Crear usuario para hacer login
        User.objects.create_user(
            username=self.user_data['username'],
            email=self.user_data['email'],
            password=self.user_data['password']
        )
        # Probar login
        response = self.client.post(reverse('funATIAPP:login'), {
            'email': self.user_data['email'],
            'password': self.user_data['password']
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'muro.html')
        self.assertTrue(response.context['user'].is_authenticated)

        # Probar logout
        response = self.client.get(reverse('funATIAPP:logout'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'index.html')
        self.assertFalse(response.context['user'].is_authenticated)

class PublicacionesIntegrationTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user, self.profile = create_test_user('testuser', 'test@example.com', 'testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_flujo_completo_publicacion(self):
        """
        Prueba de integración que verifica:
        1. El usuario puede acceder al muro (muro/).
        2. Puede crear una publicación.
        3. La publicación aparece en su perfil.
        4. La vista de detalle muestra correctamente la publicación.
        """
        # 1. Verificar acceso al muro principal
        response = self.client.get(reverse('funATIAPP:muro'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Muro')
        
        # 2. Crear una publicación
        response = self.client.post(reverse('funATIAPP:muro'), {
            'content': 'Mi primera publicación de prueba',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        
        # Verificar que la publicación existe en la base de datos
        publication = Publication.objects.first()
        self.assertIsNotNone(publication)
        self.assertEqual(publication.content, 'Mi primera publicación de prueba')
        self.assertEqual(publication.profile, self.profile)
        
        # 3. Verificar que la publicación aparece en el perfil
        response = self.client.get(reverse('funATIAPP:profile'))
        self.assertContains(response, 'Mi primera publicación de prueba')
        
        # 4. Verificar vista de detalle de publicación
        response = self.client.get(reverse('funATIAPP:publication_detail', args=[publication.id]))
        self.assertContains(response, 'Mi primera publicación de prueba')
        self.assertContains(response, 'testuser')

    def test_crear_comentario(self):
        """Prueba que un usuario puede comentar en una publicación."""
        publication = Publication.objects.create(profile=self.profile, content="Publicación para comentar")
        
        # Postear un comentario
        response = self.client.post(reverse('funATIAPP:publication_detail', args=[publication.id]), {
            'content': 'Este es un comentario de prueba.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Este es un comentario de prueba.')
        
        # Verificar que el comentario existe en la DB
        comment = Comment.objects.first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.publication, publication)

class PerfilConfigTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user, self.profile = create_test_user('testuser', 'test@example.com', 'testpass123')
        self.user2, self.profile2 = create_test_user('user2', 'user2@example.com', 'testpass123')
        self.client.login(username='testuser', password='testpass123')

    def test_edit_profile_view(self):
        """Prueba que un usuario puede editar su perfil."""
        response = self.client.post(reverse('funATIAPP:edit_profile'), {
            'first_name': 'Usuario',
            'last_name': 'Prueba',
            'email': 'newemail@example.com',
            'biography': 'Una nueva biografía.'
        }, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'perfil-main.html')
        self.assertContains(response, 'Una nueva biografía.')

        # Verificar que los datos se guardaron en la DB
        self.user.refresh_from_db()
        self.profile.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Usuario')
        self.assertEqual(self.user.email, 'newemail@example.com')
        self.assertEqual(self.profile.biography, 'Una nueva biografía.')
