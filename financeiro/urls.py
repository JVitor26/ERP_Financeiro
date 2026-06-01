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


router = DefaultRouter()
router.register("centros-custo", CentroCustoViewSet)
router.register("plano-contas", PlanoContaViewSet)
router.register("contas-bancarias", ContaBancariaViewSet)
router.register("clientes", ClienteViewSet)
router.register("fornecedores", FornecedorViewSet)
router.register("servicos", ServicoViewSet)
router.register("contas-pagar", ContaPagarViewSet)
router.register("contas-receber", ContaReceberViewSet)
router.register("movimentacoes", MovimentacaoFinanceiraViewSet)
router.register("conciliacoes", ConciliacaoBancariaViewSet)
router.register("orcamentos", OrcamentoViewSet)
router.register("aprovacoes-pagamento", AprovacaoPagamentoViewSet)
router.register("fluxo-caixa", FluxoCaixaViewSet, basename="fluxo-caixa")
router.register("relatorios", RelatorioFinanceiroViewSet, basename="relatorios")

urlpatterns = router.urls
