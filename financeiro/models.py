from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from core.models import Empresa, TimeStampedModel


class TipoPessoa(models.TextChoices):
    FISICA = "fisica", "Fisica"
    JURIDICA = "juridica", "Juridica"


class StatusContaPagar(models.TextChoices):
    ABERTO = "aberto", "Aberto"
    A_VENCER = "a_vencer", "A vencer"
    VENCIDO = "vencido", "Vencido"
    PAGO = "pago", "Pago"
    PAGO_PARCIAL = "pago_parcial", "Pago parcial"
    CANCELADO = "cancelado", "Cancelado"
    EM_APROVACAO = "em_aprovacao", "Em aprovacao"
    REPROVADO = "reprovado", "Reprovado"
    AGENDADO = "agendado", "Agendado"


class StatusContaReceber(models.TextChoices):
    ABERTO = "aberto", "Aberto"
    A_VENCER = "a_vencer", "A vencer"
    VENCIDO = "vencido", "Vencido"
    RECEBIDO = "recebido", "Recebido"
    RECEBIDO_PARCIAL = "recebido_parcial", "Recebido parcial"
    CANCELADO = "cancelado", "Cancelado"
    RENEGOCIADO = "renegociado", "Renegociado"
    EM_COBRANCA = "em_cobranca", "Em cobranca"
    JUDICIAL = "judicial", "Judicial"
    PROTESTADO = "protestado", "Protestado"


class TipoPlanoConta(models.TextChoices):
    RECEITA = "receita", "Receita"
    DESPESA = "despesa", "Despesa"
    CUSTO = "custo", "Custo"
    INVESTIMENTO = "investimento", "Investimento"
    IMPOSTO = "imposto", "Imposto"
    TAXA = "taxa", "Taxa"
    COMISSAO = "comissao", "Comissao"
    REPASSE = "repasse", "Repasse"
    FINANCIAMENTO = "financiamento", "Financiamento"
    EMPRESTIMO = "emprestimo", "Emprestimo"


class TipoMovimentacao(models.TextChoices):
    ENTRADA = "entrada", "Entrada"
    SAIDA = "saida", "Saida"


class StatusConciliacao(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    SUGERIDA = "sugerida", "Sugerida"
    CONCILIADA = "conciliada", "Conciliada"
    DIVERGENTE = "divergente", "Divergente"
    DUPLICADA = "duplicada", "Duplicada"


class StatusAprovacao(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    APROVADO = "aprovado", "Aprovado"
    REPROVADO = "reprovado", "Reprovado"
    CANCELADO = "cancelado", "Cancelado"


class StatusRelatorio(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    PROCESSANDO = "processando", "Processando"
    PRONTO = "pronto", "Pronto"
    FALHOU = "falhou", "Falhou"


class CentroCusto(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="centros_custo")
    codigo = models.CharField(max_length=40)
    nome = models.CharField(max_length=120)
    pai = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="filhos")
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["codigo", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_centro_custo_empresa_codigo",
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class PlanoConta(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="plano_contas")
    codigo = models.CharField(max_length=40)
    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=30, choices=TipoPlanoConta.choices)
    pai = models.ForeignKey("self", on_delete=models.PROTECT, null=True, blank=True, related_name="filhos")
    vincula_dre = models.BooleanField(default=True)
    vincula_fluxo_caixa = models.BooleanField(default=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["codigo", "nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_plano_conta_empresa_codigo",
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class ContaBancaria(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="contas_bancarias")
    banco = models.CharField(max_length=80)
    agencia = models.CharField(max_length=20, blank=True)
    numero = models.CharField(max_length=40)
    descricao = models.CharField(max_length=120, blank=True)
    saldo_inicial = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    ativa = models.BooleanField(default=True)

    class Meta:
        ordering = ["banco", "numero"]

    def __str__(self):
        return f"{self.banco} - {self.numero}"


class Cliente(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="clientes")
    nome = models.CharField(max_length=180)
    tipo_pessoa = models.CharField(max_length=20, choices=TipoPessoa.choices, default=TipoPessoa.JURIDICA)
    documento = models.CharField(max_length=18, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    ativo = models.BooleanField(default=True)
    metadados = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["nome"]
        indexes = [models.Index(fields=["empresa", "documento"])]

    def __str__(self):
        return self.nome


class Fornecedor(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="fornecedores")
    nome = models.CharField(max_length=180)
    tipo_pessoa = models.CharField(max_length=20, choices=TipoPessoa.choices, default=TipoPessoa.JURIDICA)
    documento = models.CharField(max_length=18, blank=True)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=30, blank=True)
    ativo = models.BooleanField(default=True)
    metadados = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["nome"]
        indexes = [models.Index(fields=["empresa", "documento"])]

    def __str__(self):
        return self.nome


class Servico(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="servicos")
    codigo = models.CharField(max_length=40, blank=True)
    nome = models.CharField(max_length=160)
    descricao = models.TextField(blank=True)
    valor_padrao = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    plano_conta = models.ForeignKey(PlanoConta, on_delete=models.PROTECT, null=True, blank=True, related_name="servicos")
    ativo = models.BooleanField(default=True)
    metadados = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                condition=~models.Q(codigo=""),
                name="uniq_servico_empresa_codigo",
            )
        ]
        indexes = [models.Index(fields=["empresa", "nome"])]

    def __str__(self):
        return self.nome


class LancamentoFinanceiroBase(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.PROTECT)
    descricao = models.CharField(max_length=180)
    data_emissao = models.DateField()
    data_vencimento = models.DateField()
    valor_original = models.DecimalField(max_digits=14, decimal_places=2)
    desconto = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    juros = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    multa = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    acrescimo = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True)
    plano_conta = models.ForeignKey(PlanoConta, on_delete=models.PROTECT, null=True, blank=True)
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, null=True, blank=True)
    observacao = models.TextField(blank=True)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_responsavel",
    )
    excluido_logicamente = models.BooleanField(default=False)
    excluido_em = models.DateTimeField(null=True, blank=True)
    excluido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="%(class)s_exclusoes",
    )

    class Meta:
        abstract = True

    @property
    def valor_total(self):
        return self.valor_original + self.juros + self.multa + self.acrescimo - self.desconto

    def clean(self):
        super().clean()
        campos_monetarios = ["valor_original", "desconto", "juros", "multa", "acrescimo"]
        for campo in campos_monetarios:
            valor = getattr(self, campo)
            if valor is not None and valor < 0:
                raise ValidationError({campo: "Valor nao pode ser negativo."})
        if self.valor_original is not None and self.valor_original <= 0:
            raise ValidationError({"valor_original": "Valor original deve ser maior que zero."})
        if self.data_emissao and self.data_vencimento and self.data_vencimento < self.data_emissao:
            raise ValidationError({"data_vencimento": "Vencimento nao pode ser anterior a emissao."})
        if self.desconto and self.valor_original and self.desconto > self.valor_original:
            raise ValidationError({"desconto": "Desconto nao pode ser maior que o valor original."})


class ContaPagar(LancamentoFinanceiroBase):
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, related_name="contas_pagar")
    numero_documento = models.CharField(max_length=80, blank=True)
    nota_fiscal = models.CharField(max_length=80, blank=True)
    valor_pago = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    forma_pagamento = models.CharField(max_length=80, blank=True)
    status = models.CharField(
        max_length=30,
        choices=StatusContaPagar.choices,
        default=StatusContaPagar.ABERTO,
    )
    data_baixa = models.DateTimeField(null=True, blank=True)
    baixado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contas_pagar_baixadas",
    )
    comprovante = models.FileField(upload_to="comprovantes/pagar/", null=True, blank=True)

    class Meta:
        ordering = ["data_vencimento", "fornecedor__nome"]
        indexes = [
            models.Index(fields=["empresa", "status", "data_vencimento"]),
            models.Index(fields=["empresa", "fornecedor", "numero_documento"]),
        ]

    def __str__(self):
        return f"{self.fornecedor} - {self.descricao}"

    @property
    def saldo_pendente(self):
        return max(self.valor_total - self.valor_pago, Decimal("0.00"))

    def atualizar_status_por_saldo(self):
        if self.valor_pago <= 0:
            return
        if self.valor_pago >= self.valor_total:
            self.status = StatusContaPagar.PAGO
        else:
            self.status = StatusContaPagar.PAGO_PARCIAL
        self.data_baixa = self.data_baixa or timezone.now()

    def clean(self):
        super().clean()
        if self.valor_pago is not None and self.valor_pago < 0:
            raise ValidationError({"valor_pago": "Valor pago nao pode ser negativo."})
        if self.valor_pago and self.valor_total and self.valor_pago > self.valor_total:
            raise ValidationError({"valor_pago": "Valor pago nao pode ser maior que o valor total."})
        if self.status == StatusContaPagar.PAGO and self.valor_pago < self.valor_total:
            raise ValidationError({"status": "Conta so pode ser marcada como paga quando o saldo estiver quitado."})


class ContaReceber(LancamentoFinanceiroBase):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="contas_receber")
    contrato = models.CharField(max_length=80, blank=True)
    parcela = models.PositiveIntegerField(null=True, blank=True)
    valor_recebido = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    honorarios = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    forma_recebimento = models.CharField(max_length=80, blank=True)
    status = models.CharField(
        max_length=30,
        choices=StatusContaReceber.choices,
        default=StatusContaReceber.ABERTO,
    )
    data_recebimento = models.DateTimeField(null=True, blank=True)
    recebido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contas_receber_recebidas",
    )
    conta_original = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="renegociacoes",
    )
    renegociado_em = models.DateTimeField(null=True, blank=True)
    renegociado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contas_receber_renegociadas",
    )

    class Meta:
        ordering = ["data_vencimento", "cliente__nome"]
        indexes = [
            models.Index(fields=["empresa", "status", "data_vencimento"]),
            models.Index(fields=["empresa", "cliente", "contrato"]),
        ]

    def __str__(self):
        return f"{self.cliente} - {self.descricao}"

    @property
    def valor_total(self):
        return super().valor_total + self.honorarios

    @property
    def saldo_pendente(self):
        return max(self.valor_total - self.valor_recebido, Decimal("0.00"))

    @property
    def dias_atraso(self):
        hoje = timezone.localdate()
        if self.data_vencimento >= hoje or self.status in {StatusContaReceber.RECEBIDO, StatusContaReceber.CANCELADO}:
            return 0
        return (hoje - self.data_vencimento).days

    def atualizar_status_por_saldo(self):
        if self.valor_recebido <= 0:
            return
        if self.valor_recebido >= self.valor_total:
            self.status = StatusContaReceber.RECEBIDO
        else:
            self.status = StatusContaReceber.RECEBIDO_PARCIAL
        self.data_recebimento = self.data_recebimento or timezone.now()

    def clean(self):
        super().clean()
        if self.valor_recebido is not None and self.valor_recebido < 0:
            raise ValidationError({"valor_recebido": "Valor recebido nao pode ser negativo."})
        if self.honorarios is not None and self.honorarios < 0:
            raise ValidationError({"honorarios": "Honorarios nao podem ser negativos."})
        if self.valor_recebido and self.valor_total and self.valor_recebido > self.valor_total:
            raise ValidationError({"valor_recebido": "Valor recebido nao pode ser maior que o valor total."})
        if self.status == StatusContaReceber.RECEBIDO and self.valor_recebido < self.valor_total:
            raise ValidationError({"status": "Conta so pode ser marcada como recebida quando o saldo estiver quitado."})


class MovimentacaoFinanceira(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="movimentacoes_financeiras")
    tipo = models.CharField(max_length=20, choices=TipoMovimentacao.choices)
    descricao = models.CharField(max_length=180)
    data_movimento = models.DateField()
    data_competencia = models.DateField(null=True, blank=True)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, related_name="movimentacoes")
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True)
    plano_conta = models.ForeignKey(PlanoConta, on_delete=models.PROTECT, null=True, blank=True)
    origem_modelo = models.CharField(max_length=120, blank=True)
    origem_id = models.CharField(max_length=80, blank=True)
    conciliado = models.BooleanField(default=False)

    class Meta:
        ordering = ["-data_movimento", "-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "tipo", "data_movimento"]),
            models.Index(fields=["origem_modelo", "origem_id"]),
        ]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao}"


class ConciliacaoBancaria(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="conciliacoes_bancarias")
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, related_name="conciliacoes")
    data_movimento = models.DateField()
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    historico = models.TextField()
    documento = models.CharField(max_length=80, blank=True)
    status = models.CharField(
        max_length=30,
        choices=StatusConciliacao.choices,
        default=StatusConciliacao.PENDENTE,
    )
    movimentacao = models.ForeignKey(
        MovimentacaoFinanceira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="conciliacoes",
    )
    metadados = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-data_movimento", "-criado_em"]
        indexes = [models.Index(fields=["empresa", "status", "data_movimento"])]

    def __str__(self):
        return f"{self.data_movimento} - {self.valor}"


class Orcamento(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="orcamentos")
    ano = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField(null=True, blank=True)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True)
    plano_conta = models.ForeignKey(PlanoConta, on_delete=models.PROTECT, null=True, blank=True)
    valor_previsto = models.DecimalField(max_digits=14, decimal_places=2)
    valor_realizado = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        ordering = ["ano", "mes"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "ano", "mes", "centro_custo", "plano_conta"],
                name="uniq_orcamento_dimensoes",
            )
        ]

    def __str__(self):
        periodo = f"{self.mes:02d}/{self.ano}" if self.mes else str(self.ano)
        return f"{periodo} - {self.valor_previsto}"


class AprovacaoPagamento(TimeStampedModel):
    conta_pagar = models.ForeignKey(ContaPagar, on_delete=models.CASCADE, related_name="aprovacoes")
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aprovacoes_solicitadas",
    )
    aprovador = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="aprovacoes_realizadas",
    )
    status = models.CharField(max_length=20, choices=StatusAprovacao.choices, default=StatusAprovacao.PENDENTE)
    justificativa = models.TextField(blank=True)
    decidido_em = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.conta_pagar} - {self.status}"


class RelatorioGerado(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="relatorios")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    tipo = models.CharField(max_length=80)
    formato = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=StatusRelatorio.choices, default=StatusRelatorio.PRONTO)
    parametros = models.JSONField(default=dict, blank=True)
    arquivo = models.FileField(upload_to="relatorios/", null=True, blank=True)
    erro = models.TextField(blank=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["empresa", "tipo", "formato", "criado_em"])]

    def __str__(self):
        return f"{self.tipo}.{self.formato} - {self.status}"


class AnexoFinanceiro(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="anexos_financeiros")
    arquivo = models.FileField(upload_to="anexos/financeiro/")
    nome_original = models.CharField(max_length=180)
    content_type = models.CharField(max_length=120, blank=True)
    tamanho = models.PositiveIntegerField(default=0)
    origem_modelo = models.CharField(max_length=120)
    origem_id = models.CharField(max_length=80)
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["empresa", "origem_modelo", "origem_id"])]

    def __str__(self):
        return self.nome_original
