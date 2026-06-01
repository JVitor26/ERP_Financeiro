from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register("contas-contabeis", views.ContaContabilViewSet)
router.register("centros-resultado", views.CentroResultadoContabilViewSet)
router.register("historicos-padrao", views.HistoricoPadraoViewSet)
router.register("competencias", views.CompetenciaContabilViewSet)
router.register("lancamentos", views.LancamentoContabilViewSet)
router.register("relatorios", views.RelatorioContabilViewSet, basename="relatorio-contabil")

urlpatterns = router.urls
