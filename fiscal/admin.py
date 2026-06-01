from django.contrib import admin

from .models import (
    ConfiguracaoFiscalEmpresa,
    ConfiguracaoImpostoPorServico,
    EventoFiscal,
    ImpostoApurado,
    ItemNotaFiscal,
    NotaFiscal,
    ObrigacaoFiscal,
)


class ItemNotaFiscalInline(admin.TabularInline):
    model = ItemNotaFiscal
    extra = 0
    fields = ("descricao", "quantidade", "valor_unitario", "valor_total", "aliquota_iss", "valor_iss")


class EventoFiscalInline(admin.TabularInline):
    model = EventoFiscal
    extra = 0
    readonly_fields = ("tipo_evento", "descricao", "codigo_retorno", "criado_em")
    fields = ("tipo_evento", "descricao", "codigo_retorno", "criado_em")
    can_delete = False


@admin.register(ConfiguracaoFiscalEmpresa)
class ConfiguracaoFiscalEmpresaAdmin(admin.ModelAdmin):
    list_display = ("empresa", "regime_tributario", "aliquota_iss", "aliquota_pis", "aliquota_cofins")
    list_filter = ("regime_tributario",)


@admin.register(NotaFiscal)
class NotaFiscalAdmin(admin.ModelAdmin):
    list_display = ("numero", "serie", "tipo", "empresa", "data_emissao", "valor_total", "status")
    list_filter = ("empresa", "tipo", "status")
    search_fields = ("numero", "chave_acesso")
    date_hierarchy = "data_emissao"
    inlines = [ItemNotaFiscalInline, EventoFiscalInline]


@admin.register(ImpostoApurado)
class ImpostoApuradoAdmin(admin.ModelAdmin):
    list_display = ("empresa", "ano", "mes", "tipo_imposto", "valor_apurado", "valor_a_pagar")
    list_filter = ("empresa", "tipo_imposto", "ano")


@admin.register(ObrigacaoFiscal)
class ObrigacaoFiscalAdmin(admin.ModelAdmin):
    list_display = ("empresa", "descricao", "tipo", "data_vencimento", "status")
    list_filter = ("empresa", "status", "tipo")


@admin.register(ConfiguracaoImpostoPorServico)
class ConfiguracaoImpostoPorServicoAdmin(admin.ModelAdmin):
    list_display = ("empresa", "servico", "tipo_imposto", "aliquota", "retencao")
    list_filter = ("empresa", "tipo_imposto", "retencao")
