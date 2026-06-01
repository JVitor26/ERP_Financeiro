from rest_framework import serializers

from .models import AlertaIA, Anomalia, PrevisaoIA


class AlertaIASerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertaIA
        fields = "__all__"


class AnomaliaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Anomalia
        fields = "__all__"


class PrevisaoIASerializer(serializers.ModelSerializer):
    class Meta:
        model = PrevisaoIA
        fields = "__all__"


class FeedbackAnaliseSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["confirmado", "descartado", "resolvido", "em_analise"])
    observacao = serializers.CharField(required=False, allow_blank=True)


class HorizontePrevisaoSerializer(serializers.Serializer):
    horizonte_dias = serializers.IntegerField(required=False, min_value=1, max_value=365, default=60)
