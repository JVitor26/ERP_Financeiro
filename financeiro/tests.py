from datetime import date
from decimal import Decimal

from django.test import TestCase

from core.models import Empresa

from .models import Cliente, ContaBancaria, ContaPagar, ContaReceber, Fornecedor, StatusAprovacao, StatusContaPagar, StatusContaReceber
from .services import (
    BaixaInvalida,
    baixar_conta_pagar,
    cancelar_conta_pagar,
    decidir_aprovacao_pagamento,
    receber_conta_receber,
    renegociar_conta_receber,
    solicitar_aprovacao_pagamento,
)


class ContaPagarTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(razao_social="Empresa Teste")
        self.fornecedor = Fornecedor.objects.create(empresa=self.empresa, nome="Fornecedor Teste")
        self.conta_bancaria = ContaBancaria.objects.create(
            empresa=self.empresa,
            banco="Banco Teste",
            numero="0001",
        )

    def test_baixa_parcial_atualiza_status(self):
        conta = ContaPagar.objects.create(
            empresa=self.empresa,
            fornecedor=self.fornecedor,
            descricao="Servico",
            data_emissao=date(2026, 5, 1),
            data_vencimento=date(2026, 5, 10),
            valor_original=Decimal("100.00"),
            conta_bancaria=self.conta_bancaria,
        )

        baixar_conta_pagar(conta_pagar=conta, valor="40.00", usuario=None)
        conta.refresh_from_db()

        self.assertEqual(conta.status, StatusContaPagar.PAGO_PARCIAL)
        self.assertEqual(conta.valor_pago, Decimal("40.00"))

    def test_nao_permite_baixa_sem_valor(self):
        conta = ContaPagar.objects.create(
            empresa=self.empresa,
            fornecedor=self.fornecedor,
            descricao="Servico",
            data_emissao=date(2026, 5, 1),
            data_vencimento=date(2026, 5, 10),
            valor_original=Decimal("100.00"),
        )

        with self.assertRaises(BaixaInvalida):
            baixar_conta_pagar(conta_pagar=conta, valor="0.00", usuario=None)

    def test_conta_com_aprovacao_pendente_nao_baixa(self):
        conta = ContaPagar.objects.create(
            empresa=self.empresa,
            fornecedor=self.fornecedor,
            descricao="Servico",
            data_emissao=date(2026, 5, 1),
            data_vencimento=date(2026, 5, 10),
            valor_original=Decimal("100.00"),
        )
        solicitar_aprovacao_pagamento(conta_pagar=conta, usuario=None)

        with self.assertRaises(BaixaInvalida):
            baixar_conta_pagar(conta_pagar=conta, valor="10.00", usuario=None)

    def test_aprovacao_pendente_libera_pagamento_agendado(self):
        conta = ContaPagar.objects.create(
            empresa=self.empresa,
            fornecedor=self.fornecedor,
            descricao="Servico",
            data_emissao=date(2026, 5, 1),
            data_vencimento=date(2026, 5, 10),
            valor_original=Decimal("100.00"),
        )
        aprovacao = solicitar_aprovacao_pagamento(conta_pagar=conta, usuario=None)

        decidir_aprovacao_pagamento(aprovacao=aprovacao, usuario=None, aprovado=True, justificativa="ok")
        conta.refresh_from_db()
        aprovacao.refresh_from_db()

        self.assertEqual(aprovacao.status, StatusAprovacao.APROVADO)
        self.assertEqual(conta.status, StatusContaPagar.AGENDADO)

    def test_conta_paga_nao_cancela(self):
        conta = ContaPagar.objects.create(
            empresa=self.empresa,
            fornecedor=self.fornecedor,
            descricao="Servico",
            data_emissao=date(2026, 5, 1),
            data_vencimento=date(2026, 5, 10),
            valor_original=Decimal("100.00"),
            valor_pago=Decimal("100.00"),
            status=StatusContaPagar.PAGO,
        )

        with self.assertRaises(BaixaInvalida):
            cancelar_conta_pagar(conta_pagar=conta, usuario=None, justificativa="teste")


class ContaReceberTests(TestCase):
    def setUp(self):
        self.empresa = Empresa.objects.create(razao_social="Empresa Teste")
        self.cliente = Cliente.objects.create(empresa=self.empresa, nome="Cliente Teste")
        self.conta_bancaria = ContaBancaria.objects.create(
            empresa=self.empresa,
            banco="Banco Teste",
            numero="0001",
        )

    def test_recebimento_parcial_atualiza_status(self):
        conta = ContaReceber.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            descricao="Contrato",
            data_emissao=date(2026, 5, 1),
            data_vencimento=date(2026, 5, 10),
            valor_original=Decimal("200.00"),
            conta_bancaria=self.conta_bancaria,
        )

        receber_conta_receber(conta_receber=conta, valor="50.00", usuario=None)
        conta.refresh_from_db()

        self.assertEqual(conta.status, StatusContaReceber.RECEBIDO_PARCIAL)
        self.assertEqual(conta.valor_recebido, Decimal("50.00"))

    def test_renegociacao_cria_nova_conta(self):
        conta = ContaReceber.objects.create(
            empresa=self.empresa,
            cliente=self.cliente,
            descricao="Contrato",
            data_emissao=date(2026, 5, 1),
            data_vencimento=date(2026, 5, 10),
            valor_original=Decimal("200.00"),
        )

        nova = renegociar_conta_receber(
            conta_receber=conta,
            usuario=None,
            dados={"nova_data_vencimento": date(2026, 6, 10), "valor_original": Decimal("220.00")},
        )
        conta.refresh_from_db()

        self.assertEqual(conta.status, StatusContaReceber.RENEGOCIADO)
        self.assertEqual(nova.conta_original, conta)
