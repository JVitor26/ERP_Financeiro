import hashlib
import json
import uuid
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class TimeStampedModel(models.Model):
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class EmpresaStatus(models.TextChoices):
    ATIVA = "ativa", "Ativa"
    INATIVA = "inativa", "Inativa"
    SUSPENSA = "suspensa", "Suspensa"


class Empresa(TimeStampedModel):
    razao_social = models.CharField(max_length=180)
    nome_fantasia = models.CharField(max_length=180, blank=True)
    cnpj = models.CharField(max_length=18, unique=True, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=EmpresaStatus.choices,
        default=EmpresaStatus.ATIVA,
    )
    timezone = models.CharField(max_length=64, default="America/Cuiaba")
    configuracoes = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["razao_social"]

    def __str__(self):
        return self.nome_fantasia or self.razao_social


class Modulo(TimeStampedModel):
    codigo = models.SlugField(max_length=60, unique=True)
    nome = models.CharField(max_length=120)
    descricao = models.TextField(blank=True)
    ativo = models.BooleanField(default=True)
    schema_configuracao = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class EmpresaModulo(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="modulos")
    modulo = models.ForeignKey(Modulo, on_delete=models.PROTECT, related_name="empresas")
    ativo = models.BooleanField(default=True)
    instalado_em = models.DateTimeField(auto_now_add=True)
    configuracoes = models.JSONField(default=dict, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "modulo"],
                name="uniq_empresa_modulo",
            )
        ]

    def __str__(self):
        return f"{self.empresa} - {self.modulo}"


class Usuario(AbstractUser):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.PROTECT,
        related_name="usuarios",
        null=True,
        blank=True,
    )
    telefone = models.CharField(max_length=30, blank=True)
    cargo = models.CharField(max_length=80, blank=True)
    mfa_habilitado = models.BooleanField(default=False)
    precisa_trocar_senha = models.BooleanField(default=False)
    ultimo_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ["username"]

    def __str__(self):
        return self.get_full_name() or self.username


class Perfil(TimeStampedModel):
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.CASCADE,
        related_name="perfis",
        null=True,
        blank=True,
    )
    nome = models.CharField(max_length=80)
    descricao = models.TextField(blank=True)
    sistema = models.BooleanField(default=False)

    class Meta:
        ordering = ["nome"]
        constraints = [
            models.UniqueConstraint(
                fields=["empresa", "nome"],
                name="uniq_perfil_empresa_nome",
            )
        ]

    def __str__(self):
        return self.nome


class Permissao(TimeStampedModel):
    codigo = models.SlugField(max_length=120, unique=True)
    modulo = models.ForeignKey(
        Modulo,
        on_delete=models.PROTECT,
        related_name="permissoes",
        null=True,
        blank=True,
    )
    tela = models.CharField(max_length=80)
    acao = models.CharField(max_length=60)
    descricao = models.TextField(blank=True)
    sensivel = models.BooleanField(default=False)

    class Meta:
        ordering = ["modulo__codigo", "tela", "acao"]

    def __str__(self):
        return self.codigo


class PerfilPermissao(TimeStampedModel):
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="perfil_permissoes")
    permissao = models.ForeignKey(Permissao, on_delete=models.CASCADE, related_name="permissao_perfis")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["perfil", "permissao"],
                name="uniq_perfil_permissao",
            )
        ]


class UsuarioPerfil(TimeStampedModel):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="usuario_perfis")
    perfil = models.ForeignKey(Perfil, on_delete=models.CASCADE, related_name="perfil_usuarios")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["usuario", "perfil"],
                name="uniq_usuario_perfil",
            )
        ]


class TipoEvento(models.TextChoices):
    CRIACAO = "criacao", "Criacao"
    ALTERACAO = "alteracao", "Alteracao"
    EXCLUSAO_LOGICA = "exclusao_logica", "Exclusao logica"
    BAIXA = "baixa", "Baixa"
    APROVACAO = "aprovacao", "Aprovacao"
    REPROVACAO = "reprovacao", "Reprovacao"
    EXPORTACAO = "exportacao", "Exportacao"
    ACESSO_SENSIVEL = "acesso_sensivel", "Acesso sensivel"
    ALERTA_SISTEMA = "alerta_sistema", "Alerta do sistema"
    ALERTA_IA = "alerta_ia", "Alerta de IA"
    INTEGRACAO = "integracao", "Integracao"


class NivelRisco(models.TextChoices):
    BAIXO = "baixo", "Baixo"
    MEDIO = "medio", "Medio"
    ALTO = "alto", "Alto"
    CRITICO = "critico", "Critico"


class EventLog(models.Model):
    event_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    tipo_evento = models.CharField(max_length=40, choices=TipoEvento.choices)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="eventos",
        null=True,
        blank=True,
    )
    empresa = models.ForeignKey(
        Empresa,
        on_delete=models.SET_NULL,
        related_name="eventos",
        null=True,
        blank=True,
    )
    modulo = models.CharField(max_length=80)
    tela = models.CharField(max_length=80, blank=True)
    acao = models.CharField(max_length=80)
    registro_modelo = models.CharField(max_length=120, blank=True)
    registro_id = models.CharField(max_length=80, blank=True)
    valor_anterior = models.JSONField(null=True, blank=True)
    valor_novo = models.JSONField(null=True, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    dispositivo = models.CharField(max_length=255, blank=True)
    origem = models.CharField(max_length=80, default="sistema")
    justificativa = models.TextField(blank=True)
    nivel_risco = models.CharField(
        max_length=20,
        choices=NivelRisco.choices,
        default=NivelRisco.BAIXO,
    )
    hash_anterior = models.CharField(max_length=64, blank=True)
    hash_evento = models.CharField(max_length=64, blank=True, db_index=True)
    metadados = models.JSONField(default=dict, blank=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        indexes = [
            models.Index(fields=["empresa", "criado_em"]),
            models.Index(fields=["tipo_evento", "nivel_risco"]),
            models.Index(fields=["modulo", "acao"]),
            models.Index(fields=["registro_modelo", "registro_id"]),
        ]

    def __str__(self):
        return f"{self.tipo_evento} {self.modulo}.{self.acao} {self.criado_em:%Y-%m-%d %H:%M}"

    def save(self, *args, **kwargs):
        if self.pk and not kwargs.get("force_insert"):
            raise ValueError("EventLog e imutavel e nao pode ser alterado.")
        if not self.hash_anterior:
            ultimo = EventLog.objects.order_by("-id").only("hash_evento").first()
            self.hash_anterior = ultimo.hash_evento if ultimo else ""
        if not self.hash_evento:
            self.hash_evento = self._gerar_hash()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("EventLog e imutavel e nao pode ser excluido.")

    def _gerar_hash(self):
        payload = {
            "event_id": str(self.event_id),
            "tipo_evento": self.tipo_evento,
            "usuario_id": self.usuario_id,
            "empresa_id": self.empresa_id,
            "modulo": self.modulo,
            "tela": self.tela,
            "acao": self.acao,
            "registro_modelo": self.registro_modelo,
            "registro_id": self.registro_id,
            "valor_anterior": self.valor_anterior,
            "valor_novo": self.valor_novo,
            "ip": str(self.ip) if self.ip else "",
            "origem": self.origem,
            "nivel_risco": self.nivel_risco,
            "hash_anterior": self.hash_anterior,
        }
        conteudo = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(conteudo).hexdigest()


class LoginAttempt(models.Model):
    username = models.CharField(max_length=150)
    ip = models.GenericIPAddressField(null=True, blank=True)
    falhas = models.PositiveIntegerField(default=0)
    bloqueado_ate = models.DateTimeField(null=True, blank=True)
    ultimo_evento = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["username", "ip"], name="uniq_login_attempt_username_ip"),
        ]
        indexes = [models.Index(fields=["username", "ip", "bloqueado_ate"])]

    @property
    def bloqueado(self):
        return self.bloqueado_ate is not None and self.bloqueado_ate > timezone.now()

    def registrar_falha(self, limite=5, minutos_bloqueio=15):
        self.falhas += 1
        if self.falhas >= limite:
            self.bloqueado_ate = timezone.now() + timedelta(minutes=minutos_bloqueio)
        self.save(update_fields=["falhas", "bloqueado_ate", "ultimo_evento"])

    def limpar(self):
        self.falhas = 0
        self.bloqueado_ate = None
        self.save(update_fields=["falhas", "bloqueado_ate", "ultimo_evento"])

    def __str__(self):
        return f"{self.username} - {self.ip}"

class NotificacaoStatus(models.TextChoices):
    PENDENTE = "pendente", "Pendente"
    ENVIADA = "enviada", "Enviada"
    FALHOU = "falhou", "Falhou"
    LIDA = "lida", "Lida"


class CanalNotificacao(models.TextChoices):
    SISTEMA = "sistema", "Sistema"
    EMAIL = "email", "E-mail"
    WHATSAPP = "whatsapp", "WhatsApp"
    SMS = "sms", "SMS"
    PUSH = "push", "Push"


class Notificacao(TimeStampedModel):
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name="notificacoes")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notificacoes",
        null=True,
        blank=True,
    )
    canal = models.CharField(max_length=20, choices=CanalNotificacao.choices)
    titulo = models.CharField(max_length=160)
    mensagem = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=NotificacaoStatus.choices,
        default=NotificacaoStatus.PENDENTE,
    )
    enviado_em = models.DateTimeField(null=True, blank=True)
    lido_em = models.DateTimeField(null=True, blank=True)
    metadados = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo
