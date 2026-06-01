from rest_framework.routers import DefaultRouter

from .views import AlertaIAViewSet, AnomaliaViewSet, PrevisaoIAViewSet


router = DefaultRouter()
router.register("alertas", AlertaIAViewSet)
router.register("anomalias", AnomaliaViewSet)
router.register("previsoes", PrevisaoIAViewSet)

urlpatterns = router.urls
