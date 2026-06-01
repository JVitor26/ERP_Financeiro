from decimal import Decimal

from django.db import transaction
from rest_framework import serializers

from .models import (
    CentroResultadoContabil,
    CompetenciaContabil,
    ContaContabil,
    HistoricoPadrao,
    LancamentoContabil,
    NaturezaConta,
    PartidaContabil,
    StatusFechamento,
)


class ContaContabilSerializer(serializers.ModelSerializer):
    natureza_display = serializers.CharField(source="get_natureza_display", read_only=True)
    tipo_saldo_display = serializers.CharField(source="get_tipo_saldo_display", read_only=True)
    pai_codigo = serializers.CharField(source="pai.codigo", read_only=True, default=None)

    class Meta:
        model = ContaContabil
        fields = [
            "id",
            "empresa",
            "codigo",
            "nome",
            "natureza",
            "natureza_display",
            "tipo_saldo",
            "tipo_saldo_display",
            "pai",
            "pai_codigo",
            "aceita_lancamento",
            "plano_conta_financeiro",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em"]

    def validate(self, data):
        natureza = data.get("natureza", getattr(self.instance, "natureza", None))
        tipo_saldo = data.get("tipo_saldo", getattr(self.instance, "tipo_saldo", None))
        _naturezas_devedoras = {NaturezaConta.ATIVO, NaturezaConta.DESPESA, NaturezaConta.CUSTO}
        if natureza and tipo_saldo:
            expected = "devedora" if natureza in _naturezas_devedoras else "credora"
            if tipo_saldo != expected:
                raise serializers.ValidationError(
                    {
                        "tipo_saldo": (
                            f"Para a natureza '{natureza}', o tipo de saldo deve ser '{expected}'."
                        )
                    }
                )
        return data


class ContaContabilArvoreSerializer(serializers.ModelSerializer):
    filhos = serializers.SerializerMethodField()

    class Meta:
        model = ContaContabil
        fields = [
            "id",
            "codigo",
            "nome",
            "natureza",
            "tipo_saldo",
            "aceita_lancamento",
            "ativo",
            "filhos",
        ]

    def get_filhos(self, obj):
        filhos = obj.filhos.filter(ativo=True)
        return ContaContabilArvoreSerializer(filhos, many=True, context=self.context).data


class CentroResultadoContabilSerializer(serializers.ModelSerializer):
    pai_codigo = serializers.CharField(source="pai.codigo", read_only=True, default=None)

    class Meta:
        model = CentroResultadoContabil
        fields = [
            "id",
            "empresa",
            "codigo",
            "nome",
            "pai",
            "pai_codigo",
            "ativo",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em"]


class HistoricoPadraoSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistoricoPadrao
        fields = [
            "id",
            "empresa",
            "codigo",
            "descricao",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "criado_em", "atualizado_em"]


class CompetenciaContabilSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    esta_fechada = serializers.SerializerMethodField()

    class Meta:
        model = CompetenciaContabil
        fields = [
            "id",
            "empresa",
            "ano",
            "mes",
            "status",
            "status_display",
            "esta_fechada",
            "fechado_em",
            "fechado_por",
            "reaberto_em",
            "reaberto_por",
            "justificativa_reabertura",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "status",
            "fechado_em",
            "fechado_por",
            "reaberto_em",
            "reaberto_por",
            "criado_em",
            "atualizado_em",
        ]

    def get_esta_fechada(self, obj):
        return obj.esta_fechada()

    def validate(self, data):
        mes = data.get("mes", getattr(self.instance, "mes", None))
        if mes is not None and not (1 <= mes <= 12):
            raise serializers.ValidationError({"mes": "O mês deve estar entre 1 e 12."})
        return data


class FecharCompetenciaSerializer(serializers.Serializer):
    confirmar = serializers.BooleanField(required=True)

    def validate_confirmar(self, value):
        if not value:
            raise serializers.ValidationError("É necessário confirmar o fechamento.")
        return value


class ReabrirCompetenciaSerializer(serializers.Serializer):
    justificativa = serializers.CharField(required=True, min_length=10)


class PartidaContabilSerializer(serializers.ModelSerializer):
    tipo_partida_display = serializers.CharField(
        source="get_tipo_partida_display", read_only=True
    )
    conta_codigo = serializers.CharField(source="conta.codigo", read_only=True)
    conta_nome = serializers.CharField(source="conta.nome", read_only=True)

    class Meta:
        model = PartidaContabil
        fields = [
            "id",
            "lancamento",
            "conta",
            "conta_codigo",
            "conta_nome",
            "centro_resultado",
            "tipo_partida",
            "tipo_partida_display",
            "valor",
            "historico_complementar",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = ["id", "lancamento", "criado_em", "atualizado_em"]

    def validate_valor(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value

    def validate_conta(self, conta):
        if not conta.aceita_lancamento:
            raise serializers.ValidationError(
                f"A conta '{conta}' é sintética e não aceita lançamentos diretos."
            )
        return conta


class PartidaContabilWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = PartidaContabil
        fields = [
            "conta",
            "centro_resultado",
            "tipo_partida",
            "valor",
            "historico_complementar",
        ]

    def validate_valor(self, value):
        if value <= 0:
            raise serializers.ValidationError("O valor deve ser maior que zero.")
        return value

    def validate_conta(self, conta):
        if not conta.aceita_lancamento:
            raise serializers.ValidationError(
                f"A conta '{conta}' é sintética e não aceita lançamentos diretos."
            )
        return conta


class LancamentoContabilSerializer(serializers.ModelSerializer):
    partidas = PartidaContabilWriteSerializer(many=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    usuario_nome = serializers.CharField(source="usuario.__str__", read_only=True, default=None)

    class Meta:
        model = LancamentoContabil
        fields = [
            "id",
            "empresa",
            "numero",
            "data_lancamento",
            "data_competencia",
            "tipo",
            "tipo_display",
            "historico",
            "historico_padrao",
            "origem_modelo",
            "origem_id",
            "usuario",
            "usuario_nome",
            "estornado",
            "lancamento_original",
            "excluido_logicamente",
            "justificativa_exclusao",
            "partidas",
            "criado_em",
            "atualizado_em",
        ]
        read_only_fields = [
            "id",
            "numero",
            "estornado",
            "criado_em",
            "atualizado_em",
        ]

    def _validar_balanco(self, partidas_data):
        debitos = sum(
            p["valor"] for p in partidas_data if p["tipo_partida"] == "debito"
        )
        creditos = sum(
            p["valor"] for p in partidas_data if p["tipo_partida"] == "credito"
        )
        if debitos != creditos:
            raise serializers.ValidationError(
                {
                    "partidas": (
                        f"O lançamento deve ser balanceado. "
                        f"Débitos: {debitos}, Créditos: {creditos}."
                    )
                }
            )
        if not partidas_data:
            raise serializers.ValidationError(
                {"partidas": "O lançamento deve ter ao menos uma partida."}
            )

    def validate(self, data):
        partidas_data = data.get("partidas", [])
        if partidas_data:
            self._validar_balanco(partidas_data)
        return data

    @transaction.atomic
    def create(self, validated_data):
        partidas_data = validated_data.pop("partidas", [])
        lancamento = LancamentoContabil.objects.create(**validated_data)
        for partida_data in partidas_data:
            PartidaContabil.objects.create(lancamento=lancamento, **partida_data)
        return lancamento

    @transaction.atomic
    def update(self, instance, validated_data):
        partidas_data = validated_data.pop("partidas", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if partidas_data is not None:
            instance.partidas.all().delete()
            for partida_data in partidas_data:
                PartidaContabil.objects.create(lancamento=instance, **partida_data)
        return instance


class LancamentoContabilReadSerializer(serializers.ModelSerializer):
    partidas = PartidaContabilSerializer(many=True, read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    usuario_nome = serializers.CharField(source="usuario.__str__", read_only=True, default=None)

    class Meta:
        model = LancamentoContabil
        fields = [
            "id",
            "empresa",
            "numero",
            "data_lancamento",
            "data_competencia",
            "tipo",
            "tipo_display",
            "historico",
            "historico_padrao",
            "origem_modelo",
            "origem_id",
            "usuario",
            "usuario_nome",
            "estornado",
            "lancamento_original",
            "excluido_logicamente",
            "justificativa_exclusao",
            "partidas",
            "criado_em",
            "atualizado_em",
        ]


class EstornarLancamentoSerializer(serializers.Serializer):
    motivo = serializers.CharField(required=True, min_length=5)
    data_estorno = serializers.DateField(required=False)
