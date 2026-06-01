from django.contrib import admin
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView

from core.auth_views import ERPTokenObtainPairView, MeView


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
    path("api/core/", include("core.urls")),
    path("api/financeiro/", include("financeiro.urls")),
    path("api/inteligencia/", include("inteligencia.urls")),
]
