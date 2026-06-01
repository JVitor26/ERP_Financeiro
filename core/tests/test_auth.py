from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Empresa, Usuario


class AuthTestCase(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(razao_social="Empresa Teste")
        self.user = Usuario.objects.create_superuser(
            username="testuser",
            password="SenhaSegura@123",
            empresa=self.empresa,
        )
        self.login_url = "/api/auth/token/"
        self.me_url = "/api/auth/me/"
        self.refresh_url = "/api/auth/token/refresh/"

    def test_login_sucesso(self):
        response = self.client.post(self.login_url, {"username": "testuser", "password": "SenhaSegura@123"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_senha_errada(self):
        response = self.client.post(self.login_url, {"username": "testuser", "password": "senhaerrada"})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    def test_login_usuario_inexistente(self):
        response = self.client.post(self.login_url, {"username": "naoexiste", "password": "qualquer"})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED])

    def test_me_autenticado(self):
        tokens = self.client.post(self.login_url, {"username": "testuser", "password": "SenhaSegura@123"}).data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "testuser")

    def test_me_sem_autenticacao(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_token(self):
        tokens = self.client.post(self.login_url, {"username": "testuser", "password": "SenhaSegura@123"}).data
        response = self.client.post(self.refresh_url, {"refresh": tokens["refresh"]})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_login_bloqueio_apos_falhas(self):
        from django.conf import settings
        limite = getattr(settings, "LOGIN_FAILURE_LIMIT", 5)
        for _ in range(limite):
            self.client.post(self.login_url, {"username": "testuser", "password": "errada"})
        response = self.client.post(self.login_url, {"username": "testuser", "password": "SenhaSegura@123"})
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])
