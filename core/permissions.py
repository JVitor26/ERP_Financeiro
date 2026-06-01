from rest_framework.permissions import SAFE_METHODS, BasePermission

from .models import UsuarioPerfil


class StaffWritePermission(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user and request.user.is_authenticated and request.user.is_staff


class PermissaoPorAcao(BasePermission):
    metodo_para_acao = {
        "GET": "visualizar",
        "HEAD": "visualizar",
        "OPTIONS": "visualizar",
        "POST": "editar",
        "PUT": "editar",
        "PATCH": "editar",
        "DELETE": "excluir",
    }
    action_para_acao = {
        "list": "visualizar",
        "retrieve": "visualizar",
        "create": "editar",
        "update": "editar",
        "partial_update": "editar",
        "destroy": "excluir",
    }

    def has_permission(self, request, view):
        usuario = request.user
        if not usuario or not usuario.is_authenticated:
            return False
        if usuario.is_superuser:
            return True

        codigo = self._codigo_permissao(request, view)
        if not codigo:
            return True

        return UsuarioPerfil.objects.filter(
            usuario=usuario,
            perfil__perfil_permissoes__permissao__codigo=codigo,
        ).exists()

    def _codigo_permissao(self, request, view):
        permissao_base = getattr(view, "permissao_base", "")
        if not permissao_base:
            return ""

        action = getattr(view, "action", None)
        action_map = getattr(view, "permissao_action_map", {})
        if action in action_map:
            return action_map[action]

        acao = self.action_para_acao.get(action) or self.metodo_para_acao.get(request.method)
        if not acao:
            return ""
        return f"{permissao_base}.{acao}"
