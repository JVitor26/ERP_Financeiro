from rest_framework import serializers

from .models import (
    ConfiguracaoFiscalEmpresa,
    ConfiguracaoImpostoPorServico,
    EventoFiscal,
    ImpostoApurado,
    ItemNotaFiscal,
    NotaFiscal,
    ObrigacaoFiscal,
)


class ConfiguracaoFiscalEmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfiguracaoFiscalEmpresa
        fields = "__all__"
        read_only_fields = ["criado_em", "atualizado_em"]


class ItemNotaFiscalSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemNotaFiscal
        fields = "__all__"
        read_only_fields = ["criado_em", "atualizado_em"]


class ItemNotaFiscalWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemNotaFiscal
        exclude = ["nota_fiscal"]
        read_only_fields = ["criado_em", "atualizado_em"]


class EventoFiscalSerializer(serializers.ModelSerializer):
    tipo_evento_display = serializers.CharField(source="get_tipo_evento_display", read_only=True)

    class Meta:
        model = EventoFiscal
        fields = "__all__"
        read_only_fields = ["criado_em", "atualizado_em"]


class NotaFiscalSerializer(serializers.ModelSerializer):
    itens = ItemNotaFiscalWriteSerializer(many=True, required=False)
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = NotaFiscal
        fields = "__all__"
        read_only_fields = ["criado_em", "atualizado_em"]

    def create(self, validated_data):
        itens_data = validated_data.pop("itens", [])
        nota = NotaFiscal.objects.create(**validated_data)
        for item_data in itens_data:
            ItemNotaFiscal.objects.create(nota_fiscal=nota, **item_data)
        return nota

    def update(self, instance, validated_data):
        itens_data = validated_data.pop("itens", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if itens_data is not None:
            instance.itens.all().delete()
            for item_data in itens_data:
                ItemNotaFiscal.objects.create(nota_fiscal=instance, **item_data)
        return instance


class NotaFiscalListSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)

    class Meta:
        model = NotaFiscal
        fields = [
            "id",
            "empresa",
            "tipo",
            "tipo_display",
            "numero",
            "serie",
            "data_emissao",
            "cliente",
            "fornecedor",
            "valor_total",
            "status",
            "status_display",
            "criado_em",
        ]


class CancelarNotaFiscalSerializer(serializers.Serializer):
    justificativa = serializers.CharField(min_length=15, max_length=255)


class CalcularImpostosSerializer(serializers.Serializer):
    nota_fiscal_id = serializers.IntegerField(read_only=True)
    valor_iss = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    valor_pis = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    valor_cofins = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    valor_inss = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)


class ImpostoApuradoSerializer(serializers.ModelSerializer):
    tipo_imposto_display = serializers.CharField(source="get_tipo_imposto_display", read_only=True)

    class Meta:
        model = ImpostoApurado
        fields = "__all__"
        read_only_fields = ["criado_em", "atualizado_em"]


class ApurarImpostosSerializer(serializers.Serializer):
    ano = serializers.IntegerField(min_value=2000, max_value=2100)
    mes = serializers.IntegerField(min_value=1, max_value=12)


class ObrigacaoFiscalSerializer(serializers.ModelSerializer):
    tipo_display = serializers.CharField(source="get_tipo_display", read_only=True)
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = ObrigacaoFiscal
        fields = "__all__"
        read_only_fields = ["criado_em", "atualizado_em"]


class ConfiguracaoImpostoPorServicoSerializer(serializers.ModelSerializer):
    tipo_imposto_display = serializers.CharField(source="get_tipo_imposto_display", read_only=True)

    class Meta:
        model = ConfiguracaoImpostoPorServico
        fields = "__all__"
        read_only_fields = ["criado_em", "atualizado_em"]


class ResumoImpostosSerializer(serializers.Serializer):
    ano = serializers.IntegerField()
    mes = serializers.IntegerField()


class ResumoPorStatusSerializer(serializers.Serializer):
    status = serializers.CharField()
    total = serializers.IntegerField()
    valor_total = serializers.DecimalField(max_digits=14, decimal_places=2)
