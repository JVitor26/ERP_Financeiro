from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from core.auth_views import ERPTokenObtainPairView, MeView
from core.views_mfa import (
    MFASetupView,
    MFAAtivarView,
    MFAVerificarView,
    MFADesativarView,
    MFABackupCodesView,
    MFARegenerarBackupCodesView,
)


def home(request):
    return render(request, "frontend/index.html")


def empty_response(request):
    return HttpResponse("", status=204)


urlpatterns = [
    path("", home),
    path("favicon.ico", empty_response),
    path("service-worker.js", empty_response),
    path("admin/", admin.site.urls),
    path("api/auth/token/", ERPTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/auth/token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("api/auth/me/", MeView.as_view(), name="auth_me"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/auth/mfa/setup/", MFASetupView.as_view(), name="mfa_setup"),
    path("api/auth/mfa/ativar/", MFAAtivarView.as_view(), name="mfa_ativar"),
    path("api/auth/mfa/verificar/", MFAVerificarView.as_view(), name="mfa_verificar"),
    path("api/auth/mfa/desativar/", MFADesativarView.as_view(), name="mfa_desativar"),
    path("api/auth/mfa/backup-codes/", MFABackupCodesView.as_view(), name="mfa_backup_codes"),
    path("api/auth/mfa/regenerar-backup-codes/", MFARegenerarBackupCodesView.as_view(), name="mfa_regenerar"),
    path("api/core/", include("core.urls")),
    path("api/financeiro/", include("financeiro.urls")),
    path("api/inteligencia/", include("inteligencia.urls")),
    path("api/contabil/", include("contabil.urls")),
    path("api/fiscal/", include("fiscal.urls")),
]
