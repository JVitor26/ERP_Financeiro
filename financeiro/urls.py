from rest_framework.routers import DefaultRouter

from .views import (
    AprovacaoPagamentoViewSet,
    CentroCustoViewSet,
    ClienteViewSet,
    ConciliacaoBancariaViewSet,
    ContaBancariaViewSet,
    ContaPagarViewSet,
    ContaReceberViewSet,
    FluxoCaixaViewSet,
    FornecedorViewSet,
    MovimentacaoFinanceiraViewSet,
    OrcamentoViewSet,
    PlanoContaViewSet,
    RelatorioFinanceiroViewSet,
    ServicoViewSet,
)
from .views_advanced import (
    AplicacaoFinanceiraViewSet,
    AlcadaAprovacaoViewSet,
    CobrancaFinanceiraViewSet,
    ContratoFinanceiroViewSet,
    CredencialBancariaViewSet,
    HistoricoCobrancaViewSet,
    ImportacaoOFXViewSet,
    PeriodoFechamentoViewSet,
    RateioLancamentoViewSet,
    RegraCobrancanViewSet,
    RegraConciliacaoViewSet,
    RecorrenciaFinanceiraViewSet,
    TransferenciaInternaViewSet,
)

router = DefaultRouter()
# Cadastros base
router.register("centros-custo", CentroCustoViewSet)
router.register("plano-contas", PlanoContaViewSet)
router.register("contas-bancarias", ContaBancariaViewSet)
router.register("clientes", ClienteViewSet)
router.register("fornecedores", FornecedorViewSet)
router.register("servicos", ServicoViewSet)
# Contas a pagar / receber
router.register("contas-pagar", ContaPagarViewSet)
router.register("contas-receber", ContaReceberViewSet)
# Movimentações e conciliação
router.register("movimentacoes", MovimentacaoFinanceiraViewSet)
router.register("conciliacoes", ConciliacaoBancariaViewSet)
# Orçamentos e aprovações
router.register("orcamentos", OrcamentoViewSet)
router.register("aprovacoes-pagamento", AprovacaoPagamentoViewSet)
# Relatórios e fluxo de caixa
router.register("fluxo-caixa", FluxoCaixaViewSet, basename="fluxo-caixa")
router.register("relatorios", RelatorioFinanceiroViewSet, basename="relatorios")
# ── Avançado (Fase 2/3/4) ──
router.register("recorrencias", RecorrenciaFinanceiraViewSet)
router.register("periodos-fechamento", PeriodoFechamentoViewSet)
router.register("rateios", RateioLancamentoViewSet)
router.register("alcadas-aprovacao", AlcadaAprovacaoViewSet)
router.register("credenciais-bancarias", CredencialBancariaViewSet)
router.register("importacoes-ofx", ImportacaoOFXViewSet)
router.register("regras-conciliacao", RegraConciliacaoViewSet)
router.register("cobrancas", CobrancaFinanceiraViewSet)
router.register("regras-cobranca", RegraCobrancanViewSet)
router.register("historico-cobranca", HistoricoCobrancaViewSet, basename="historico-cobranca")
router.register("transferencias-internas", TransferenciaInternaViewSet)
router.register("contratos-financeiros", ContratoFinanceiroViewSet)
router.register("aplicacoes-financeiras", AplicacaoFinanceiraViewSet)

urlpatterns = router.urls
