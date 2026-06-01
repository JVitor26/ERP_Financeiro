from rest_framework import serializers

from .models import (
    AprovacaoPagamento,
    AnexoFinanceiro,
    CentroCusto,
    Cliente,
    ConciliacaoBancaria,
    ContaBancaria,
    ContaPagar,
    ContaReceber,
    Fornecedor,
    MovimentacaoFinanceira,
    Orcamento,
    PlanoConta,
    RelatorioGerado,
    Servico,
    StatusContaPagar,
    StatusContaReceber,
)


def validar_valores_nao_negativos(attrs, campos):
    for campo in campos:
        valor = attrs.get(campo)
        if valor is not None and valor < 0:
            raise serializers.ValidationError({campo: "Valor nao pode ser negativo."})


def validar_empresa_relacionada(attrs, empresa, campos):
    if not empresa:
        return
    for campo in campos:
        objeto = attrs.get(campo)
        if objeto is not None and getattr(objeto, "empresa_id", empresa.id) != empresa.id:
            raise serializers.ValidationError({campo: "Registro pertence a outra empresa."})


class CentroCustoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CentroCusto
        fields = "__all__"


class PlanoContaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanoConta
        fields = "__all__"


class ContaBancariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContaBancaria
        fields = "__all__"


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = "__all__"


class FornecedorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fornecedor
        fields = "__all__"


class ServicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Servico
        fields = "__all__"

    def validate(self, attrs):
        instancia = self.instance
        valor_padrao = attrs.get("valor_padrao", getattr(instancia, "valor_padrao", None))
        empresa = attrs.get("empresa") or getattr(instancia, "empresa", None)
        validar_valores_nao_negativos(attrs, ["valor_padrao"])
        validar_empresa_relacionada(attrs, empresa, ["plano_conta"])
        if valor_padrao is not None and valor_padrao < 0:
            raise serializers.ValidationError({"valor_padrao": "Valor padrao nao pode ser negativo."})
        return attrs


class ContaPagarSerializer(serializers.ModelSerializer):
    saldo_pendente = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    valor_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = ContaPagar
        fields = "__all__"
        read_only_fields = ["valor_pago", "data_baixa", "baixado_por", "excluido_logicamente", "excluido_em", "excluido_por"]

    def validate(self, attrs):
        instancia = self.instance
        empresa = attrs.get("empresa") or getattr(instancia, "empresa", None)
        validar_valores_nao_negativos(attrs, ["valor_original", "desconto", "juros", "multa", "acrescimo"])
        validar_empresa_relacionada(attrs, empresa, ["fornecedor", "centro_custo", "plano_conta", "conta_bancaria"])
        valor_original = attrs.get("valor_original", getattr(instancia, "valor_original", None))
        desconto = attrs.get("desconto", getattr(instancia, "desconto", 0))
        data_emissao = attrs.get("data_emissao", getattr(instancia, "data_emissao", None))
        data_vencimento = attrs.get("data_vencimento", getattr(instancia, "data_vencimento", None))
        status = attrs.get("status", getattr(instancia, "status", None))
        if valor_original is not None and valor_original <= 0:
            raise serializers.ValidationError({"valor_original": "Valor original deve ser maior que zero."})
        if desconto and valor_original and desconto > valor_original:
            raise serializers.ValidationError({"desconto": "Desconto nao pode ser maior que o valor original."})
        if data_emissao and data_vencimento and data_vencimento < data_emissao:
            raise serializers.ValidationError({"data_vencimento": "Vencimento nao pode ser anterior a emissao."})
        if instancia and instancia.status == StatusContaPagar.PAGO:
            protegidos = {"valor_original", "data_vencimento", "fornecedor", "status"}
            if protegidos.intersection(attrs):
                raise serializers.ValidationError("Conta paga nao pode ter campos financeiros criticos alterados.")
        if status == StatusContaPagar.PAGO:
            raise serializers.ValidationError({"status": "Use a acao de baixa para marcar conta como paga."})
        return attrs


class ContaReceberSerializer(serializers.ModelSerializer):
    saldo_pendente = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    valor_total = serializers.DecimalField(max_digits=14, decimal_places=2, read_only=True)
    dias_atraso = serializers.IntegerField(read_only=True)

    class Meta:
        model = ContaReceber
        fields = "__all__"
        read_only_fields = [
            "valor_recebido",
            "data_recebimento",
            "recebido_por",
            "conta_original",
            "renegociado_em",
            "renegociado_por",
            "excluido_logicamente",
            "excluido_em",
            "excluido_por",
        ]

    def validate(self, attrs):
        instancia = self.instance
        empresa = attrs.get("empresa") or getattr(instancia, "empresa", None)
        validar_valores_nao_negativos(attrs, ["valor_original", "desconto", "juros", "multa", "acrescimo", "honorarios"])
        validar_empresa_relacionada(attrs, empresa, ["cliente", "centro_custo", "plano_conta", "conta_bancaria"])
        valor_original = attrs.get("valor_original", getattr(instancia, "valor_original", None))
        desconto = attrs.get("desconto", getattr(instancia, "desconto", 0))
        data_emissao = attrs.get("data_emissao", getattr(instancia, "data_emissao", None))
        data_vencimento = attrs.get("data_vencimento", getattr(instancia, "data_vencimento", None))
        status = attrs.get("status", getattr(instancia, "status", None))
        if valor_original is not None and valor_original <= 0:
            raise serializers.ValidationError({"valor_original": "Valor original deve ser maior que zero."})
        if desconto and valor_original and desconto > valor_original:
            raise serializers.ValidationError({"desconto": "Desconto nao pode ser maior que o valor original."})
        if data_emissao and data_vencimento and data_vencimento < data_emissao:
            raise serializers.ValidationError({"data_vencimento": "Vencimento nao pode ser anterior a emissao."})
        if instancia and instancia.status == StatusContaReceber.RECEBIDO:
            protegidos = {"valor_original", "data_vencimento", "cliente", "status"}
            if protegidos.intersection(attrs):
                raise serializers.ValidationError("Conta recebida nao pode ter campos financeiros criticos alterados.")
        if status == StatusContaReceber.RECEBIDO:
            raise serializers.ValidationError({"status": "Use a acao de recebimento para marcar conta como recebida."})
        return attrs


class MovimentacaoFinanceiraSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovimentacaoFinanceira
        fields = "__all__"


class ConciliacaoBancariaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConciliacaoBancaria
        fields = "__all__"


class OrcamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Orcamento
        fields = "__all__"


class AprovacaoPagamentoSerializer(serializers.ModelSerializer):
    solicitante_nome = serializers.SerializerMethodField()
    aprovador_nome = serializers.SerializerMethodField()
    conta_pagar_detalhes = serializers.SerializerMethodField()

    class Meta:
        model = AprovacaoPagamento
        fields = "__all__"
        read_only_fields = ["solicitante", "aprovador", "status", "decidido_em"]

    def get_solicitante_nome(self, obj):
        return obj.solicitante.username if obj.solicitante else None

    def get_aprovador_nome(self, obj):
        return obj.aprovador.username if obj.aprovador else None

    def get_conta_pagar_detalhes(self, obj):
        if obj.conta_pagar:
            return {
                "fornecedor": obj.conta_pagar.fornecedor.nome if obj.conta_pagar.fornecedor else None,
                "numero_documento": obj.conta_pagar.numero_documento,
                "valor_total": obj.conta_pagar.valor_total,
                "data_vencimento": obj.conta_pagar.data_vencimento,
                "descricao": obj.conta_pagar.descricao,
            }
        return None


class RelatorioGeradoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RelatorioGerado
        fields = "__all__"


class AnexoFinanceiroSerializer(serializers.ModelSerializer):
    class Meta:
        model = AnexoFinanceiro
        fields = "__all__"
        read_only_fields = ["empresa", "nome_original", "content_type", "tamanho", "enviado_por"]


class BaixaContaPagarSerializer(serializers.Serializer):
    valor = serializers.DecimalField(max_digits=14, decimal_places=2)
    conta_bancaria = serializers.IntegerField(required=False)
    forma_pagamento = serializers.CharField(required=False, allow_blank=True)


class RecebimentoContaReceberSerializer(serializers.Serializer):
    valor = serializers.DecimalField(max_digits=14, decimal_places=2)
    conta_bancaria = serializers.IntegerField(required=False)
    forma_recebimento = serializers.CharField(required=False, allow_blank=True)


class FluxoCaixaResumoSerializer(serializers.Serializer):
    data_inicio = serializers.DateField()
    data_fim = serializers.DateField()

    def validate(self, attrs):
        if attrs["data_fim"] < attrs["data_inicio"]:
            raise serializers.ValidationError({"data_fim": "Data final deve ser maior ou igual a inicial."})
        return attrs


class AprovacaoAcaoSerializer(serializers.Serializer):
    justificativa = serializers.CharField(required=True, min_length=5, help_text="Justificativa obrigatoria para a acao.")

    def validate_justificativa(self, value):
        if not value.strip():
            raise serializers.ValidationError("A justificativa não pode estar em branco.")
        return value


class RenegociacaoContaReceberSerializer(serializers.Serializer):
    nova_data_vencimento = serializers.DateField()
    valor_original = serializers.DecimalField(max_digits=14, decimal_places=2)
    juros = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)
    multa = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)
    desconto = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)
    honorarios = serializers.DecimalField(max_digits=14, decimal_places=2, required=False, default=0)
    observacao = serializers.CharField(required=False, allow_blank=True)


class CancelamentoSerializer(serializers.Serializer):
    justificativa = serializers.CharField()


class RelatorioRequestSerializer(serializers.Serializer):
    tipo = serializers.ChoiceField(choices=["contas_pagar", "contas_receber", "eventos", "fluxo_caixa"])
    formato = serializers.ChoiceField(choices=["csv", "xlsx", "pdf"])
    data_inicio = serializers.DateField(required=False)
    data_fim = serializers.DateField(required=False)


class ConciliacaoImportCSVSerializer(serializers.Serializer):
    arquivo = serializers.FileField()
    conta_bancaria = serializers.IntegerField()


class ConciliacaoManualSerializer(serializers.Serializer):
    movimentacao = serializers.IntegerField()
