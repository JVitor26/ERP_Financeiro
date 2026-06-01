from datetime import date
from decimal import Decimal

from django.db import transaction
from django.db.models import Q, Sum
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from core.views import EmpresaScopedQuerysetMixin

from .models import (
    CentroResultadoContabil,
    CompetenciaContabil,
    ContaContabil,
    HistoricoPadrao,
    LancamentoContabil,
    NaturezaConta,
    PartidaContabil,
    StatusFechamento,
    TipoLancamentoContabil,
)
from .serializers import (
    CentroResultadoContabilSerializer,
    CompetenciaContabilSerializer,
    ContaContabilArvoreSerializer,
    ContaContabilSerializer,
    EstornarLancamentoSerializer,
    FecharCompetenciaSerializer,
    HistoricoPadraoSerializer,
    LancamentoContabilReadSerializer,
    LancamentoContabilSerializer,
    PartidaContabilSerializer,
    ReabrirCompetenciaSerializer,
)
from .services import calcular_saldo_conta, gerar_balancete


def _empresa_do_usuario(request):
    empresa = getattr(request.user, "empresa", None)
    if empresa is None:
        raise ValidationError({"empresa": "Usuário sem empresa vinculada."})
    return empresa


class ContaContabilViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ContaContabil.objects.select_related("empresa", "pai", "plano_conta_financeiro")
    serializer_class = ContaContabilSerializer
    filterset_fields = ["natureza", "ativo", "aceita_lancamento", "pai"]
    search_fields = ["codigo", "nome"]
    ordering_fields = ["codigo", "nome", "natureza"]

    @action(detail=False, methods=["get"], url_path="arvore")
    def arvore(self, request):
        """Retorna a hierarquia de contas contábeis (somente raízes com filhos aninhados)."""
        empresa = _empresa_do_usuario(request)
        ativo = request.query_params.get("ativo", "true").lower() == "true"
        raizes = ContaContabil.objects.filter(
            empresa=empresa,
            pai__isnull=True,
            ativo=ativo,
        ).prefetch_related("filhos")
        serializer = ContaContabilArvoreSerializer(
            raizes, many=True, context={"request": request}
        )
        return Response(serializer.data)


class CentroResultadoContabilViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CentroResultadoContabil.objects.select_related("empresa", "pai")
    serializer_class = CentroResultadoContabilSerializer
    filterset_fields = ["ativo", "pai"]
    search_fields = ["codigo", "nome"]
    ordering_fields = ["codigo", "nome"]


class HistoricoPadraoViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = HistoricoPadrao.objects.select_related("empresa")
    serializer_class = HistoricoPadraoSerializer
    filterset_fields = []
    search_fields = ["codigo", "descricao"]
    ordering_fields = ["codigo", "descricao"]


class CompetenciaContabilViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = CompetenciaContabil.objects.select_related(
        "empresa", "fechado_por", "reaberto_por"
    )
    serializer_class = CompetenciaContabilSerializer
    filterset_fields = ["ano", "mes", "status"]
    ordering_fields = ["ano", "mes", "status"]

    @action(detail=True, methods=["post"], url_path="fechar")
    def fechar(self, request, pk=None):
        """Fecha a competência contábil, impedindo novos lançamentos."""
        competencia = self.get_object()
        serializer = FecharCompetenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if competencia.esta_fechada():
            return Response(
                {"detail": "A competência já está fechada."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if competencia.status == StatusFechamento.EM_FECHAMENTO:
            return Response(
                {"detail": "A competência já está em processo de fechamento."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        competencia.status = StatusFechamento.FECHADO
        competencia.fechado_em = timezone.now()
        competencia.fechado_por = request.user
        competencia.save(update_fields=["status", "fechado_em", "fechado_por", "atualizado_em"])

        return Response(
            CompetenciaContabilSerializer(competencia, context={"request": request}).data
        )

    @action(detail=True, methods=["post"], url_path="reabrir")
    def reabrir(self, request, pk=None):
        """Reabre uma competência fechada, exigindo justificativa."""
        competencia = self.get_object()
        serializer = ReabrirCompetenciaSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not competencia.esta_fechada() and competencia.status != StatusFechamento.REABERTO:
            return Response(
                {"detail": "Somente competências fechadas podem ser reabertas."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        competencia.status = StatusFechamento.REABERTO
        competencia.reaberto_em = timezone.now()
        competencia.reaberto_por = request.user
        competencia.justificativa_reabertura = serializer.validated_data["justificativa"]
        competencia.save(
            update_fields=[
                "status",
                "reaberto_em",
                "reaberto_por",
                "justificativa_reabertura",
                "atualizado_em",
            ]
        )

        return Response(
            CompetenciaContabilSerializer(competencia, context={"request": request}).data
        )


class LancamentoContabilViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = LancamentoContabil.objects.select_related(
        "empresa", "historico_padrao", "usuario", "lancamento_original"
    ).prefetch_related("partidas__conta", "partidas__centro_resultado")
    filterset_fields = ["tipo", "estornado", "excluido_logicamente"]
    search_fields = ["historico", "numero", "origem_modelo", "origem_id"]
    ordering_fields = ["data_lancamento", "data_competencia", "numero"]

    def get_serializer_class(self):
        if self.action in ("list", "retrieve"):
            return LancamentoContabilReadSerializer
        return LancamentoContabilSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        data_ini = params.get("data_ini")
        data_fim = params.get("data_fim")
        conta_id = params.get("conta")

        if data_ini:
            queryset = queryset.filter(data_lancamento__gte=data_ini)
        if data_fim:
            queryset = queryset.filter(data_lancamento__lte=data_fim)
        if conta_id:
            queryset = queryset.filter(partidas__conta_id=conta_id).distinct()

        return queryset

    def perform_create(self, serializer):
        empresa = _empresa_do_usuario(self.request)
        serializer.save(empresa=empresa, usuario=self.request.user)

    @action(detail=True, methods=["post"], url_path="estornar")
    def estornar(self, request, pk=None):
        """Gera um lançamento de estorno inverso ao lançamento original."""
        lancamento = self.get_object()
        serializer = EstornarLancamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if lancamento.estornado:
            return Response(
                {"detail": "Este lançamento já foi estornado."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if lancamento.excluido_logicamente:
            return Response(
                {"detail": "Não é possível estornar um lançamento excluído."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        motivo = serializer.validated_data["motivo"]
        data_estorno = serializer.validated_data.get("data_estorno", date.today())

        with transaction.atomic():
            estorno = LancamentoContabil.objects.create(
                empresa=lancamento.empresa,
                data_lancamento=data_estorno,
                data_competencia=data_estorno,
                tipo=TipoLancamentoContabil.ESTORNO,
                historico=f"ESTORNO: {lancamento.historico} | Motivo: {motivo}",
                origem_modelo=lancamento.origem_modelo,
                origem_id=lancamento.origem_id,
                usuario=request.user,
                lancamento_original=lancamento,
            )
            # Create inverted partidas
            for partida in lancamento.partidas.all():
                tipo_invertido = "credito" if partida.tipo_partida == "debito" else "debito"
                PartidaContabil.objects.create(
                    lancamento=estorno,
                    conta=partida.conta,
                    centro_resultado=partida.centro_resultado,
                    tipo_partida=tipo_invertido,
                    valor=partida.valor,
                    historico_complementar=f"Estorno: {partida.historico_complementar}",
                )
            lancamento.estornado = True
            lancamento.save(update_fields=["estornado", "atualizado_em"])

        return Response(
            LancamentoContabilReadSerializer(estorno, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )


class RelatorioContabilViewSet(viewsets.ViewSet):
    """ViewSet de relatórios contábeis sem model próprio."""

    def _get_empresa(self, request):
        return _empresa_do_usuario(request)

    def _parse_periodo(self, request):
        """Extrai e valida data_ini e data_fim dos query params."""
        data_ini_str = request.query_params.get("data_ini")
        data_fim_str = request.query_params.get("data_fim")
        try:
            data_ini = date.fromisoformat(data_ini_str) if data_ini_str else date.today().replace(day=1)
            data_fim = date.fromisoformat(data_fim_str) if data_fim_str else date.today()
        except ValueError:
            raise ValidationError(
                {"detail": "Datas inválidas. Use o formato YYYY-MM-DD."}
            )
        return data_ini, data_fim

    @action(detail=False, methods=["get"], url_path="diario")
    def diario(self, request):
        """Lista lançamentos por período ordenados cronologicamente."""
        empresa = self._get_empresa(request)
        data_ini, data_fim = self._parse_periodo(request)

        lancamentos = (
            LancamentoContabil.objects.filter(
                empresa=empresa,
                excluido_logicamente=False,
                data_lancamento__gte=data_ini,
                data_lancamento__lte=data_fim,
            )
            .select_related("historico_padrao", "usuario")
            .prefetch_related("partidas__conta", "partidas__centro_resultado")
            .order_by("data_lancamento", "numero")
        )
        serializer = LancamentoContabilReadSerializer(
            lancamentos, many=True, context={"request": request}
        )
        return Response(
            {
                "data_ini": data_ini,
                "data_fim": data_fim,
                "total_lancamentos": lancamentos.count(),
                "lancamentos": serializer.data,
            }
        )

    @action(detail=False, methods=["get"], url_path="razao")
    def razao(self, request):
        """Detalha lançamentos de uma conta contábil específica no período."""
        empresa = self._get_empresa(request)
        data_ini, data_fim = self._parse_periodo(request)
        conta_id = request.query_params.get("conta")
        if not conta_id:
            raise ValidationError({"detail": "Parâmetro 'conta' é obrigatório."})

        try:
            conta = ContaContabil.objects.get(pk=conta_id, empresa=empresa)
        except ContaContabil.DoesNotExist:
            raise ValidationError({"detail": "Conta contábil não encontrada."})

        saldo = calcular_saldo_conta(conta, data_ini, data_fim)

        partidas = (
            PartidaContabil.objects.filter(
                conta=conta,
                lancamento__empresa=empresa,
                lancamento__excluido_logicamente=False,
                lancamento__data_lancamento__gte=data_ini,
                lancamento__data_lancamento__lte=data_fim,
            )
            .select_related("lancamento", "centro_resultado")
            .order_by("lancamento__data_lancamento", "lancamento__numero")
        )

        partidas_data = PartidaContabilSerializer(
            partidas, many=True, context={"request": request}
        ).data

        return Response(
            {
                "conta": {"id": conta.id, "codigo": conta.codigo, "nome": conta.nome},
                "data_ini": data_ini,
                "data_fim": data_fim,
                "debitos": saldo["debitos"],
                "creditos": saldo["creditos"],
                "saldo": saldo["saldo"],
                "partidas": partidas_data,
            }
        )

    @action(detail=False, methods=["get"], url_path="balancete")
    def balancete(self, request):
        """Saldos de todas as contas por período."""
        empresa = self._get_empresa(request)
        ano = request.query_params.get("ano")
        mes = request.query_params.get("mes")

        if not ano or not mes:
            raise ValidationError({"detail": "Parâmetros 'ano' e 'mes' são obrigatórios."})

        try:
            ano_int = int(ano)
            mes_int = int(mes)
        except ValueError:
            raise ValidationError({"detail": "Ano e mês devem ser inteiros."})

        linhas = gerar_balancete(empresa, ano_int, mes_int)
        return Response(
            {
                "empresa": str(empresa),
                "ano": ano_int,
                "mes": mes_int,
                "contas": linhas,
            }
        )

    @action(detail=False, methods=["get"], url_path="balanco-patrimonial")
    def balanco_patrimonial(self, request):
        """Agrupa contas em Ativo, Passivo e Patrimônio Líquido."""
        empresa = self._get_empresa(request)
        data_ini, data_fim = self._parse_periodo(request)

        def _saldo_natureza(naturezas):
            resultado = {}
            for nat in naturezas:
                contas = ContaContabil.objects.filter(
                    empresa=empresa, natureza=nat, ativo=True
                )
                total_debitos = Decimal("0.00")
                total_creditos = Decimal("0.00")
                contas_data = []
                for conta in contas:
                    saldo = calcular_saldo_conta(conta, data_ini, data_fim)
                    if saldo["debitos"] or saldo["creditos"]:
                        contas_data.append(
                            {
                                "id": conta.id,
                                "codigo": conta.codigo,
                                "nome": conta.nome,
                                "debitos": saldo["debitos"],
                                "creditos": saldo["creditos"],
                                "saldo": saldo["saldo"],
                            }
                        )
                    total_debitos += saldo["debitos"]
                    total_creditos += saldo["creditos"]
                resultado[nat] = {
                    "contas": contas_data,
                    "total_debitos": total_debitos,
                    "total_creditos": total_creditos,
                    "saldo": total_debitos - total_creditos,
                }
            return resultado

        ativo = _saldo_natureza([NaturezaConta.ATIVO])
        passivo_pl = _saldo_natureza(
            [NaturezaConta.PASSIVO, NaturezaConta.PATRIMONIO_LIQUIDO]
        )

        total_ativo = ativo[NaturezaConta.ATIVO]["saldo"]
        total_passivo = passivo_pl[NaturezaConta.PASSIVO]["saldo"]
        total_pl = passivo_pl[NaturezaConta.PATRIMONIO_LIQUIDO]["saldo"]

        return Response(
            {
                "data_ini": data_ini,
                "data_fim": data_fim,
                "ativo": ativo[NaturezaConta.ATIVO],
                "passivo": passivo_pl[NaturezaConta.PASSIVO],
                "patrimonio_liquido": passivo_pl[NaturezaConta.PATRIMONIO_LIQUIDO],
                "total_ativo": total_ativo,
                "total_passivo_pl": total_passivo + total_pl,
                "diferenca": total_ativo - (total_passivo + total_pl),
            }
        )

    @action(detail=False, methods=["get"], url_path="dre")
    def dre(self, request):
        """Demonstração do Resultado do Exercício: Receitas - Despesas - Custos = Resultado."""
        empresa = self._get_empresa(request)
        data_ini, data_fim = self._parse_periodo(request)

        def _total_natureza(natureza):
            contas = ContaContabil.objects.filter(
                empresa=empresa, natureza=natureza, ativo=True
            )
            contas_data = []
            total = Decimal("0.00")
            for conta in contas:
                saldo = calcular_saldo_conta(conta, data_ini, data_fim)
                valor = saldo["saldo"]
                if valor:
                    contas_data.append(
                        {
                            "id": conta.id,
                            "codigo": conta.codigo,
                            "nome": conta.nome,
                            "saldo": valor,
                        }
                    )
                    total += valor
            return contas_data, total

        receitas_contas, total_receitas = _total_natureza(NaturezaConta.RECEITA)
        despesas_contas, total_despesas = _total_natureza(NaturezaConta.DESPESA)
        custos_contas, total_custos = _total_natureza(NaturezaConta.CUSTO)
        resultado_contas, total_resultado_contas = _total_natureza(NaturezaConta.RESULTADO)

        # Para receitas (natureza credora): saldo = creditos - debitos (positivo = receita)
        # Para despesas/custos (natureza devedora): saldo = debitos - creditos (positivo = gasto)
        lucro_prejuizo = total_receitas - total_despesas - total_custos

        return Response(
            {
                "data_ini": data_ini,
                "data_fim": data_fim,
                "receitas": {
                    "contas": receitas_contas,
                    "total": total_receitas,
                },
                "despesas": {
                    "contas": despesas_contas,
                    "total": total_despesas,
                },
                "custos": {
                    "contas": custos_contas,
                    "total": total_custos,
                },
                "resultado_antes_impostos": lucro_prejuizo,
                "contas_resultado": resultado_contas,
                "resultado_liquido": lucro_prejuizo + total_resultado_contas,
            }
        )
