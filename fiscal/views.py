from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.views import EmpresaScopedQuerysetMixin

from .models import (
    ConfiguracaoFiscalEmpresa,
    ConfiguracaoImpostoPorServico,
    EventoFiscal,
    ImpostoApurado,
    NotaFiscal,
    ObrigacaoFiscal,
    StatusNotaFiscal,
)
from .serializers import (
    ApurarImpostosSerializer,
    CalcularImpostosSerializer,
    CancelarNotaFiscalSerializer,
    ConfiguracaoFiscalEmpresaSerializer,
    ConfiguracaoImpostoPorServicoSerializer,
    EventoFiscalSerializer,
    ImpostoApuradoSerializer,
    NotaFiscalSerializer,
    NotaFiscalListSerializer,
    ObrigacaoFiscalSerializer,
)
from .services import calcular_impostos_nota, apurar_impostos_periodo


class ConfiguracaoFiscalEmpresaViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ConfiguracaoFiscalEmpresaSerializer
    queryset = ConfiguracaoFiscalEmpresa.objects.all()

    def get_queryset(self):
        empresa = self.request.user.empresa
        return ConfiguracaoFiscalEmpresa.objects.filter(empresa=empresa)

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)


class NotaFiscalViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = NotaFiscal.objects.select_related("cliente", "fornecedor").prefetch_related("itens", "eventos")
    filterset_fields = ["status", "tipo", "cliente", "fornecedor"]
    search_fields = ["numero", "chave_acesso", "cliente__nome", "fornecedor__nome"]
    ordering_fields = ["data_emissao", "valor_total", "numero"]

    def get_serializer_class(self):
        if self.action == "list":
            return NotaFiscalListSerializer
        return NotaFiscalSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        data_ini = self.request.query_params.get("data_ini")
        data_fim = self.request.query_params.get("data_fim")
        if data_ini:
            qs = qs.filter(data_emissao__gte=data_ini)
        if data_fim:
            qs = qs.filter(data_emissao__lte=data_fim)
        return qs

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        nota = self.get_object()
        serializer = CancelarNotaFiscalSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if nota.status not in (StatusNotaFiscal.EMITIDA, StatusNotaFiscal.AUTORIZADA):
            return Response(
                {"detail": "Apenas notas emitidas ou autorizadas podem ser canceladas."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        nota.status = StatusNotaFiscal.CANCELADA
        nota.save(update_fields=["status"])
        EventoFiscal.objects.create(
            nota_fiscal=nota,
            tipo_evento="cancelamento",
            descricao=serializer.validated_data["justificativa"],
            usuario=request.user,
        )
        return Response({"detail": "Nota fiscal cancelada."})

    @action(detail=True, methods=["post"])
    def calcular_impostos(self, request, pk=None):
        nota = self.get_object()
        resultado = calcular_impostos_nota(nota)
        return Response(resultado)


class EventoFiscalViewSet(EmpresaScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = EventoFiscalSerializer
    queryset = EventoFiscal.objects.select_related("nota_fiscal", "usuario")

    def get_queryset(self):
        empresa = self.request.user.empresa
        return EventoFiscal.objects.filter(nota_fiscal__empresa=empresa)


class ImpostoApuradoViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ImpostoApuradoSerializer
    queryset = ImpostoApurado.objects.all()
    filterset_fields = ["ano", "mes", "tipo_imposto"]
    ordering_fields = ["ano", "mes", "tipo_imposto"]

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)

    @action(detail=False, methods=["post"])
    def apurar(self, request):
        serializer = ApurarImpostosSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        empresa = request.user.empresa
        ano = serializer.validated_data["ano"]
        mes = serializer.validated_data["mes"]
        impostos = apurar_impostos_periodo(empresa, ano, mes)
        return Response({"detail": f"Apuração concluída.", "impostos": impostos})


class ObrigacaoFiscalViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ObrigacaoFiscalSerializer
    queryset = ObrigacaoFiscal.objects.all()
    filterset_fields = ["status", "tipo", "competencia_ano", "competencia_mes"]
    ordering_fields = ["data_vencimento", "competencia_ano", "competencia_mes"]
    search_fields = ["descricao"]

    def get_queryset(self):
        qs = super().get_queryset()
        data_ini = self.request.query_params.get("vencimento_ini")
        data_fim = self.request.query_params.get("vencimento_fim")
        if data_ini:
            qs = qs.filter(data_vencimento__gte=data_ini)
        if data_fim:
            qs = qs.filter(data_vencimento__lte=data_fim)
        return qs

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)


class ConfiguracaoImpostoPorServicoViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ConfiguracaoImpostoPorServicoSerializer
    queryset = ConfiguracaoImpostoPorServico.objects.select_related("servico")

    def perform_create(self, serializer):
        serializer.save(empresa=self.request.user.empresa)


class RelatorioFiscalViewSet(viewsets.ViewSet):
    """ViewSet de relatórios fiscais (sem model próprio)."""

    def get_empresa(self):
        return self.request.user.empresa

    @action(detail=False, methods=["get"])
    def resumo_impostos(self, request):
        from django.db.models import Sum
        empresa = self.get_empresa()
        ano = request.query_params.get("ano")
        mes = request.query_params.get("mes")
        qs = ImpostoApurado.objects.filter(empresa=empresa)
        if ano:
            qs = qs.filter(ano=ano)
        if mes:
            qs = qs.filter(mes=mes)
        resultado = (
            qs.values("tipo_imposto")
            .annotate(
                total_apurado=Sum("valor_apurado"),
                total_retido=Sum("valor_retido"),
                total_pagar=Sum("valor_a_pagar"),
            )
            .order_by("tipo_imposto")
        )
        return Response(list(resultado))

    @action(detail=False, methods=["get"])
    def notas_por_status(self, request):
        from django.db.models import Count
        empresa = self.get_empresa()
        qs = (
            NotaFiscal.objects.filter(empresa=empresa)
            .values("status")
            .annotate(total=Count("id"))
            .order_by("status")
        )
        return Response(list(qs))

    @action(detail=False, methods=["get"])
    def inconsistencias(self, request):
        empresa = self.get_empresa()
        sem_chave = NotaFiscal.objects.filter(
            empresa=empresa,
            status=StatusNotaFiscal.AUTORIZADA,
            chave_acesso="",
        ).values("id", "numero", "data_emissao", "valor_total")
        return Response(
            {
                "notas_autorizadas_sem_chave": list(sem_chave),
            }
        )
