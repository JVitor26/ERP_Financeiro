from rest_framework.routers import DefaultRouter

from .views import (
    EmpresaModuloViewSet,
    EmpresaViewSet,
    EventLogViewSet,
    ModuloViewSet,
    NotificacaoViewSet,
    PerfilPermissaoViewSet,
    PerfilViewSet,
    PermissaoViewSet,
    UsuarioPerfilViewSet,
    UsuarioViewSet,
)


router = DefaultRouter()
router.register("empresas", EmpresaViewSet)
router.register("modulos", ModuloViewSet)
router.register("empresa-modulos", EmpresaModuloViewSet)
router.register("usuarios", UsuarioViewSet)
router.register("perfis", PerfilViewSet)
router.register("permissoes", PermissaoViewSet)
router.register("perfil-permissoes", PerfilPermissaoViewSet)
router.register("usuario-perfis", UsuarioPerfilViewSet)
router.register("eventos", EventLogViewSet)
router.register("notificacoes", NotificacaoViewSet)

urlpatterns = router.urls
