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


# ---------------------------------------------------------------------------
# Fase 2 — Financeiro Avancado
# ---------------------------------------------------------------------------

class PeriodicidadeChoices(models.TextChoices):
    DIARIA = "diaria", "Diaria"
    SEMANAL = "semanal", "Semanal"
    MENSAL = "mensal", "Mensal"
    TRIMESTRAL = "trimestral", "Trimestral"
    SEMESTRAL = "semestral", "Semestral"
    ANUAL = "anual", "Anual"


class StatusRecorrencia(models.TextChoices):
    ATIVA = "ativa", "Ativa"
    PAUSADA = "pausada", "Pausada"
    CANCELADA = "cancelada", "Cancelada"
    ENCERRADA = "encerrada", "Encerrada"


class RecorrenciaFinanceira(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="recorrencias_financeiras")
    tipo = models.CharField(max_length=20, choices=[("pagar", "Pagar"), ("receber", "Receber")])
    descricao = models.CharField(max_length=180)
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    periodicidade = models.CharField(max_length=20, choices=PeriodicidadeChoices.choices)
    data_inicio = models.DateField()
    data_fim = models.DateField(null=True, blank=True)
    dia_vencimento = models.PositiveSmallIntegerField(
        help_text="Dia do mes para cobrancas mensais e superiores (1-31)."
    )
    plano_conta = models.ForeignKey(PlanoConta, on_delete=models.PROTECT, null=True, blank=True, related_name="recorrencias")
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True, related_name="recorrencias")
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, null=True, blank=True, related_name="recorrencias")
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, null=True, blank=True, related_name="recorrencias")
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, null=True, blank=True, related_name="recorrencias")
    status = models.CharField(max_length=20, choices=StatusRecorrencia.choices, default=StatusRecorrencia.ATIVA)
    total_gerado = models.PositiveIntegerField(default=0)
    ultima_geracao = models.DateField(null=True, blank=True)
    responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recorrencias_financeiras",
    )
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["empresa", "status", "tipo"])]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao}"

    def proxima_data_vencimento(self):
        from datetime import date
        import calendar

        referencia = self.ultima_geracao or self.data_inicio
        if self.periodicidade == PeriodicidadeChoices.DIARIA:
            from datetime import timedelta
            return referencia + timedelta(days=1)
        if self.periodicidade == PeriodicidadeChoices.SEMANAL:
            from datetime import timedelta
            return referencia + timedelta(weeks=1)
        if self.periodicidade == PeriodicidadeChoices.MENSAL:
            mes = referencia.month + 1
            ano = referencia.year + (mes - 1) // 12
            mes = ((mes - 1) % 12) + 1
            dia = min(self.dia_vencimento, calendar.monthrange(ano, mes)[1])
            return date(ano, mes, dia)
        if self.periodicidade == PeriodicidadeChoices.TRIMESTRAL:
            mes = referencia.month + 3
            ano = referencia.year + (mes - 1) // 12
            mes = ((mes - 1) % 12) + 1
            dia = min(self.dia_vencimento, calendar.monthrange(ano, mes)[1])
            return date(ano, mes, dia)
        if self.periodicidade == PeriodicidadeChoices.SEMESTRAL:
            mes = referencia.month + 6
            ano = referencia.year + (mes - 1) // 12
            mes = ((mes - 1) % 12) + 1
            dia = min(self.dia_vencimento, calendar.monthrange(ano, mes)[1])
            return date(ano, mes, dia)
        if self.periodicidade == PeriodicidadeChoices.ANUAL:
            ano = referencia.year + 1
            dia = min(self.dia_vencimento, calendar.monthrange(ano, referencia.month)[1])
            return date(ano, referencia.month, dia)
        return referencia


class PeriodoFechamento(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="periodos_fechamento")
    ano = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    status = models.CharField(
        max_length=20,
        choices=[("aberto", "Aberto"), ("fechado", "Fechado"), ("reaberto", "Reaberto")],
        default="aberto",
    )
    fechado_em = models.DateTimeField(null=True, blank=True)
    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="periodos_fechados",
    )
    reaberto_em = models.DateTimeField(null=True, blank=True)
    reaberto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="periodos_reabertos",
    )
    justificativa = models.TextField(blank=True)

    class Meta:
        ordering = ["-ano", "-mes"]
        constraints = [
            models.UniqueConstraint(fields=["empresa", "ano", "mes"], name="uniq_periodo_fechamento_empresa_ano_mes")
        ]

    def __str__(self):
        return f"{self.mes:02d}/{self.ano} - {self.status}"

    def esta_fechado(self):
        return self.status == "fechado"


class RateioLancamento(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="rateios_lancamento")
    origem_modelo = models.CharField(max_length=120, help_text="Ex: financeiro.ContaPagar")
    origem_id = models.CharField(max_length=80)
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True, related_name="rateios")
    plano_conta = models.ForeignKey(PlanoConta, on_delete=models.PROTECT, null=True, blank=True, related_name="rateios")
    percentual = models.DecimalField(max_digits=5, decimal_places=2, help_text="Percentual do rateio (0.00-100.00)")
    valor = models.DecimalField(max_digits=14, decimal_places=2, help_text="Valor calculado")
    observacao = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["origem_modelo", "origem_id"]
        indexes = [models.Index(fields=["empresa", "origem_modelo", "origem_id"])]

    def __str__(self):
        return f"{self.origem_modelo}#{self.origem_id} - {self.percentual}%"

    @classmethod
    def total_percentual_da_origem(cls, empresa, origem_modelo, origem_id):
        from django.db.models import Sum
        resultado = cls.objects.filter(
            empresa=empresa, origem_modelo=origem_modelo, origem_id=origem_id
        ).aggregate(total=Sum("percentual"))
        return resultado["total"] or Decimal("0.00")


class AlcadaAprovacao(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="alcadas_aprovacao")
    nome = models.CharField(max_length=120)
    valor_minimo = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    valor_maximo = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True, help_text="null = sem limite")
    centro_custo = models.ForeignKey(CentroCusto, on_delete=models.PROTECT, null=True, blank=True, related_name="alcadas")
    plano_conta = models.ForeignKey(PlanoConta, on_delete=models.PROTECT, null=True, blank=True, related_name="alcadas")
    fornecedor = models.ForeignKey(Fornecedor, on_delete=models.PROTECT, null=True, blank=True, related_name="alcadas")
    tipo_aprovacao = models.CharField(
        max_length=20,
        choices=[("sequencial", "Sequencial"), ("paralela", "Paralela")],
        default="sequencial",
    )
    prazo_aprovacao_horas = models.PositiveIntegerField(default=48)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class AlcadaAprovador(TimeStampedModel):
    alcada = models.ForeignKey(AlcadaAprovacao, on_delete=models.CASCADE, related_name="aprovadores")
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="alcadas_aprovador")
    ordem = models.PositiveSmallIntegerField(default=1, help_text="Ordem para aprovacao sequencial")

    class Meta:
        ordering = ["alcada", "ordem"]
        constraints = [
            models.UniqueConstraint(fields=["alcada", "usuario"], name="uniq_alcada_aprovador_alcada_usuario")
        ]

    def __str__(self):
        return f"{self.alcada} - {self.usuario} (ordem {self.ordem})"


# ---------------------------------------------------------------------------
# Fase 3 — Integracao Bancaria
# ---------------------------------------------------------------------------

class CredencialBancaria(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="credenciais_bancarias")
    banco = models.CharField(max_length=80)
    descricao = models.CharField(max_length=120)
    tipo_integracao = models.CharField(
        max_length=20,
        choices=[("api", "API"), ("ofx", "OFX"), ("remessa", "Remessa")],
    )
    client_id = models.CharField(max_length=200, blank=True)
    client_secret = models.CharField(max_length=200, blank=True)
    certificado = models.FileField(upload_to="fiscal/certificados/", null=True, blank=True, help_text="Certificado digital")
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, related_name="credenciais")
    ativa = models.BooleanField(default=True)
    configuracoes = models.JSONField(default=dict, blank=True)
    metadados = models.JSONField(default=dict, blank=True, help_text="Logs, ultimo sync, etc.")

    class Meta:
        ordering = ["banco", "descricao"]

    def __str__(self):
        return f"{self.banco} - {self.descricao}"


class ImportacaoOFX(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="importacoes_ofx")
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, related_name="importacoes_ofx")
    arquivo = models.FileField(upload_to="ofx/")
    nome_arquivo = models.CharField(max_length=180)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pendente", "Pendente"),
            ("processando", "Processando"),
            ("processado", "Processado"),
            ("erro", "Erro"),
        ],
        default="pendente",
    )
    total_lancamentos = models.PositiveIntegerField(default=0)
    lancamentos_importados = models.PositiveIntegerField(default=0)
    lancamentos_duplicados = models.PositiveIntegerField(default=0)
    data_inicio_extrato = models.DateField(null=True, blank=True)
    data_fim_extrato = models.DateField(null=True, blank=True)
    erro = models.TextField(blank=True)
    importado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="importacoes_ofx",
    )

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.nome_arquivo} - {self.status}"


class RegraConciliacao(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="regras_conciliacao")
    nome = models.CharField(max_length=120)
    campo_comparacao = models.CharField(
        max_length=20,
        choices=[("valor", "Valor"), ("data", "Data"), ("documento", "Documento"), ("historico", "Historico")],
    )
    operador = models.CharField(
        max_length=20,
        choices=[("igual", "Igual"), ("contem", "Contem"), ("comeca_com", "Comeca com"), ("regex", "Regex")],
    )
    valor_referencia = models.CharField(max_length=200)
    peso = models.PositiveSmallIntegerField(default=1, help_text="Peso no score de similaridade")
    ativa = models.BooleanField(default=True)
    auto_conciliar_acima = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text="Percentual minimo de score para auto-conciliar"
    )

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class CobrancaFinanceira(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="cobrancas_financeiras")
    conta_receber = models.ForeignKey(ContaReceber, on_delete=models.CASCADE, related_name="cobrancas")
    tipo = models.CharField(max_length=20, choices=[("boleto", "Boleto"), ("pix", "PIX")])
    status = models.CharField(
        max_length=20,
        choices=[
            ("criado", "Criado"),
            ("registrado", "Registrado"),
            ("aguardando", "Aguardando"),
            ("pago", "Pago"),
            ("vencido", "Vencido"),
            ("cancelado", "Cancelado"),
        ],
        default="criado",
    )
    nosso_numero = models.CharField(max_length=40, blank=True)
    linha_digitavel = models.TextField(blank=True)
    codigo_pix = models.TextField(blank=True, help_text="EMV PIX")
    qrcode_base64 = models.TextField(blank=True)
    data_vencimento = models.DateField()
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    data_pagamento = models.DateField(null=True, blank=True)
    valor_pago = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    url_boleto = models.CharField(max_length=500, blank=True)
    metadados = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.conta_receber} - {self.status}"


class RegraCobrancanAutomatica(models.TextChoices):
    ANTES_VENCIMENTO = "antes_vencimento", "Antes do vencimento"
    NO_VENCIMENTO = "no_vencimento", "No vencimento"
    APOS_VENCIMENTO = "apos_vencimento", "Apos o vencimento"
    COBRANCA_FINAL = "cobranca_final", "Cobranca final"


class RegraCobrancan(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="regras_cobranca")
    nome = models.CharField(max_length=120)
    gatilho = models.CharField(max_length=30, choices=RegraCobrancanAutomatica.choices)
    dias_offset = models.IntegerField(default=0, help_text="Ex: -3 (3 dias antes), 0, +7 (7 dias depois)")
    canal = models.CharField(
        max_length=20,
        choices=[("sistema", "Sistema"), ("email", "E-mail"), ("whatsapp", "WhatsApp"), ("sms", "SMS")],
    )
    modelo_mensagem = models.TextField()
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class HistoricoCobranca(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="historicos_cobranca")
    conta_receber = models.ForeignKey(ContaReceber, on_delete=models.CASCADE, related_name="historico_cobranca")
    canal = models.CharField(max_length=20)
    mensagem_enviada = models.TextField()
    status_envio = models.CharField(max_length=20, choices=[("enviado", "Enviado"), ("falhou", "Falhou")])
    enviado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-enviado_em"]

    def __str__(self):
        return f"{self.conta_receber} - {self.canal} - {self.status_envio}"


# ---------------------------------------------------------------------------
# Fase 4 — Tesouraria
# ---------------------------------------------------------------------------

class TransferenciaInterna(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="transferencias_internas")
    conta_origem = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, related_name="transferencias_saida")
    conta_destino = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, related_name="transferencias_entrada")
    data_transferencia = models.DateField()
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    tarifa = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    descricao = models.CharField(max_length=200)
    movimentacao_saida = models.ForeignKey(
        MovimentacaoFinanceira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transferencia_saida",
    )
    movimentacao_entrada = models.ForeignKey(
        MovimentacaoFinanceira,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transferencia_entrada",
    )
    realizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transferencias_realizadas",
    )
    comprovante = models.FileField(upload_to="transferencias/", null=True, blank=True)

    class Meta:
        ordering = ["-data_transferencia", "-criado_em"]

    def __str__(self):
        return f"{self.conta_origem} -> {self.conta_destino} R$ {self.valor}"


class ContratoFinanceiro(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="contratos_financeiros")
    tipo = models.CharField(
        max_length=20,
        choices=[("emprestimo", "Emprestimo"), ("financiamento", "Financiamento"), ("leasing", "Leasing")],
    )
    descricao = models.CharField(max_length=200)
    credor = models.CharField(max_length=120, help_text="Banco ou credor")
    valor_principal = models.DecimalField(max_digits=14, decimal_places=2)
    taxa_juros_mensal = models.DecimalField(max_digits=6, decimal_places=4, help_text="Ex: 1.5000 = 1.5% ao mes")
    total_parcelas = models.PositiveIntegerField()
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(
        max_length=20,
        choices=[
            ("ativo", "Ativo"),
            ("quitado", "Quitado"),
            ("inadimplente", "Inadimplente"),
            ("cancelado", "Cancelado"),
        ],
        default="ativo",
    )
    saldo_devedor = models.DecimalField(max_digits=14, decimal_places=2, help_text="Saldo calculado")
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, null=True, blank=True, related_name="contratos_financeiros")
    plano_conta = models.ForeignKey(PlanoConta, on_delete=models.PROTECT, null=True, blank=True, related_name="contratos_financeiros")
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_inicio"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.descricao}"


class ParcelaContratoFinanceiro(TimeStampedModel):
    contrato = models.ForeignKey(ContratoFinanceiro, on_delete=models.CASCADE, related_name="parcelas")
    numero_parcela = models.PositiveSmallIntegerField()
    data_vencimento = models.DateField()
    valor_principal = models.DecimalField(max_digits=14, decimal_places=2)
    valor_juros = models.DecimalField(max_digits=14, decimal_places=2)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pendente", "Pendente"),
            ("pago", "Pago"),
            ("atrasado", "Atrasado"),
            ("cancelado", "Cancelado"),
        ],
        default="pendente",
    )
    conta_pagar = models.ForeignKey(ContaPagar, on_delete=models.SET_NULL, null=True, blank=True, related_name="parcelas_contrato")
    data_pagamento = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ["contrato", "numero_parcela"]

    def __str__(self):
        return f"{self.contrato} - Parcela {self.numero_parcela}"


class AplicacaoFinanceira(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="aplicacoes_financeiras")
    banco = models.CharField(max_length=80)
    descricao = models.CharField(max_length=120)
    tipo = models.CharField(
        max_length=20,
        choices=[
            ("cdb", "CDB"),
            ("lci", "LCI"),
            ("lca", "LCA"),
            ("fundos", "Fundos"),
            ("poupanca", "Poupanca"),
            ("tesouro", "Tesouro Direto"),
            ("outros", "Outros"),
        ],
    )
    conta_bancaria = models.ForeignKey(ContaBancaria, on_delete=models.PROTECT, null=True, blank=True, related_name="aplicacoes_financeiras")
    data_aplicacao = models.DateField()
    valor_aplicado = models.DecimalField(max_digits=14, decimal_places=2)
    rendimento_percentual = models.DecimalField(max_digits=6, decimal_places=4, default=Decimal("0.0000"), help_text="% ao ano")
    data_vencimento = models.DateField(null=True, blank=True)
    data_resgate = models.DateField(null=True, blank=True)
    valor_resgatado = models.DecimalField(max_digits=14, decimal_places=2, null=True, blank=True)
    valor_imposto = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    saldo_atual = models.DecimalField(max_digits=14, decimal_places=2, help_text="Atualizado periodicamente")
    status = models.CharField(
        max_length=20,
        choices=[
            ("ativa", "Ativa"),
            ("vencida", "Vencida"),
            ("resgatada", "Resgatada"),
            ("cancelada", "Cancelada"),
        ],
        default="ativa",
    )
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_aplicacao"]

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.banco} - {self.descricao}"
