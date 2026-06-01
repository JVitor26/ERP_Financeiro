from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Empresa, Usuario
from financeiro.models import Cliente, ContaReceber, StatusContaReceber


class ContasReceberTestCase(APITestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(razao_social="Empresa Teste")
        self.user = Usuario.objects.create_superuser(
            username="user_test", password="SenhaSegura@123", empresa=self.empresa
        )
        self.cliente = Cliente.objects.create(empresa=self.empresa, nome="Cliente Teste")
        self.url = "/api/financeiro/contas-receber/"
        tokens = self.client.post("/api/auth/token/", {"username": "user_test", "password": "SenhaSegura@123"}).data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def _criar_conta(self):
        return ContaReceber.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            descricao="Recebivel de teste",
            data_emissao=timezone.localdate(),
            data_vencimento=timezone.localdate(),
            valor_original=Decimal("200.00"),
        )

    def test_criar_conta_receber(self):
        payload = {
            "empresa": self.empresa.id,
            "cliente": self.cliente.id,
            "descricao": "Recebivel via API",
            "data_emissao": str(timezone.localdate()),
            "data_vencimento": str(timezone.localdate()),
            "valor_original": "300.00",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_receber_conta(self):
        conta = self._criar_conta()
        response = self.client.post(
            f"{self.url}{conta.id}/receber/",
            {"valor": "200.00", "forma_recebimento": "pix"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conta.refresh_from_db()
        self.assertEqual(conta.status, StatusContaReceber.RECEBIDO)

    def test_cancelar_conta_receber(self):
        conta = self._criar_conta()
        response = self.client.post(
            f"{self.url}{conta.id}/cancelar/",
            {"justificativa": "Cancelamento de teste"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conta.refresh_from_db()
        self.assertEqual(conta.status, StatusContaReceber.CANCELADO)

    def test_renegociar_conta(self):
        conta = self._criar_conta()
        payload = {
            "nova_data_vencimento": str(timezone.localdate()),
            "valor_original": "180.00",
        }
        response = self.client.post(f"{self.url}{conta.id}/renegociar/", payload)
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_201_CREATED])
        conta.refresh_from_db()
        self.assertEqual(conta.status, StatusContaReceber.RENEGOCIADO)
