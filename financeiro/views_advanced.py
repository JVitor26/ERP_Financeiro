"""ViewSets para os modelos avançados do app financeiro (Fase 2/3/4)."""
import re
from decimal import Decimal
from datetime import date

from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from core.views import EmpresaScopedQuerysetMixin

from .models import (
    AplicacaoFinanceira,
    AlcadaAprovacao,
    AlcadaAprovador,
    CobrancaFinanceira,
    ContratoFinanceiro,
    CredencialBancaria,
    HistoricoCobranca,
    ImportacaoOFX,
    ParcelaContratoFinanceiro,
    PeriodoFechamento,
    RateioLancamento,
    RegraCobrancan,
    RegraConciliacao,
    RecorrenciaFinanceira,
    TransferenciaInterna,
    MovimentacaoFinanceira,
    ContaBancaria,
    TipoMovimentacao,
)
from .serializers import (
    AplicacaoFinanceiraSerializer,
    AlcadaAprovacaoSerializer,
    AlcadaAprovadorSerializer,
    CobrancaFinanceiraSerializer,
    ContratoFinanceiroSerializer,
    CredencialBancariaSerializer,
    HistoricoCobrancaSerializer,
    ImportacaoOFXSerializer,
    ParcelaContratoFinanceiroSerializer,
    PeriodoFechamentoSerializer,
    RateioLancamentoSerializer,
    RegraCobrancanSerializer,
    RegraConciliacaoSerializer,
    RecorrenciaFinanceiraSerializer,
    TransferenciaInternaSerializer,
)


def empresa_usuario(request):
    return request.user.empresa


# ─── RECORRÊNCIAS ────────────────────────────────────────────────────────────

class RecorrenciaFinanceiraViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = RecorrenciaFinanceiraSerializer
    queryset = RecorrenciaFinanceira.objects.all()
    filterset_fields = ["tipo", "status", "periodicidade"]
    search_fields = ["descricao"]
    ordering_fields = ["data_inicio", "descricao", "valor"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))

    @action(detail=True, methods=["post"])
    def pausar(self, request, pk=None):
        rec = self.get_object()
        rec.status = "pausada"
        rec.save(update_fields=["status"])
        return Response({"detail": "Recorrência pausada."})

    @action(detail=True, methods=["post"])
    def reativar(self, request, pk=None):
        rec = self.get_object()
        rec.status = "ativa"
        rec.save(update_fields=["status"])
        return Response({"detail": "Recorrência reativada."})

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        rec = self.get_object()
        rec.status = "cancelada"
        rec.save(update_fields=["status"])
        return Response({"detail": "Recorrência cancelada."})


# ─── PERÍODO DE FECHAMENTO ───────────────────────────────────────────────────

class PeriodoFechamentoViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = PeriodoFechamentoSerializer
    queryset = PeriodoFechamento.objects.all()
    filterset_fields = ["ano", "mes", "status"]
    ordering_fields = ["ano", "mes"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))

    @action(detail=True, methods=["post"])
    def fechar(self, request, pk=None):
        periodo = self.get_object()
        if periodo.esta_fechado():
            return Response({"detail": "Período já está fechado."}, status=status.HTTP_400_BAD_REQUEST)
        periodo.status = "fechado"
        periodo.fechado_em = timezone.now()
        periodo.fechado_por = request.user
        periodo.save(update_fields=["status", "fechado_em", "fechado_por"])
        return Response({"detail": f"Período {periodo.mes:02d}/{periodo.ano} fechado."})

    @action(detail=True, methods=["post"])
    def reabrir(self, request, pk=None):
        periodo = self.get_object()
        justificativa = request.data.get("justificativa", "").strip()
        if not justificativa:
            return Response({"detail": "Justificativa obrigatória para reabertura."}, status=status.HTTP_400_BAD_REQUEST)
        periodo.status = "reaberto"
        periodo.reaberto_em = timezone.now()
        periodo.reaberto_por = request.user
        periodo.justificativa = justificativa
        periodo.save(update_fields=["status", "reaberto_em", "reaberto_por", "justificativa"])
        return Response({"detail": f"Período {periodo.mes:02d}/{periodo.ano} reaberto."})


# ─── RATEIO ──────────────────────────────────────────────────────────────────

class RateioLancamentoViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = RateioLancamentoSerializer
    queryset = RateioLancamento.objects.all()
    filterset_fields = ["origem_modelo", "centro_custo", "plano_conta"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))


# ─── ALÇADA DE APROVAÇÃO ─────────────────────────────────────────────────────

class AlcadaAprovacaoViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = AlcadaAprovacaoSerializer
    queryset = AlcadaAprovacao.objects.prefetch_related("aprovadores").all()
    filterset_fields = ["ativo"]
    search_fields = ["nome"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))


# ─── CREDENCIAL BANCÁRIA ─────────────────────────────────────────────────────

class CredencialBancariaViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = CredencialBancariaSerializer
    queryset = CredencialBancaria.objects.all()
    filterset_fields = ["ativa", "tipo_integracao"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))


# ─── IMPORTAÇÃO OFX ──────────────────────────────────────────────────────────

class ImportacaoOFXViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ImportacaoOFXSerializer
    queryset = ImportacaoOFX.objects.all()
    parser_classes = [MultiPartParser]
    filterset_fields = ["status", "conta_bancaria"]
    ordering_fields = ["criado_em"]

    def perform_create(self, serializer):
        obj = serializer.save(
            empresa=empresa_usuario(self.request),
            importado_por=self.request.user,
            status="pendente",
        )
        self._processar_ofx(obj)

    def _processar_ofx(self, importacao):
        """Parse básico do arquivo OFX e cria ConciliacaoBancaria para cada transação."""
        from .models import ConciliacaoBancaria, StatusConciliacao
        try:
            conteudo = importacao.arquivo.read().decode("latin-1", errors="replace")
            importacao.status = "processando"
            importacao.save(update_fields=["status"])

            padrao = re.compile(
                r"<STMTTRN>.*?<DTPOSTED>(\d+).*?<TRNAMT>([-\d.]+).*?(?:<FITID>([^<]+))?.*?(?:<MEMO>([^<]*?))?(?:</STMTTRN>|<STMTTRN>)",
                re.DOTALL,
            )
            lancamentos = padrao.findall(conteudo)
            total = len(lancamentos)
            importados = 0
            duplicados = 0

            datas = []
            for match in lancamentos:
                dtposted, trnamt, fitid, memo = match
                try:
                    dt = date(int(dtposted[:4]), int(dtposted[4:6]), int(dtposted[6:8]))
                except Exception:
                    dt = timezone.localdate()
                valor = Decimal(trnamt.replace(",", "."))
                fitid = fitid.strip() if fitid else ""
                memo = memo.strip() if memo else ""
                datas.append(dt)

                # Verificar duplicidade por FITID
                if fitid and ConciliacaoBancaria.objects.filter(
                    empresa=importacao.empresa,
                    conta_bancaria=importacao.conta_bancaria,
                    metadados__fitid=fitid,
                ).exists():
                    duplicados += 1
                    continue

                ConciliacaoBancaria.objects.create(
                    empresa=importacao.empresa,
                    conta_bancaria=importacao.conta_bancaria,
                    data_movimento=dt,
                    valor=valor,
                    historico=memo or "Importado OFX",
                    status=StatusConciliacao.PENDENTE,
                    metadados={"fitid": fitid, "importacao_id": importacao.id},
                )
                importados += 1

            importacao.total_lancamentos = total
            importacao.lancamentos_importados = importados
            importacao.lancamentos_duplicados = duplicados
            importacao.status = "processado"
            if datas:
                importacao.data_inicio_extrato = min(datas)
                importacao.data_fim_extrato = max(datas)
            importacao.save()
        except Exception as exc:
            importacao.status = "erro"
            importacao.erro = str(exc)
            importacao.save(update_fields=["status", "erro"])


# ─── REGRA DE CONCILIAÇÃO ────────────────────────────────────────────────────

class RegraConciliacaoViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = RegraConciliacaoSerializer
    queryset = RegraConciliacao.objects.all()
    filterset_fields = ["ativa"]
    search_fields = ["nome"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))


# ─── COBRANÇA (BOLETO / PIX) ─────────────────────────────────────────────────

class CobrancaFinanceiraViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = CobrancaFinanceiraSerializer
    queryset = CobrancaFinanceira.objects.select_related("conta_receber").all()
    filterset_fields = ["tipo", "status"]
    ordering_fields = ["data_vencimento", "valor"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))

    @action(detail=True, methods=["post"])
    def gerar_pix(self, request, pk=None):
        cobranca = self.get_object()
        # Stub: gera código PIX simulado
        codigo_pix = f"00020126330014BR.GOV.BCB.PIX0111{cobranca.empresa_id}5204000053039865406{cobranca.valor}5802BR5913ERP Financeiro6009SAO PAULO62070503***6304"
        cobranca.codigo_pix = codigo_pix
        cobranca.save(update_fields=["codigo_pix"])
        return Response({"codigo_pix": codigo_pix, "detail": "Código PIX gerado (simulado)."})


# ─── RÉGUA DE COBRANÇA ───────────────────────────────────────────────────────

class RegraCobrancanViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = RegraCobrancanSerializer
    queryset = RegraCobrancan.objects.all()
    filterset_fields = ["ativo", "gatilho", "canal"]
    search_fields = ["nome"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))


# ─── HISTÓRICO DE COBRANÇA ───────────────────────────────────────────────────

class HistoricoCobrancaViewSet(EmpresaScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = HistoricoCobrancaSerializer
    queryset = HistoricoCobranca.objects.all()
    filterset_fields = ["canal", "status_envio"]


# ─── TRANSFERÊNCIA INTERNA ───────────────────────────────────────────────────

class TransferenciaInternaViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = TransferenciaInternaSerializer
    queryset = TransferenciaInterna.objects.select_related("conta_origem", "conta_destino").all()
    filterset_fields = ["conta_origem", "conta_destino"]
    ordering_fields = ["data_transferencia", "valor"]
    search_fields = ["descricao"]

    def perform_create(self, serializer):
        empresa = empresa_usuario(self.request)
        obj = serializer.save(empresa=empresa, realizado_por=self.request.user)
        self._gerar_movimentacoes(obj)

    def _gerar_movimentacoes(self, transferencia):
        MovimentacaoFinanceira.objects.create(
            empresa=transferencia.empresa,
            tipo=TipoMovimentacao.SAIDA,
            descricao=f"Transferência para {transferencia.conta_destino}",
            data_movimento=transferencia.data_transferencia,
            valor=transferencia.valor + transferencia.tarifa,
            conta_bancaria=transferencia.conta_origem,
            origem_modelo="financeiro.TransferenciaInterna",
            origem_id=str(transferencia.id),
        )
        mov_entrada = MovimentacaoFinanceira.objects.create(
            empresa=transferencia.empresa,
            tipo=TipoMovimentacao.ENTRADA,
            descricao=f"Transferência de {transferencia.conta_origem}",
            data_movimento=transferencia.data_transferencia,
            valor=transferencia.valor,
            conta_bancaria=transferencia.conta_destino,
            origem_modelo="financeiro.TransferenciaInterna",
            origem_id=str(transferencia.id),
        )
        transferencia.movimentacao_entrada = mov_entrada
        transferencia.save(update_fields=["movimentacao_entrada"])


# ─── CONTRATO FINANCEIRO (EMPRÉSTIMOS) ───────────────────────────────────────

class ContratoFinanceiroViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = ContratoFinanceiroSerializer
    queryset = ContratoFinanceiro.objects.prefetch_related("parcelas").all()
    filterset_fields = ["tipo", "status"]
    search_fields = ["descricao", "credor"]
    ordering_fields = ["data_inicio", "valor_principal"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))

    @action(detail=True, methods=["post"])
    def gerar_parcelas(self, request, pk=None):
        from .models import ContaPagar, Fornecedor
        from dateutil.relativedelta import relativedelta
        contrato = self.get_object()
        if contrato.parcelas.exists():
            return Response({"detail": "Parcelas já geradas."}, status=status.HTTP_400_BAD_REQUEST)

        parcelas_criadas = []
        valor_parcela = (contrato.valor_principal / contrato.total_parcelas).quantize(Decimal("0.01"))
        data_base = contrato.data_inicio
        for i in range(1, contrato.total_parcelas + 1):
            data_venc = data_base + relativedelta(months=i)
            juros = (valor_parcela * contrato.taxa_juros_mensal / 100).quantize(Decimal("0.01"))
            parcela = ParcelaContratoFinanceiro.objects.create(
                contrato=contrato,
                numero_parcela=i,
                data_vencimento=data_venc,
                valor_principal=valor_parcela,
                valor_juros=juros,
                valor_total=valor_parcela + juros,
                status="pendente",
            )
            parcelas_criadas.append(parcela.id)
        return Response({"detail": f"{contrato.total_parcelas} parcelas geradas.", "parcelas": parcelas_criadas})


# ─── APLICAÇÃO FINANCEIRA ────────────────────────────────────────────────────

class AplicacaoFinanceiraViewSet(EmpresaScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = AplicacaoFinanceiraSerializer
    queryset = AplicacaoFinanceira.objects.all()
    filterset_fields = ["tipo", "status"]
    search_fields = ["descricao", "banco"]
    ordering_fields = ["data_aplicacao", "valor_aplicado", "saldo_atual"]

    def perform_create(self, serializer):
        serializer.save(empresa=empresa_usuario(self.request))

    @action(detail=True, methods=["post"])
    def resgatar(self, request, pk=None):
        aplicacao = self.get_object()
        valor_resgate = Decimal(str(request.data.get("valor_resgatado", aplicacao.saldo_atual)))
        imposto = Decimal(str(request.data.get("valor_imposto", "0")))
        data_resgate = request.data.get("data_resgate") or str(timezone.localdate())
        aplicacao.data_resgate = data_resgate
        aplicacao.valor_resgatado = valor_resgate
        aplicacao.valor_imposto = imposto
        aplicacao.saldo_atual = Decimal("0.00")
        aplicacao.status = "resgatada"
        aplicacao.save(update_fields=["data_resgate", "valor_resgatado", "valor_imposto", "saldo_atual", "status"])
        return Response(AplicacaoFinanceiraSerializer(aplicacao).data)
