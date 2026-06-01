from django.contrib import admin

from .models import (
    CentroResultadoContabil,
    CompetenciaContabil,
    ContaContabil,
    HistoricoPadrao,
    LancamentoContabil,
    PartidaContabil,
)


class PartidaContabilInline(admin.TabularInline):
    model = PartidaContabil
    extra = 0
    fields = ("tipo_partida", "conta", "centro_resultado", "valor", "historico_complementar")


@admin.register(ContaContabil)
class ContaContabilAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "natureza", "tipo_saldo", "aceita_lancamento", "ativo")
    list_filter = ("empresa", "natureza", "ativo")
    search_fields = ("codigo", "nome")
    ordering = ("codigo",)


@admin.register(CentroResultadoContabil)
class CentroResultadoContabilAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "empresa", "ativo")
    list_filter = ("empresa", "ativo")
    search_fields = ("codigo", "nome")


@admin.register(HistoricoPadrao)
class HistoricoPadraoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descricao", "empresa")
    list_filter = ("empresa",)
    search_fields = ("codigo", "descricao")


@admin.register(CompetenciaContabil)
class CompetenciaContabilAdmin(admin.ModelAdmin):
    list_display = ("empresa", "ano", "mes", "status", "fechado_em")
    list_filter = ("empresa", "status", "ano")
    ordering = ("-ano", "-mes")


@admin.register(LancamentoContabil)
class LancamentoContabilAdmin(admin.ModelAdmin):
    list_display = ("numero", "empresa", "data_lancamento", "tipo", "estornado", "excluido_logicamente")
    list_filter = ("empresa", "tipo", "estornado")
    search_fields = ("historico", "numero")
    inlines = [PartidaContabilInline]


@admin.register(PartidaContabil)
class PartidaContabilAdmin(admin.ModelAdmin):
    list_display = ("lancamento", "conta", "tipo_partida", "valor")
    list_filter = ("tipo_partida",)
