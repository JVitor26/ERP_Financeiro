from django.contrib import admin

from .models import (
    AprovacaoPagamento,
    AnexoFinanceiro,
    CentroCusto,
    Cliente,
    ConciliacaoBancaria,
    ContaBancaria,
    ContaPagar,
    ContaReceber,
    Fornecedor,
    MovimentacaoFinanceira,
    Orcamento,
    PlanoConta,
    RelatorioGerado,
    Servico,
)


@admin.register(CentroCusto)
class CentroCustoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "empresa", "ativo")
    list_filter = ("ativo", "empresa")
    search_fields = ("codigo", "nome")


@admin.register(PlanoConta)
class PlanoContaAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nome", "tipo", "empresa", "ativo")
    list_filter = ("tipo", "ativo", "empresa")
    search_fields = ("codigo", "nome")


@admin.register(ContaBancaria)
class ContaBancariaAdmin(admin.ModelAdmin):
    list_display = ("banco", "numero", "empresa", "saldo_inicial", "ativa")
    list_filter = ("ativa", "empresa")
    search_fields = ("banco", "numero", "descricao")


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "documento", "ativo")
    list_filter = ("ativo", "empresa")
    search_fields = ("nome", "documento", "email")


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "documento", "ativo")
    list_filter = ("ativo", "empresa")
    search_fields = ("nome", "documento", "email")


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "codigo", "empresa", "valor_padrao", "ativo")
    list_filter = ("ativo", "empresa")
    search_fields = ("codigo", "nome", "descricao")


@admin.register(ContaPagar)
class ContaPagarAdmin(admin.ModelAdmin):
    list_display = ("descricao", "fornecedor", "empresa", "data_vencimento", "valor_original", "valor_pago", "status")
    list_filter = ("status", "empresa", "data_vencimento")
    search_fields = ("descricao", "fornecedor__nome", "numero_documento", "nota_fiscal")
    date_hierarchy = "data_vencimento"


@admin.register(ContaReceber)
class ContaReceberAdmin(admin.ModelAdmin):
    list_display = ("descricao", "cliente", "empresa", "data_vencimento", "valor_original", "valor_recebido", "status")
    list_filter = ("status", "empresa", "data_vencimento")
    search_fields = ("descricao", "cliente__nome", "contrato")
    date_hierarchy = "data_vencimento"


@admin.register(MovimentacaoFinanceira)
class MovimentacaoFinanceiraAdmin(admin.ModelAdmin):
    list_display = ("data_movimento", "tipo", "descricao", "empresa", "valor", "conta_bancaria", "conciliado")
    list_filter = ("tipo", "conciliado", "empresa")
    search_fields = ("descricao", "origem_modelo", "origem_id")
    date_hierarchy = "data_movimento"


@admin.register(ConciliacaoBancaria)
class ConciliacaoBancariaAdmin(admin.ModelAdmin):
    list_display = ("data_movimento", "empresa", "conta_bancaria", "valor", "status")
    list_filter = ("status", "empresa")
    search_fields = ("historico", "documento")
    date_hierarchy = "data_movimento"


admin.site.register(Orcamento)
admin.site.register(AprovacaoPagamento)
admin.site.register(RelatorioGerado)
admin.site.register(AnexoFinanceiro)
