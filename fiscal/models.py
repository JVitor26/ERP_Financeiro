from django.conf import settings
from django.db import models

from core.models import Empresa, TimeStampedModel


class RegimeTributario(models.TextChoices):
    SIMPLES_NACIONAL = "simples_nacional", "Simples Nacional"
    LUCRO_PRESUMIDO = "lucro_presumido", "Lucro Presumido"
    LUCRO_REAL = "lucro_real", "Lucro Real"
    MEI = "mei", "MEI"


class TipoImposto(models.TextChoices):
    ISS = "iss", "ISS"
    PIS = "pis", "PIS"
    COFINS = "cofins", "COFINS"
    IRPJ = "irpj", "IRPJ"
    CSLL = "csll", "CSLL"
    INSS_RETIDO = "inss_retido", "INSS Retido"
    ICMS = "icms", "ICMS"
    IPI = "ipi", "IPI"


class StatusNotaFiscal(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    EMITIDA = "emitida", "Emitida"
    AUTORIZADA = "autorizada", "Autorizada"
    CANCELADA = "cancelada", "Cancelada"
    REJEITADA = "rejeitada", "Rejeitada"
    INUTILIZADA = "inutilizada", "Inutilizada"


class TipoNotaFiscal(models.TextChoices):
    NFE = "nfe", "NF-e"
    NFSE = "nfse", "NFS-e"
    NFCE = "nfce", "NFC-e"
    CTE = "cte", "CT-e"


class ConfiguracaoFiscalEmpresa(TimeStampedModel):
    empresa = models.OneToOneField(
        Empresa,
        on_delete=models.CASCADE,
        related_name="configuracao_fiscal",
    )
    regime_tributario = models.CharField(
        max_length=30,
        choices=RegimeTributario.choices,
        default=RegimeTributario.SIMPLES_NACIONAL,
    )
    inscricao_estadual = models.CharField(max_length=30, blank=True)
    inscricao_municipal = models.CharField(max_length=30, blank=True)
    cnae_principal = models.CharField(max_length=10, blank=True)
    aliquota_iss = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    aliquota_pis = models.DecimalField(max_digits=5, decimal_places=2, default=0.65)
    aliquota_cofins = models.DecimalField(max_digits=5, decimal_places=2, default=3.00)
    aliquota_irpj = models.DecimalField(max_digits=5, decimal_places=2, default=15.00)
    aliquota_csll = models.DecimalField(max_digits=5, decimal_places=2, default=9.00)
    retencao_inss = models.BooleanField(default=False)
    aliquota_inss = models.DecimalField(max_digits=5, decimal_places=2, default=11.00)
    configuracoes_extras = models.JSONField(default=dict)

    class Meta:
        verbose_name = "Configuracao Fiscal da Empresa"
        verbose_name_plural = "Configuracoes Fiscais das Empresas"

    def __str__(self):
        return f"Config fiscal - {self.empresa}"


class NotaFiscal(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="notas_fiscais",
    )
    tipo = models.CharField(max_length=10, choices=TipoNotaFiscal.choices)
    numero = models.CharField(max_length=20, blank=True)
    serie = models.CharField(max_length=5, blank=True)
    chave_acesso = models.CharField(max_length=44, blank=True)
    protocolo = models.CharField(max_length=60, blank=True)
    data_emissao = models.DateField()
    data_competencia = models.DateField(null=True, blank=True)
    cliente = models.ForeignKey(
        "financeiro.Cliente",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_fiscais",
    )
    fornecedor = models.ForeignKey(
        "financeiro.Fornecedor",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_fiscais",
    )
    valor_produtos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_servicos = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_desconto = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_iss = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_pis = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_cofins = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_irrf = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_csll = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_inss = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=StatusNotaFiscal.choices,
        default=StatusNotaFiscal.PENDENTE,
    )
    xml_nota = models.TextField(blank=True)
    pdf_danfe = models.FileField(upload_to="fiscal/danfe/", null=True, blank=True)
    conta_pagar = models.ForeignKey(
        "financeiro.ContaPagar",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_fiscais",
    )
    conta_receber = models.ForeignKey(
        "financeiro.ContaReceber",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notas_fiscais",
    )
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ["-data_emissao"]
        indexes = [
            models.Index(fields=["empresa", "status", "data_emissao"]),
        ]
        verbose_name = "Nota Fiscal"
        verbose_name_plural = "Notas Fiscais"

    def __str__(self):
        return f"{self.get_tipo_display()} {self.numero or 'S/N'} - {self.empresa}"


class ItemNotaFiscal(TimeStampedModel):
    nota_fiscal = models.ForeignKey(
        NotaFiscal,
        on_delete=models.CASCADE,
        related_name="itens",
    )
    descricao = models.CharField(max_length=200)
    quantidade = models.DecimalField(max_digits=10, decimal_places=3)
    valor_unitario = models.DecimalField(max_digits=14, decimal_places=2)
    valor_total = models.DecimalField(max_digits=14, decimal_places=2)
    servico = models.ForeignKey(
        "financeiro.Servico",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="itens_nota_fiscal",
    )
    codigo_servico_municipal = models.CharField(max_length=20, blank=True)
    aliquota_iss = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    valor_iss = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Item de Nota Fiscal"
        verbose_name_plural = "Itens de Nota Fiscal"

    def __str__(self):
        return f"{self.descricao} - {self.nota_fiscal}"


class EventoFiscal(TimeStampedModel):
    TIPO_EVENTO_CHOICES = [
        ("emissao", "Emissao"),
        ("autorizacao", "Autorizacao"),
        ("cancelamento", "Cancelamento"),
        ("inutilizacao", "Inutilizacao"),
        ("consulta", "Consulta"),
        ("rejeicao", "Rejeicao"),
    ]

    nota_fiscal = models.ForeignKey(
        NotaFiscal,
        on_delete=models.CASCADE,
        related_name="eventos",
    )
    tipo_evento = models.CharField(max_length=20, choices=TIPO_EVENTO_CHOICES)
    descricao = models.CharField(max_length=200)
    codigo_retorno = models.CharField(max_length=10, blank=True)
    mensagem_retorno = models.TextField(blank=True)
    xml_evento = models.TextField(blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_fiscais",
    )

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Evento Fiscal"
        verbose_name_plural = "Eventos Fiscais"

    def __str__(self):
        return f"{self.get_tipo_evento_display()} - NF {self.nota_fiscal_id}"


class ImpostoApurado(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="impostos_apurados",
    )
    ano = models.PositiveSmallIntegerField()
    mes = models.PositiveSmallIntegerField()
    tipo_imposto = models.CharField(max_length=20, choices=TipoImposto.choices)
    base_calculo = models.DecimalField(max_digits=14, decimal_places=2)
    aliquota = models.DecimalField(max_digits=5, decimal_places=2)
    valor_apurado = models.DecimalField(max_digits=14, decimal_places=2)
    valor_retido = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    valor_a_pagar = models.DecimalField(max_digits=14, decimal_places=2)
    data_vencimento = models.DateField(null=True, blank=True)
    conta_pagar = models.ForeignKey(
        "financeiro.ContaPagar",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="impostos_apurados",
    )

    class Meta:
        ordering = ["-ano", "-mes", "tipo_imposto"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "ano", "mes", "tipo_imposto"],
                name="uniq_imposto_apurado_periodo",
            )
        ]
        verbose_name = "Imposto Apurado"
        verbose_name_plural = "Impostos Apurados"

    def __str__(self):
        return f"{self.get_tipo_imposto_display()} {self.mes:02d}/{self.ano} - {self.empresa}"


class ObrigacaoFiscal(TimeStampedModel):
    TIPO_CHOICES = [
        ("declaracao", "Declaracao"),
        ("pagamento", "Pagamento"),
        ("entrega", "Entrega"),
    ]
    STATUS_CHOICES = [
        ("pendente", "Pendente"),
        ("cumprida", "Cumprida"),
        ("atrasada", "Atrasada"),
        ("dispensada", "Dispensada"),
    ]

    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="obrigacoes_fiscais",
    )
    descricao = models.CharField(max_length=160)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    competencia_ano = models.PositiveSmallIntegerField()
    competencia_mes = models.PositiveSmallIntegerField()
    data_vencimento = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pendente")
    observacao = models.TextField(blank=True)

    class Meta:
        ordering = ["data_vencimento"]
        verbose_name = "Obrigacao Fiscal"
        verbose_name_plural = "Obrigacoes Fiscais"

    def __str__(self):
        return f"{self.descricao} - {self.competencia_mes:02d}/{self.competencia_ano}"


class ConfiguracaoImpostoPorServico(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="configuracoes_imposto_servico",
    )
    servico = models.ForeignKey(
        "financeiro.Servico",
        on_delete=models.CASCADE,
        related_name="configuracoes_imposto",
    )
    tipo_imposto = models.CharField(max_length=20, choices=TipoImposto.choices)
    aliquota = models.DecimalField(max_digits=5, decimal_places=2)
    retencao = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "servico", "tipo_imposto"],
                name="uniq_config_imposto_servico",
            )
        ]
        verbose_name = "Configuracao de Imposto por Servico"
        verbose_name_plural = "Configuracoes de Imposto por Servico"

    def __str__(self):
        return f"{self.servico} - {self.get_tipo_imposto_display()} ({self.aliquota}%)"
