from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("configuracao-fiscal", views.ConfiguracaoFiscalEmpresaViewSet, basename="configuracao-fiscal")
router.register("notas-fiscais", views.NotaFiscalViewSet)
router.register("eventos-fiscais", views.EventoFiscalViewSet, basename="evento-fiscal")
router.register("impostos-apurados", views.ImpostoApuradoViewSet)
router.register("obrigacoes-fiscais", views.ObrigacaoFiscalViewSet)
router.register("config-imposto-servico", views.ConfiguracaoImpostoPorServicoViewSet)
router.register("relatorios", views.RelatorioFiscalViewSet, basename="relatorio-fiscal")

urlpatterns = router.urls
