"""
Views REST para gerenciamento de MFA TOTP.

Endpoints:
  POST   /api/auth/mfa/setup/                — gera secret + QR code
  POST   /api/auth/mfa/ativar/               — valida TOTP e ativa MFA
  POST   /api/auth/mfa/verificar/            — verifica código no login
  POST   /api/auth/mfa/desativar/            — desativa MFA
  GET    /api/auth/mfa/backup-codes/         — lista backup codes mascarados
  POST   /api/auth/mfa/regenerar-backup-codes/ — regenera backup codes
"""
import base64
import io
import secrets
import string

import pyotp
import qrcode
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .audit import get_client_ip, get_user_agent
from .models import MFASecret, NivelRisco, TipoEvento
from .services import registrar_evento

BACKUP_CODE_COUNT = 8
BACKUP_CODE_LENGTH = 10


def _gerar_backup_codes():
    """Gera N backup codes aleatórios alfanuméricos."""
    alfabeto = string.ascii_uppercase + string.digits
    return [
        "".join(secrets.choice(alfabeto) for _ in range(BACKUP_CODE_LENGTH))
        for _ in range(BACKUP_CODE_COUNT)
    ]


def _qrcode_base64(totp_uri: str) -> str:
    """Gera QR code PNG em base64 a partir de uma URI OTPAuth."""
    img = qrcode.make(totp_uri)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


class MFASetupView(APIView):
    """Gera secret TOTP e QR code para o usuário logado (sem ativar ainda)."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        issuer = "ERP Financeiro"
        uri = totp.provisioning_uri(name=user.email or user.username, issuer_name=issuer)
        qr_b64 = _qrcode_base64(uri)

        # Salva o secret temporário (não ativado ainda — ativado_em=None)
        mfa_secret, _ = MFASecret.objects.get_or_create(usuario=user)
        mfa_secret.secret = secret
        mfa_secret.ativado_em = None
        mfa_secret.backup_codes = []
        mfa_secret.save()

        registrar_evento(
            tipo_evento=TipoEvento.ACESSO_SENSIVEL,
            usuario=user,
            empresa=user.empresa,
            modulo="core",
            tela="mfa",
            acao="mfa_setup_iniciado",
            ip=get_client_ip(request),
            dispositivo=get_user_agent(request),
            origem="api",
            nivel_risco=NivelRisco.MEDIO,
        )

        return Response(
            {
                "secret": secret,
                "qr_code_base64": qr_b64,
                "otpauth_uri": uri,
            },
            status=status.HTTP_200_OK,
        )


class MFAAtivarView(APIView):
    """Valida código TOTP e ativa MFA para o usuário logado."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        codigo = request.data.get("codigo", "").strip()

        try:
            mfa_secret = MFASecret.objects.get(usuario=user)
        except MFASecret.DoesNotExist:
            return Response(
                {"detail": "Setup MFA nao iniciado. Chame /api/auth/mfa/setup/ primeiro."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if mfa_secret.ativado_em is not None:
            return Response(
                {"detail": "MFA ja esta ativo para este usuario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        totp = pyotp.TOTP(mfa_secret.secret)
        if not totp.verify(codigo, valid_window=1):
            return Response(
                {"detail": "Codigo TOTP invalido."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        backup_codes = _gerar_backup_codes()
        mfa_secret.backup_codes = backup_codes
        mfa_secret.ativado_em = timezone.now()
        mfa_secret.save()

        user.mfa_habilitado = True
        user.save(update_fields=["mfa_habilitado"])

        registrar_evento(
            tipo_evento=TipoEvento.ACESSO_SENSIVEL,
            usuario=user,
            empresa=user.empresa,
            modulo="core",
            tela="mfa",
            acao="mfa_ativado",
            ip=get_client_ip(request),
            dispositivo=get_user_agent(request),
            origem="api",
            nivel_risco=NivelRisco.ALTO,
        )

        return Response(
            {
                "detail": "MFA ativado com sucesso.",
                "backup_codes": backup_codes,
            },
            status=status.HTTP_200_OK,
        )


class MFAVerificarView(APIView):
    """
    Verifica código TOTP ou backup code.
    Usado durante o fluxo de login quando mfa_habilitado=True.
    Não requer autenticação JWT completa — pode ser chamado com token temporário
    ou após validação de usuário/senha.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        codigo = request.data.get("codigo", "").strip()

        if not user.mfa_habilitado:
            return Response(
                {"detail": "MFA nao esta habilitado para este usuario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mfa_secret = MFASecret.objects.get(usuario=user)
        except MFASecret.DoesNotExist:
            return Response(
                {"detail": "Configuracao MFA nao encontrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Verifica TOTP
        totp = pyotp.TOTP(mfa_secret.secret)
        if totp.verify(codigo, valid_window=1):
            registrar_evento(
                tipo_evento=TipoEvento.ACESSO_SENSIVEL,
                usuario=user,
                empresa=user.empresa,
                modulo="core",
                tela="mfa",
                acao="mfa_verificado_totp",
                ip=get_client_ip(request),
                dispositivo=get_user_agent(request),
                origem="api",
                nivel_risco=NivelRisco.BAIXO,
            )
            return Response({"detail": "Codigo TOTP valido.", "valido": True})

        # Verifica backup codes
        backup_codes = mfa_secret.backup_codes or []
        if codigo in backup_codes:
            backup_codes.remove(codigo)
            mfa_secret.backup_codes = backup_codes
            mfa_secret.save(update_fields=["backup_codes"])
            registrar_evento(
                tipo_evento=TipoEvento.ACESSO_SENSIVEL,
                usuario=user,
                empresa=user.empresa,
                modulo="core",
                tela="mfa",
                acao="mfa_verificado_backup_code",
                ip=get_client_ip(request),
                dispositivo=get_user_agent(request),
                origem="api",
                nivel_risco=NivelRisco.ALTO,
                metadados={"backup_codes_restantes": len(backup_codes)},
            )
            return Response(
                {
                    "detail": "Backup code valido. Codigo consumido.",
                    "valido": True,
                    "backup_codes_restantes": len(backup_codes),
                }
            )

        registrar_evento(
            tipo_evento=TipoEvento.ALERTA_SISTEMA,
            usuario=user,
            empresa=user.empresa,
            modulo="core",
            tela="mfa",
            acao="mfa_codigo_invalido",
            ip=get_client_ip(request),
            dispositivo=get_user_agent(request),
            origem="api",
            nivel_risco=NivelRisco.ALTO,
        )
        return Response(
            {"detail": "Codigo invalido.", "valido": False},
            status=status.HTTP_400_BAD_REQUEST,
        )


class MFADesativarView(APIView):
    """Desativa MFA com confirmação de senha."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        senha = request.data.get("senha", "")

        if not user.mfa_habilitado:
            return Response(
                {"detail": "MFA nao esta ativo para este usuario."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not check_password(senha, user.password):
            return Response(
                {"detail": "Senha incorreta."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Remove o secret e desativa MFA
        MFASecret.objects.filter(usuario=user).delete()
        user.mfa_habilitado = False
        user.save(update_fields=["mfa_habilitado"])

        registrar_evento(
            tipo_evento=TipoEvento.ACESSO_SENSIVEL,
            usuario=user,
            empresa=user.empresa,
            modulo="core",
            tela="mfa",
            acao="mfa_desativado",
            ip=get_client_ip(request),
            dispositivo=get_user_agent(request),
            origem="api",
            nivel_risco=NivelRisco.CRITICO,
        )

        return Response({"detail": "MFA desativado com sucesso."})


class MFABackupCodesView(APIView):
    """Retorna backup codes mascarados (exibe apenas os 3 últimos caracteres)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        if not user.mfa_habilitado:
            return Response(
                {"detail": "MFA nao esta ativo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mfa_secret = MFASecret.objects.get(usuario=user)
        except MFASecret.DoesNotExist:
            return Response(
                {"detail": "Configuracao MFA nao encontrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        backup_codes = mfa_secret.backup_codes or []
        mascarados = [f"{'*' * (len(c) - 3)}{c[-3:]}" for c in backup_codes]

        return Response(
            {
                "backup_codes_mascarados": mascarados,
                "total": len(backup_codes),
            }
        )


class MFARegenerarBackupCodesView(APIView):
    """Regenera backup codes — invalida os anteriores."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        if not user.mfa_habilitado:
            return Response(
                {"detail": "MFA nao esta ativo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            mfa_secret = MFASecret.objects.get(usuario=user)
        except MFASecret.DoesNotExist:
            return Response(
                {"detail": "Configuracao MFA nao encontrada."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        novos_codes = _gerar_backup_codes()
        mfa_secret.backup_codes = novos_codes
        mfa_secret.save(update_fields=["backup_codes"])

        registrar_evento(
            tipo_evento=TipoEvento.ACESSO_SENSIVEL,
            usuario=user,
            empresa=user.empresa,
            modulo="core",
            tela="mfa",
            acao="mfa_backup_codes_regenerados",
            ip=get_client_ip(request),
            dispositivo=get_user_agent(request),
            origem="api",
            nivel_risco=NivelRisco.ALTO,
        )

        return Response(
            {
                "detail": "Backup codes regenerados com sucesso.",
                "backup_codes": novos_codes,
            }
        )
