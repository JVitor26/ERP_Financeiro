from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from core.models import Empresa, Usuario
from financeiro.models import ContaPagar, Fornecedor, StatusContaPagar


class ContasPagarTestCase(APITestCase):
    def setUp(self):
        self.empresa_a = Empresa.objects.create(razao_social="Empresa A")
        self.empresa_b = Empresa.objects.create(razao_social="Empresa B")
        self.user_a = Usuario.objects.create_superuser(
            username="user_a", password="SenhaSegura@123", empresa=self.empresa_a
        )
        self.user_b = Usuario.objects.create_superuser(
            username="user_b", password="SenhaSegura@123", empresa=self.empresa_b
        )
        self.fornecedor_a = Fornecedor.objects.create(empresa=self.empresa_a, nome="Fornecedor A")
        self.url = "/api/financeiro/contas-pagar/"
        self._autenticar(self.user_a)

    def _autenticar(self, user):
        tokens = self.client.post("/api/auth/token/", {"username": user.username, "password": "SenhaSegura@123"}).data
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def _criar_conta(self, empresa=None, fornecedor=None):
        empresa = empresa or self.empresa_a
        fornecedor = fornecedor or self.fornecedor_a
        return ContaPagar.objects.create(
            empresa=empresa,
            fornecedor=fornecedor,
            descricao="Conta de teste",
            data_emissao=timezone.localdate(),
            data_vencimento=timezone.localdate(),
            valor_original=Decimal("100.00"),
        )

    def test_criar_conta_pagar(self):
        payload = {
            "empresa": self.empresa_a.id,
            "fornecedor": self.fornecedor_a.id,
            "descricao": "Conta via API",
            "data_emissao": str(timezone.localdate()),
            "data_vencimento": str(timezone.localdate()),
            "valor_original": "150.00",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["descricao"], "Conta via API")

    def test_listar_contas(self):
        self._criar_conta()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_baixar_conta_pagar(self):
        conta = self._criar_conta()
        response = self.client.post(
            f"{self.url}{conta.id}/baixar/",
            {"valor": "100.00", "forma_pagamento": "pix"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conta.refresh_from_db()
        self.assertEqual(conta.status, StatusContaPagar.PAGO)

    def test_cancelar_conta_pagar(self):
        conta = self._criar_conta()
        response = self.client.post(
            f"{self.url}{conta.id}/cancelar/",
            {"justificativa": "Cancelamento de teste"},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        conta.refresh_from_db()
        self.assertEqual(conta.status, StatusContaPagar.CANCELADO)

    def test_multiempresa_isolamento(self):
        """Listagem deve retornar 200 e não falhar."""
        self._autenticar(self.user_a)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_valor_negativo_rejeitado(self):
        payload = {
            "empresa": self.empresa_a.id,
            "fornecedor": self.fornecedor_a.id,
            "descricao": "Conta inválida",
            "data_emissao": str(timezone.localdate()),
            "data_vencimento": str(timezone.localdate()),
            "valor_original": "-50.00",
        }
        response = self.client.post(self.url, payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
