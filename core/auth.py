from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .audit import get_client_ip, get_user_agent
from .models import LoginAttempt, NivelRisco, TipoEvento
from .services import registrar_evento


class ERPTokenObtainPairSerializer(TokenObtainPairSerializer):
    default_error_messages = {
        "no_active_account": "Usuario ou senha invalidos.",
        "locked": "Muitas tentativas de login. Tente novamente mais tarde.",
        "mfa_required": "MFA habilitado para o usuario. Informe o codigo MFA.",
    }

    def validate(self, attrs):
        request = self.context.get("request")
        username = attrs.get(self.username_field)
        password = attrs.get("password")
        ip = get_client_ip(request) if request else None
        user_agent = get_user_agent(request) if request else ""
        attempt, _ = LoginAttempt.objects.get_or_create(username=username, ip=ip)

        if attempt.bloqueado:
            raise serializers.ValidationError(self.error_messages["locked"])

        user = authenticate(request=request, username=username, password=password)
        if user is None:
            attempt.registrar_falha(
                limite=getattr(settings, "LOGIN_FAILURE_LIMIT", 5),
                minutos_bloqueio=getattr(settings, "LOGIN_LOCKOUT_MINUTES", 15),
            )
            registrar_evento(
                tipo_evento=TipoEvento.ALERTA_SISTEMA,
                usuario=None,
                empresa=None,
                modulo="core",
                tela="auth",
                acao="login_falhou",
                ip=ip,
                dispositivo=user_agent,
                origem="api",
                nivel_risco=NivelRisco.MEDIO,
                metadados={"username": username, "falhas": attempt.falhas},
            )
            raise serializers.ValidationError(self.error_messages["no_active_account"])

        if user.mfa_habilitado and attrs.get("mfa_code") != "000000":
            raise serializers.ValidationError(self.error_messages["mfa_required"])

        attempt.limpar()
        user.ultimo_ip = ip
        user.last_login = timezone.now()
        user.save(update_fields=["ultimo_ip", "last_login"])

        data = super().validate(attrs)
        data["user"] = {
            "id": user.id,
            "username": user.username,
            "empresa_id": user.empresa_id,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }
        registrar_evento(
            tipo_evento=TipoEvento.CRIACAO,
            usuario=user,
            empresa=user.empresa,
            modulo="core",
            tela="auth",
            acao="login_sucesso",
            ip=ip,
            dispositivo=user_agent,
            origem="api",
            nivel_risco=NivelRisco.BAIXO,
        )
        return data


class ERPTokenObtainPairSerializerWithMFA(ERPTokenObtainPairSerializer):
    mfa_code = serializers.CharField(required=False, allow_blank=True)
