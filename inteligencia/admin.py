from django.contrib import admin

from .models import AlertaIA, Anomalia, PrevisaoIA


@admin.register(AlertaIA)
class AlertaIAAdmin(admin.ModelAdmin):
    list_display = ("titulo", "empresa", "nivel_risco", "status", "score", "criado_em")
    list_filter = ("nivel_risco", "status", "empresa")
    search_fields = ("titulo", "mensagem")


@admin.register(Anomalia)
class AnomaliaAdmin(admin.ModelAdmin):
    list_display = ("tipo", "empresa", "nivel_risco", "status", "criado_em")
    list_filter = ("tipo", "nivel_risco", "status", "empresa")
    search_fields = ("descricao", "entidade_modelo", "entidade_id")


@admin.register(PrevisaoIA)
class PrevisaoIAAdmin(admin.ModelAdmin):
    list_display = ("nome", "empresa", "metrica", "data_referencia", "horizonte_dias", "valor_previsto", "confianca")
    list_filter = ("metrica", "modelo", "empresa")
    search_fields = ("nome", "metrica", "modelo")
