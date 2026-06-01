from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from .models import Empresa, EventLog, LoginAttempt, TipoEvento, Usuario
from .services import registrar_evento


class EventLogTests(TestCase):
    def test_registra_evento_basico(self):
        empresa = Empresa.objects.create(razao_social="Empresa Teste")

        evento = registrar_evento(
            tipo_evento=TipoEvento.CRIACAO,
            empresa=empresa,
            modulo="financeiro",
            tela="contas_pagar",
            acao="criar_lancamento",
        )

        self.assertEqual(evento.empresa, empresa)
        self.assertEqual(evento.modulo, "financeiro")
        self.assertEqual(evento.acao, "criar_lancamento")

    def test_evento_e_imutavel(self):
        empresa = Empresa.objects.create(razao_social="Empresa Teste")
        evento = registrar_evento(
            tipo_evento=TipoEvento.CRIACAO,
            empresa=empresa,
            modulo="core",
            tela="empresas",
            acao="criar",
        )

        evento.acao = "alterar"
        with self.assertRaises(ValueError):
            evento.save()


class AuthTests(TestCase):
    def test_token_login_sucesso(self):
        empresa = Empresa.objects.create(razao_social="Empresa Teste")
        usuario = Usuario.objects.create_user(username="admin", password="Admin@123", empresa=empresa)
        client = APIClient()

        response = client.post(reverse("token_obtain_pair"), {"username": "admin", "password": "Admin@123"}, format="json")

        self.assertEqual(response.status_code, 200)
        self.assertIn("access", response.data)
        usuario.refresh_from_db()
        self.assertIsNotNone(usuario.last_login)

    def test_login_falho_registra_tentativa(self):
        client = APIClient()

        response = client.post(reverse("token_obtain_pair"), {"username": "admin", "password": "errada"}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertEqual(LoginAttempt.objects.get(username="admin").falhas, 1)
        self.assertTrue(EventLog.objects.filter(acao="login_falhou").exists())
