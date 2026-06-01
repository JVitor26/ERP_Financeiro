from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.permissions import PermissaoPorAcao
from core.views import EmpresaScopedQuerysetMixin

from .models import AlertaIA, Anomalia, PrevisaoIA
from .serializers import (
    AlertaIASerializer,
    AnomaliaSerializer,
    FeedbackAnaliseSerializer,
    HorizontePrevisaoSerializer,
    PrevisaoIASerializer,
)
from .services import (
    detectar_pagamentos_duplicados,
    executar_varredura_ia,
    gerar_previsao_baseline_caixa,
    registrar_feedback_analise,
)


def empresa_do_usuario(request):
    empresa = getattr(request.user, "empresa", None)
    if empresa is None:
        raise ValidationError({"empresa": "Usuario sem empresa vinculada."})
    return empresa


class AlertaIAViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = AlertaIA.objects.select_related("empresa")
    serializer_class = AlertaIASerializer
    permissao_base = "inteligencia.alertas"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "nivel_risco", "status", "origem_modelo", "origem_id"]
    search_fields = ["titulo", "mensagem"]
    ordering_fields = ["criado_em", "nivel_risco", "score"]


class AnomaliaViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Anomalia.objects.select_related("empresa")
    serializer_class = AnomaliaSerializer
    permissao_base = "inteligencia.anomalias"
    permissao_action_map = {
        "detectar_duplicidades": "inteligencia.anomalias.gerar",
        "varredura": "inteligencia.anomalias.gerar",
        "feedback": "inteligencia.anomalias.editar",
    }
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "tipo", "nivel_risco", "status", "entidade_modelo", "entidade_id"]
    search_fields = ["descricao", "entidade_modelo", "entidade_id"]
    ordering_fields = ["criado_em", "nivel_risco"]

    @action(detail=False, methods=["post"])
    def detectar_duplicidades(self, request):
        anomalias = detectar_pagamentos_duplicados(empresa=empresa_do_usuario(request))
        return Response(AnomaliaSerializer(anomalias, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def varredura(self, request):
        resultado = executar_varredura_ia(empresa=empresa_do_usuario(request))
        return Response(
            {
                "duplicidades": AnomaliaSerializer(resultado["duplicidades"], many=True).data,
                "fora_padrao": AnomaliaSerializer(resultado["fora_padrao"], many=True).data,
                "previsao": PrevisaoIASerializer(resultado["previsao"]).data,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"])
    def feedback(self, request, pk=None):
        serializer = FeedbackAnaliseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        analise = registrar_feedback_analise(
            analise=self.get_object(),
            usuario=request.user,
            status=serializer.validated_data["status"],
            observacao=serializer.validated_data.get("observacao", ""),
        )
        return Response(AnomaliaSerializer(analise).data)


class PrevisaoIAViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = PrevisaoIA.objects.select_related("empresa")
    serializer_class = PrevisaoIASerializer
    permissao_base = "inteligencia.previsoes"
    permissao_action_map = {"gerar_baseline_caixa": "inteligencia.previsoes.editar"}
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "metrica", "modelo", "data_referencia"]
    search_fields = ["nome", "metrica", "modelo"]
    ordering_fields = ["data_referencia", "horizonte_dias", "valor_previsto", "confianca"]

    @action(detail=False, methods=["post"])
    def gerar_baseline_caixa(self, request):
        serializer = HorizontePrevisaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        horizonte_dias = serializer.validated_data["horizonte_dias"]
        previsao = gerar_previsao_baseline_caixa(empresa=empresa_do_usuario(request), horizonte_dias=horizonte_dias)
        return Response(PrevisaoIASerializer(previsao).data, status=status.HTTP_201_CREATED)
