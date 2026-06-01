from django.db import models

from core.models import Empresa, NivelRisco, TimeStampedModel


class StatusAnaliseIA(models.TextChoices):
    ABERTO = "aberto", "Aberto"
    EM_ANALISE = "em_analise", "Em analise"
    CONFIRMADO = "confirmado", "Confirmado"
    DESCARTADO = "descartado", "Descartado"
    RESOLVIDO = "resolvido", "Resolvido"


class TipoAnomalia(models.TextChoices):
    PAGAMENTO_DUPLICADO = "pagamento_duplicado", "Pagamento duplicado"
    VALOR_FORA_PADRAO = "valor_fora_padrao", "Valor fora do padrao"
    COMPORTAMENTO_USUARIO = "comportamento_usuario", "Comportamento de usuario"
    INADIMPLENCIA = "inadimplencia", "Inadimplencia"
    ORCAMENTO_ESTOURADO = "orcamento_estourado", "Orcamento estourado"


class AlertaIA(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="alertas_ia")
    titulo = models.CharField(max_length=180)
    mensagem = models.TextField()
    nivel_risco = models.CharField(max_length=20, choices=NivelRisco.choices, default=NivelRisco.MEDIO)
    status = models.CharField(max_length=20, choices=StatusAnaliseIA.choices, default=StatusAnaliseIA.ABERTO)
    origem_modelo = models.CharField(max_length=120, blank=True)
    origem_id = models.CharField(max_length=80, blank=True)
    score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    metadados = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["empresa", "status", "nivel_risco"])]

    def __str__(self):
        return self.titulo


class Anomalia(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="anomalias")
    tipo = models.CharField(max_length=40, choices=TipoAnomalia.choices)
    descricao = models.TextField()
    nivel_risco = models.CharField(max_length=20, choices=NivelRisco.choices, default=NivelRisco.MEDIO)
    status = models.CharField(max_length=20, choices=StatusAnaliseIA.choices, default=StatusAnaliseIA.ABERTO)
    entidade_modelo = models.CharField(max_length=120, blank=True)
    entidade_id = models.CharField(max_length=80, blank=True)
    evidencia = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [models.Index(fields=["empresa", "tipo", "status"])]

    def __str__(self):
        return f"{self.tipo} - {self.nivel_risco}"


class PrevisaoIA(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="previsoes_ia")
    nome = models.CharField(max_length=160)
    data_referencia = models.DateField()
    horizonte_dias = models.PositiveIntegerField()
    metrica = models.CharField(max_length=80)
    valor_previsto = models.DecimalField(max_digits=14, decimal_places=2)
    confianca = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    modelo = models.CharField(max_length=80, default="baseline")
    parametros = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-data_referencia", "metrica"]
        indexes = [models.Index(fields=["empresa", "metrica", "data_referencia"])]

    def __str__(self):
        return f"{self.nome} - {self.valor_previsto}"
