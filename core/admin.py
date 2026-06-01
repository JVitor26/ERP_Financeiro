from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Empresa,
    EmpresaModulo,
    EventLog,
    LoginAttempt,
    Modulo,
    Notificacao,
    Perfil,
    PerfilPermissao,
    Permissao,
    Usuario,
    UsuarioPerfil,
)


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("ERP", {"fields": ("empresa", "telefone", "cargo", "mfa_habilitado", "precisa_trocar_senha", "ultimo_ip")}),
    )
    list_display = ("username", "email", "empresa", "is_active", "is_staff")
    list_filter = ("is_active", "is_staff", "empresa", "mfa_habilitado")


@admin.register(Empresa)
class EmpresaAdmin(admin.ModelAdmin):
    list_display = ("razao_social", "nome_fantasia", "cnpj", "status")
    search_fields = ("razao_social", "nome_fantasia", "cnpj")
    list_filter = ("status",)


@admin.register(Modulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "ativo")
    search_fields = ("codigo", "nome")
    list_filter = ("ativo",)


@admin.register(EmpresaModulo)
class EmpresaModuloAdmin(admin.ModelAdmin):
    list_display = ("empresa", "modulo", "ativo", "instalado_em")
    list_filter = ("ativo", "modulo")
    search_fields = ("empresa__razao_social", "modulo__nome")


@admin.register(Perfil)
class PerfilAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "sistema")
    search_fields = ("nome", "empresa__razao_social")
    list_filter = ("sistema",)


@admin.register(Permissao)
class PermissaoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "modulo", "tela", "acao", "sensivel")
    search_fields = ("codigo", "tela", "acao")
    list_filter = ("modulo", "sensivel")


admin.site.register(PerfilPermissao)
admin.site.register(UsuarioPerfil)


@admin.register(EventLog)
class EventLogAdmin(admin.ModelAdmin):
    list_display = ("criado_em", "tipo_evento", "empresa", "usuario", "modulo", "acao", "nivel_risco", "hash_evento")
    list_filter = ("tipo_evento", "nivel_risco", "modulo")
    search_fields = ("registro_modelo", "registro_id", "acao", "justificativa")
    readonly_fields = [field.name for field in EventLog._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_active and request.user.is_staff

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ("username", "ip", "falhas", "bloqueado_ate", "ultimo_evento")
    search_fields = ("username", "ip")
    list_filter = ("bloqueado_ate",)


@admin.register(Notificacao)
class NotificacaoAdmin(admin.ModelAdmin):
    list_display = ("titulo", "empresa", "usuario", "canal", "status", "criado_em")
    list_filter = ("canal", "status")
    search_fields = ("titulo", "mensagem", "empresa__razao_social")
