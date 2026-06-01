from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils import timezone

from core.models import Empresa, TimeStampedModel
from financeiro.models import PlanoConta


class NaturezaConta(models.TextChoices):
    ATIVO = "ativo", "Ativo"
    PASSIVO = "passivo", "Passivo"
    PATRIMONIO_LIQUIDO = "patrimonio_liquido", "Patrimônio Líquido"
    RECEITA = "receita", "Receita"
    DESPESA = "despesa", "Despesa"
    CUSTO = "custo", "Custo"
    RESULTADO = "resultado", "Resultado"


class TipoLancamentoContabil(models.TextChoices):
    MANUAL = "manual", "Manual"
    AUTOMATICO = "automatico", "Automático"
    ESTORNO = "estorno", "Estorno"
    AJUSTE = "ajuste", "Ajuste"


class StatusFechamento(models.TextChoices):
    ABERTO = "aberto", "Aberto"
    EM_FECHAMENTO = "em_fechamento", "Em Fechamento"
    FECHADO = "fechado", "Fechado"
    REABERTO = "reaberto", "Reaberto"


# Naturezas que determinam o tipo de saldo
_NATUREZAS_DEVEDORAS = {NaturezaConta.ATIVO, NaturezaConta.DESPESA, NaturezaConta.CUSTO}


class ContaContabil(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="contas_contabeis",
    )
    codigo = models.CharField(max_length=40)
    nome = models.CharField(max_length=120)
    natureza = models.CharField(
        max_length=30,
        choices=NaturezaConta.choices,
    )
    tipo_saldo = models.CharField(
        max_length=10,
        choices=[("devedora", "Devedora"), ("credora", "Credora")],
    )
    pai = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="filhos",
    )
    aceita_lancamento = models.BooleanField(
        default=True,
        help_text="Contas sintéticas não aceitam lançamentos diretos.",
    )
    plano_conta_financeiro = models.ForeignKey(
        PlanoConta,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="contas_contabeis",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_conta_contabil_empresa_codigo",
            )
        ]
        indexes = [
            models.Index(fields=["empresa", "natureza"]),
            models.Index(fields=["empresa", "ativo"]),
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"

    def save(self, *args, **kwargs):
        # Auto-define tipo_saldo based on natureza if not explicitly set
        if self.natureza and not self.tipo_saldo:
            if self.natureza in _NATUREZAS_DEVEDORAS:
                self.tipo_saldo = "devedora"
            else:
                self.tipo_saldo = "credora"
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        if self.natureza:
            if self.natureza in _NATUREZAS_DEVEDORAS:
                expected = "devedora"
            else:
                expected = "credora"
            if self.tipo_saldo and self.tipo_saldo != expected:
                raise ValidationError(
                    {
                        "tipo_saldo": (
                            f"Para natureza '{self.get_natureza_display()}', "
                            f"o tipo de saldo deve ser '{expected}'."
                        )
                    }
                )


class CentroResultadoContabil(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="centros_resultado_contabil",
    )
    codigo = models.CharField(max_length=40)
    nome = models.CharField(max_length=120)
    pai = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="filhos",
    )
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ["codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_centro_resultado_contabil_empresa_codigo",
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class HistoricoPadrao(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="historicos_padrao",
    )
    codigo = models.CharField(max_length=20)
    descricao = models.CharField(max_length=200)

    class Meta:
        ordering = ["codigo"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "codigo"],
                name="uniq_historico_padrao_empresa_codigo",
            )
        ]

    def __str__(self):
        return f"{self.codigo} - {self.descricao}"


class CompetenciaContabil(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="competencias_contabeis",
    )
    ano = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(12)]
    )
    status = models.CharField(
        max_length=20,
        choices=StatusFechamento.choices,
        default=StatusFechamento.ABERTO,
    )
    fechado_em = models.DateTimeField(null=True, blank=True)
    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="competencias_fechadas",
    )
    reaberto_em = models.DateTimeField(null=True, blank=True)
    reaberto_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="competencias_reabertas",
    )
    justificativa_reabertura = models.TextField(blank=True)

    class Meta:
        ordering = ["-ano", "-mes"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "ano", "mes"],
                name="uniq_competencia_contabil_empresa_ano_mes",
            )
        ]

    def __str__(self):
        return f"{self.mes:02d}/{self.ano} - {self.empresa}"

    def esta_fechada(self) -> bool:
        return self.status == StatusFechamento.FECHADO


class LancamentoContabil(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="lancamentos_contabeis",
    )
    numero = models.PositiveIntegerField(
        editable=False,
        help_text="Número sequencial por empresa, gerado automaticamente.",
    )
    data_lancamento = models.DateField()
    data_competencia = models.DateField()
    tipo = models.CharField(
        max_length=20,
        choices=TipoLancamentoContabil.choices,
        default=TipoLancamentoContabil.MANUAL,
    )
    historico = models.TextField()
    historico_padrao = models.ForeignKey(
        HistoricoPadrao,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos",
    )
    origem_modelo = models.CharField(
        max_length=120,
        blank=True,
        help_text="Ex: financeiro.ContaPagar",
    )
    origem_id = models.CharField(max_length=80, blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="lancamentos_contabeis",
    )
    estornado = models.BooleanField(default=False)
    lancamento_original = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="estornos",
    )
    excluido_logicamente = models.BooleanField(default=False)
    justificativa_exclusao = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_lancamento", "-numero"]
        indexes = [
            models.Index(fields=["empresa", "data_lancamento"]),
            models.Index(fields=["empresa", "data_competencia"]),
            models.Index(fields=["origem_modelo", "origem_id"]),
        ]

    def __str__(self):
        return f"Lançamento {self.numero} - {self.empresa} - {self.data_lancamento}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.numero:
            ultimo = (
                LancamentoContabil.objects.filter(empresa=self.empresa)
                .order_by("-numero")
                .values_list("numero", flat=True)
                .first()
            )
            self.numero = (ultimo or 0) + 1
        super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        # Verify competencia is open when it exists (only for non-excluded records)
        if not self.excluido_logicamente and self.data_competencia and self.empresa_id:
            competencia = CompetenciaContabil.objects.filter(
                empresa_id=self.empresa_id,
                ano=self.data_competencia.year,
                mes=self.data_competencia.month,
            ).first()
            if competencia and competencia.esta_fechada():
                raise ValidationError(
                    {
                        "data_competencia": (
                            f"A competência {self.data_competencia.month:02d}/"
                            f"{self.data_competencia.year} está fechada e não "
                            "aceita novos lançamentos."
                        )
                    }
                )

        # Validate partidas balance (only when partidas exist and pk is set)
        if self.pk:
            partidas = self.partidas.all()
            if partidas.exists():
                debitos = partidas.filter(tipo_partida="debito").aggregate(
                    total=Sum("valor")
                )["total"] or Decimal("0.00")
                creditos = partidas.filter(tipo_partida="credito").aggregate(
                    total=Sum("valor")
                )["total"] or Decimal("0.00")
                if debitos != creditos:
                    raise ValidationError(
                        "O lançamento não está balanceado: "
                        f"débitos={debitos}, créditos={creditos}."
                    )


class PartidaContabil(TimeStampedModel):
    lancamento = models.ForeignKey(
        LancamentoContabil,
        on_delete=models.CASCADE,
        related_name="partidas",
    )
    conta = models.ForeignKey(
        ContaContabil,
        on_delete=models.PROTECT,
        related_name="partidas",
    )
    centro_resultado = models.ForeignKey(
        CentroResultadoContabil,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="partidas",
    )
    tipo_partida = models.CharField(
        max_length=10,
        choices=[("debito", "Débito"), ("credito", "Crédito")],
    )
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    historico_complementar = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ["tipo_partida", "conta__codigo"]
        indexes = [
            models.Index(fields=["lancamento", "tipo_partida"]),
            models.Index(fields=["conta"]),
        ]

    def __str__(self):
        return (
            f"{self.get_tipo_partida_display()} {self.conta} "
            f"R$ {self.valor} ({self.lancamento})"
        )

    def clean(self):
        super().clean()
        if self.valor is not None and self.valor <= 0:
            raise ValidationError({"valor": "O valor da partida deve ser maior que zero."})
        if self.conta_id and not self.conta.aceita_lancamento:
            raise ValidationError(
                {"conta": f"A conta '{self.conta}' é sintética e não aceita lançamentos diretos."}
            )
