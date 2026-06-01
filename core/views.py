from rest_framework import viewsets

from .audit import diff_snapshots, request_context, snapshot_model
from .models import (
    Empresa,
    EmpresaModulo,
    EventLog,
    Modulo,
    Notificacao,
    Perfil,
    PerfilPermissao,
    Permissao,
    Usuario,
    UsuarioPerfil,
    NivelRisco,
    TipoEvento,
)
from .permissions import StaffWritePermission
from .services import registrar_evento
from .serializers import (
    EmpresaModuloSerializer,
    EmpresaSerializer,
    EventLogSerializer,
    ModuloSerializer,
    NotificacaoSerializer,
    PerfilPermissaoSerializer,
    PerfilSerializer,
    PermissaoSerializer,
    UsuarioPerfilSerializer,
    UsuarioSerializer,
)


class EmpresaScopedQuerysetMixin:
    empresa_field = "empresa"

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario = self.request.user
        if not usuario.is_authenticated:
            return queryset.none()
        if usuario.is_superuser:
            return queryset
        empresa_id = getattr(usuario, "empresa_id", None)
        if empresa_id and self.empresa_field:
            return queryset.filter(**{self.empresa_field: empresa_id})
        return queryset.none()

    def perform_create(self, serializer):
        usuario = self.request.user
        if self.empresa_field == "empresa" and usuario.is_authenticated and not usuario.is_superuser and usuario.empresa_id:
            serializer.save(empresa_id=usuario.empresa_id)
            return
        serializer.save()

    def perform_update(self, serializer):
        usuario = self.request.user
        if self.empresa_field == "empresa" and usuario.is_authenticated and not usuario.is_superuser and usuario.empresa_id:
            serializer.save(empresa_id=usuario.empresa_id)
            return
        serializer.save()


def _empresa_do_registro(registro):
    empresa = getattr(registro, "empresa", None)
    if empresa is not None:
        return empresa
    if isinstance(registro, Empresa):
        return registro
    perfil = getattr(registro, "perfil", None)
    if perfil is not None:
        return perfil.empresa
    usuario = getattr(registro, "usuario", None)
    if usuario is not None:
        return usuario.empresa
    return None


class AuditedCoreMixin:
    modulo_auditoria = "core"
    tela_auditoria = ""

    def perform_create(self, serializer):
        super().perform_create(serializer)
        registro = serializer.instance
        registrar_evento(
            tipo_evento=TipoEvento.CRIACAO,
            usuario=self.request.user,
            empresa=_empresa_do_registro(registro),
            modulo=self.modulo_auditoria,
            tela=self.tela_auditoria,
            acao="criar",
            registro=registro,
            valor_novo=snapshot_model(registro),
            nivel_risco=NivelRisco.ALTO if self.tela_auditoria in {"usuarios", "permissoes", "perfis"} else NivelRisco.MEDIO,
            **request_context(self.request),
        )

    def perform_update(self, serializer):
        anterior = snapshot_model(serializer.instance)
        super().perform_update(serializer)
        registro = serializer.instance
        novo = snapshot_model(registro)
        registrar_evento(
            tipo_evento=TipoEvento.ALTERACAO,
            usuario=self.request.user,
            empresa=_empresa_do_registro(registro),
            modulo=self.modulo_auditoria,
            tela=self.tela_auditoria,
            acao="alterar",
            registro=registro,
            valor_anterior=diff_snapshots(anterior, novo),
            valor_novo=novo,
            nivel_risco=NivelRisco.ALTO if self.tela_auditoria in {"usuarios", "permissoes", "perfis"} else NivelRisco.MEDIO,
            **request_context(self.request),
        )


class EmpresaViewSet(AuditedCoreMixin, viewsets.ModelViewSet):
    queryset = Empresa.objects.all()
    serializer_class = EmpresaSerializer
    permission_classes = [StaffWritePermission]
    tela_auditoria = "empresas"
    search_fields = ["razao_social", "nome_fantasia", "cnpj"]
    ordering_fields = ["razao_social", "criado_em"]

    def get_queryset(self):
        queryset = super().get_queryset()
        usuario = self.request.user
        if not usuario.is_authenticated:
            return queryset.none()
        if usuario.is_superuser:
            return queryset
        if usuario.empresa_id:
            return queryset.filter(pk=usuario.empresa_id)
        return queryset.none()


class ModuloViewSet(AuditedCoreMixin, viewsets.ModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer
    permission_classes = [StaffWritePermission]
    tela_auditoria = "modulos"
    search_fields = ["codigo", "nome"]
    filterset_fields = ["ativo"]
    ordering_fields = ["nome", "codigo"]


class EmpresaModuloViewSet(AuditedCoreMixin, EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = EmpresaModulo.objects.select_related("empresa", "modulo")
    serializer_class = EmpresaModuloSerializer
    permission_classes = [StaffWritePermission]
    tela_auditoria = "empresa_modulos"
    filterset_fields = ["empresa", "modulo", "ativo"]
    search_fields = ["empresa__razao_social", "modulo__nome", "modulo__codigo"]


class UsuarioViewSet(AuditedCoreMixin, EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Usuario.objects.select_related("empresa")
    serializer_class = UsuarioSerializer
    permission_classes = [StaffWritePermission]
    tela_auditoria = "usuarios"
    filterset_fields = ["empresa", "is_active", "is_staff"]
    search_fields = ["username", "email", "first_name", "last_name"]


class PerfilViewSet(AuditedCoreMixin, EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Perfil.objects.select_related("empresa")
    serializer_class = PerfilSerializer
    permission_classes = [StaffWritePermission]
    tela_auditoria = "perfis"
    filterset_fields = ["empresa", "sistema"]
    search_fields = ["nome", "descricao"]


class PermissaoViewSet(AuditedCoreMixin, viewsets.ModelViewSet):
    queryset = Permissao.objects.select_related("modulo")
    serializer_class = PermissaoSerializer
    permission_classes = [StaffWritePermission]
    tela_auditoria = "permissoes"
    filterset_fields = ["modulo", "tela", "acao", "sensivel"]
    search_fields = ["codigo", "tela", "acao", "descricao"]


class PerfilPermissaoViewSet(AuditedCoreMixin, EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = PerfilPermissao.objects.select_related("perfil", "permissao", "perfil__empresa")
    serializer_class = PerfilPermissaoSerializer
    permission_classes = [StaffWritePermission]
    tela_auditoria = "perfil_permissoes"
    empresa_field = "perfil__empresa"
    filterset_fields = ["perfil", "permissao"]


class UsuarioPerfilViewSet(AuditedCoreMixin, EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = UsuarioPerfil.objects.select_related("usuario", "perfil", "usuario__empresa")
    serializer_class = UsuarioPerfilSerializer
    permission_classes = [StaffWritePermission]
    tela_auditoria = "usuario_perfis"
    empresa_field = "usuario__empresa"
    filterset_fields = ["usuario", "perfil"]


class EventLogViewSet(EmpresaScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = EventLog.objects.select_related("empresa", "usuario")
    serializer_class = EventLogSerializer
    filterset_fields = ["empresa", "tipo_evento", "modulo", "acao", "nivel_risco"]
    search_fields = ["registro_modelo", "registro_id", "justificativa", "acao"]
    ordering_fields = ["criado_em", "nivel_risco"]


class NotificacaoViewSet(AuditedCoreMixin, EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Notificacao.objects.select_related("empresa", "usuario")
    serializer_class = NotificacaoSerializer
    tela_auditoria = "notificacoes"
    filterset_fields = ["empresa", "usuario", "canal", "status"]
    search_fields = ["titulo", "mensagem"]
