from rest_framework import serializers

from .models import (
    Empresa,
    EmpresaModulo,
    EventLog,
    Modulo,
    Notificacao,
    Perfil,
    PerfilPermissao,
    Permissao,
    Usuario,
    UsuarioPerfil,
)


class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = "__all__"


class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = "__all__"


class EmpresaModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmpresaModulo
        fields = "__all__"


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "password",
            "email",
            "first_name",
            "last_name",
            "empresa",
            "telefone",
            "cargo",
            "mfa_habilitado",
            "is_active",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["date_joined"]

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        usuario = super().create(validated_data)
        if password:
            usuario.set_password(password)
            usuario.save(update_fields=["password"])
        return usuario

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        usuario = super().update(instance, validated_data)
        if password:
            usuario.set_password(password)
            usuario.save(update_fields=["password"])
        return usuario


class PerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = Perfil
        fields = "__all__"


class PermissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permissao
        fields = "__all__"


class PerfilPermissaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = PerfilPermissao
        fields = "__all__"


class UsuarioPerfilSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsuarioPerfil
        fields = "__all__"


class EventLogSerializer(serializers.ModelSerializer):
    usuario_nome = serializers.CharField(source="usuario.username", read_only=True)
    empresa_nome = serializers.CharField(source="empresa.razao_social", read_only=True)

    class Meta:
        model = EventLog
        fields = "__all__"
        read_only_fields = [
            "id",
            "event_id",
            "tipo_evento",
            "usuario",
            "empresa",
            "modulo",
            "tela",
            "acao",
            "registro_modelo",
            "registro_id",
            "valor_anterior",
            "valor_novo",
            "ip",
            "dispositivo",
            "origem",
            "justificativa",
            "nivel_risco",
            "hash_anterior",
            "hash_evento",
            "metadados",
            "criado_em",
        ]


class NotificacaoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notificacao
        fields = "__all__"
