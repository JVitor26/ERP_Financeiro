from datetime import date, datetime
from decimal import Decimal

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from django.utils import timezone

from core.audit import request_context
from core.models import NivelRisco, TipoEvento
from core.permissions import PermissaoPorAcao
from core.services import registrar_evento
from core.views import EmpresaScopedQuerysetMixin

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
    Servico,
)
from .reports import gerar_relatorio_response
from .serializers import (
    AprovacaoPagamentoSerializer,
    AprovacaoAcaoSerializer,
    AnexoFinanceiroSerializer,
    BaixaContaPagarSerializer,
    CancelamentoSerializer,
    CentroCustoSerializer,
    ClienteSerializer,
    ConciliacaoImportCSVSerializer,
    ConciliacaoManualSerializer,
    ConciliacaoBancariaSerializer,
    ContaBancariaSerializer,
    ContaPagarSerializer,
    ContaReceberSerializer,
    FluxoCaixaResumoSerializer,
    FornecedorSerializer,
    MovimentacaoFinanceiraSerializer,
    OrcamentoSerializer,
    PlanoContaSerializer,
    RelatorioRequestSerializer,
    RecebimentoContaReceberSerializer,
    RenegociacaoContaReceberSerializer,
    ServicoSerializer,
)
from .services import (
    baixar_conta_pagar,
    cancelar_conta_pagar,
    cancelar_conta_receber,
    conciliar_movimentacao,
    dashboard_financeiro,
    decidir_aprovacao_pagamento,
    dre_gerencial,
    importar_conciliacao_csv,
    receber_conta_receber,
    renegociar_conta_receber,
    resumo_fluxo_caixa,
    solicitar_aprovacao_pagamento,
    sugerir_conciliacoes,
)


def empresa_do_usuario(request):
    empresa = getattr(request.user, "empresa", None)
    if empresa is None:
        raise ValidationError({"empresa": "Usuario sem empresa vinculada."})
    return empresa


def _valor_json_seguro(valor):
    if isinstance(valor, Decimal):
        return str(valor)
    if isinstance(valor, (date, datetime)):
        return valor.isoformat()
    if hasattr(valor, "name"):
        return str(valor)
    return valor


def _snapshot_model(instance):
    return {
        field.name: _valor_json_seguro(field.value_from_object(instance))
        for field in instance._meta.concrete_fields
    }


def _empresa_do_registro(instance):
    empresa = getattr(instance, "empresa", None)
    if empresa is not None:
        return empresa
    conta_pagar = getattr(instance, "conta_pagar", None)
    if conta_pagar is not None:
        return conta_pagar.empresa
    return None


class AuditedFinanceiroMixin(EmpresaScopedQuerysetMixin):
    modulo_auditoria = "financeiro"
    tela_auditoria = ""

    def perform_create(self, serializer):
        super().perform_create(serializer)
        registro = serializer.instance
        ctx = request_context(self.request)
        registrar_evento(
            tipo_evento=TipoEvento.CRIACAO,
            usuario=self.request.user,
            empresa=_empresa_do_registro(registro),
            modulo=self.modulo_auditoria,
            tela=self.tela_auditoria,
            acao="criar",
            registro=registro,
            valor_novo=_snapshot_model(registro),
            nivel_risco=NivelRisco.MEDIO,
            **ctx,
        )

    def perform_update(self, serializer):
        valor_anterior = _snapshot_model(serializer.instance)
        super().perform_update(serializer)
        registro = serializer.instance
        ctx = request_context(self.request)
        registrar_evento(
            tipo_evento=TipoEvento.ALTERACAO,
            usuario=self.request.user,
            empresa=_empresa_do_registro(registro),
            modulo=self.modulo_auditoria,
            tela=self.tela_auditoria,
            acao="alterar",
            registro=registro,
            valor_anterior=valor_anterior,
            valor_novo=_snapshot_model(registro),
            nivel_risco=NivelRisco.MEDIO,
            **ctx,
        )


class SoftDeleteLancamentoMixin(AuditedFinanceiroMixin):
    def get_queryset(self):
        return super().get_queryset().filter(excluido_logicamente=False)

    def perform_destroy(self, instance):
        valor_anterior = _snapshot_model(instance)
        ctx = request_context(self.request)
        instance.excluido_logicamente = True
        instance.excluido_em = timezone.now()
        instance.excluido_por = self.request.user
        instance.save(update_fields=["excluido_logicamente", "excluido_em", "excluido_por", "atualizado_em"])
        registrar_evento(
            tipo_evento=TipoEvento.EXCLUSAO_LOGICA,
            usuario=self.request.user,
            empresa=_empresa_do_registro(instance),
            modulo=self.modulo_auditoria,
            tela=self.tela_auditoria,
            acao="excluir_logicamente",
            registro=instance,
            valor_anterior=valor_anterior,
            valor_novo=_snapshot_model(instance),
            nivel_risco=NivelRisco.ALTO,
            **ctx,
        )


class CentroCustoViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = CentroCusto.objects.select_related("empresa", "pai")
    serializer_class = CentroCustoSerializer
    tela_auditoria = "centros_custo"
    permissao_base = "financeiro.centros_custo"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "ativo", "pai"]
    search_fields = ["codigo", "nome"]
    ordering_fields = ["codigo", "nome"]


class PlanoContaViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = PlanoConta.objects.select_related("empresa", "pai")
    serializer_class = PlanoContaSerializer
    tela_auditoria = "plano_contas"
    permissao_base = "financeiro.plano_contas"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "tipo", "ativo", "pai"]
    search_fields = ["codigo", "nome"]
    ordering_fields = ["codigo", "nome"]


class ContaBancariaViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = ContaBancaria.objects.select_related("empresa")
    serializer_class = ContaBancariaSerializer
    tela_auditoria = "contas_bancarias"
    permissao_base = "financeiro.contas_bancarias"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "ativa", "banco"]
    search_fields = ["banco", "numero", "descricao"]


class ClienteViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = Cliente.objects.select_related("empresa")
    serializer_class = ClienteSerializer
    tela_auditoria = "clientes"
    permissao_base = "financeiro.clientes"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "ativo", "tipo_pessoa"]
    search_fields = ["nome", "documento", "email"]


class FornecedorViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = Fornecedor.objects.select_related("empresa")
    serializer_class = FornecedorSerializer
    tela_auditoria = "fornecedores"
    permissao_base = "financeiro.fornecedores"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "ativo", "tipo_pessoa"]
    search_fields = ["nome", "documento", "email"]


class ServicoViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = Servico.objects.select_related("empresa", "plano_conta")
    serializer_class = ServicoSerializer
    tela_auditoria = "servicos"
    permissao_base = "financeiro.servicos"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "ativo", "plano_conta"]
    search_fields = ["codigo", "nome", "descricao"]
    ordering_fields = ["nome", "codigo", "valor_padrao"]


class ContaPagarViewSet(SoftDeleteLancamentoMixin, viewsets.ModelViewSet):
    queryset = ContaPagar.objects.select_related("empresa", "fornecedor", "centro_custo", "plano_conta", "conta_bancaria")
    serializer_class = ContaPagarSerializer
    tela_auditoria = "contas_pagar"
    permissao_base = "financeiro.contas_pagar"
    permissao_action_map = {"baixar": "financeiro.contas_pagar.baixar"}
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "status", "fornecedor", "centro_custo", "plano_conta", "conta_bancaria"]
    search_fields = ["descricao", "fornecedor__nome", "numero_documento", "nota_fiscal"]
    ordering_fields = ["data_vencimento", "valor_original", "status"]

    @action(detail=True, methods=["post"])
    def baixar(self, request, pk=None):
        conta = self.get_object()
        serializer = BaixaContaPagarSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conta_bancaria = None
        conta_bancaria_id = serializer.validated_data.get("conta_bancaria")
        if conta_bancaria_id:
            conta_bancaria = ContaBancaria.objects.get(pk=conta_bancaria_id, empresa=conta.empresa)
        conta = baixar_conta_pagar(
            conta_pagar=conta,
            valor=serializer.validated_data["valor"],
            usuario=request.user,
            conta_bancaria=conta_bancaria,
            forma_pagamento=serializer.validated_data.get("forma_pagamento", ""),
        )
        return Response(ContaPagarSerializer(conta).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def solicitar_aprovacao(self, request, pk=None):
        conta = self.get_object()
        serializer = AprovacaoAcaoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        aprovacao = solicitar_aprovacao_pagamento(
            conta_pagar=conta,
            usuario=request.user,
            justificativa=serializer.validated_data.get("justificativa", ""),
        )
        return Response(AprovacaoPagamentoSerializer(aprovacao).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        conta = self.get_object()
        serializer = CancelamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conta = cancelar_conta_pagar(
            conta_pagar=conta,
            usuario=request.user,
            justificativa=serializer.validated_data["justificativa"],
        )
        return Response(ContaPagarSerializer(conta).data)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def anexar(self, request, pk=None):
        conta = self.get_object()
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            raise ValidationError({"arquivo": "Arquivo e obrigatorio."})
        anexo = AnexoFinanceiro.objects.create(
            empresa=conta.empresa,
            arquivo=arquivo,
            nome_original=arquivo.name,
            content_type=getattr(arquivo, "content_type", ""),
            tamanho=arquivo.size,
            origem_modelo="ContaPagar",
            origem_id=str(conta.pk),
            enviado_por=request.user,
        )
        return Response(AnexoFinanceiroSerializer(anexo).data, status=status.HTTP_201_CREATED)


class ContaReceberViewSet(SoftDeleteLancamentoMixin, viewsets.ModelViewSet):
    queryset = ContaReceber.objects.select_related("empresa", "cliente", "centro_custo", "plano_conta", "conta_bancaria")
    serializer_class = ContaReceberSerializer
    tela_auditoria = "contas_receber"
    permissao_base = "financeiro.contas_receber"
    permissao_action_map = {"receber": "financeiro.contas_receber.receber"}
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "status", "cliente", "centro_custo", "plano_conta", "conta_bancaria"]
    search_fields = ["descricao", "cliente__nome", "contrato"]
    ordering_fields = ["data_vencimento", "valor_original", "status"]

    @action(detail=True, methods=["post"])
    def receber(self, request, pk=None):
        conta = self.get_object()
        serializer = RecebimentoContaReceberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conta_bancaria = None
        conta_bancaria_id = serializer.validated_data.get("conta_bancaria")
        if conta_bancaria_id:
            conta_bancaria = ContaBancaria.objects.get(pk=conta_bancaria_id, empresa=conta.empresa)
        conta = receber_conta_receber(
            conta_receber=conta,
            valor=serializer.validated_data["valor"],
            usuario=request.user,
            conta_bancaria=conta_bancaria,
            forma_recebimento=serializer.validated_data.get("forma_recebimento", ""),
        )
        return Response(ContaReceberSerializer(conta).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def renegociar(self, request, pk=None):
        conta = self.get_object()
        serializer = RenegociacaoContaReceberSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        nova = renegociar_conta_receber(conta_receber=conta, usuario=request.user, dados=serializer.validated_data)
        return Response(ContaReceberSerializer(nova).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def cancelar(self, request, pk=None):
        conta = self.get_object()
        serializer = CancelamentoSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        conta = cancelar_conta_receber(
            conta_receber=conta,
            usuario=request.user,
            justificativa=serializer.validated_data["justificativa"],
        )
        return Response(ContaReceberSerializer(conta).data)

    @action(detail=True, methods=["post"], parser_classes=[MultiPartParser])
    def anexar(self, request, pk=None):
        conta = self.get_object()
        arquivo = request.FILES.get("arquivo")
        if not arquivo:
            raise ValidationError({"arquivo": "Arquivo e obrigatorio."})
        anexo = AnexoFinanceiro.objects.create(
            empresa=conta.empresa,
            arquivo=arquivo,
            nome_original=arquivo.name,
            content_type=getattr(arquivo, "content_type", ""),
            tamanho=arquivo.size,
            origem_modelo="ContaReceber",
            origem_id=str(conta.pk),
            enviado_por=request.user,
        )
        return Response(AnexoFinanceiroSerializer(anexo).data, status=status.HTTP_201_CREATED)


class MovimentacaoFinanceiraViewSet(EmpresaScopedQuerysetMixin, viewsets.ReadOnlyModelViewSet):
    queryset = MovimentacaoFinanceira.objects.select_related("empresa", "conta_bancaria", "centro_custo", "plano_conta")
    serializer_class = MovimentacaoFinanceiraSerializer
    permissao_base = "financeiro.movimentacoes"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "tipo", "conta_bancaria", "centro_custo", "plano_conta", "conciliado"]
    search_fields = ["descricao", "origem_modelo", "origem_id"]
    ordering_fields = ["data_movimento", "valor"]


class ConciliacaoBancariaViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = ConciliacaoBancaria.objects.select_related("empresa", "conta_bancaria", "movimentacao")
    serializer_class = ConciliacaoBancariaSerializer
    tela_auditoria = "conciliacoes"
    permissao_base = "financeiro.conciliacoes"
    permissao_action_map = {
        "importar_csv": "financeiro.conciliacoes.importar",
        "sugerir": "financeiro.conciliacoes.editar",
        "conciliar": "financeiro.conciliacoes.conciliar",
    }
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "conta_bancaria", "status"]
    search_fields = ["historico", "documento"]
    ordering_fields = ["data_movimento", "valor"]

    @action(detail=False, methods=["post"], parser_classes=[MultiPartParser])
    def importar_csv(self, request):
        serializer = ConciliacaoImportCSVSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        criadas = importar_conciliacao_csv(
            empresa=empresa_do_usuario(request),
            conta_bancaria_id=serializer.validated_data["conta_bancaria"],
            arquivo=serializer.validated_data["arquivo"],
            usuario=request.user,
        )
        return Response(ConciliacaoBancariaSerializer(criadas, many=True).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"])
    def sugerir(self, request):
        sugestoes = sugerir_conciliacoes(empresa=empresa_do_usuario(request))
        return Response(ConciliacaoBancariaSerializer(sugestoes, many=True).data)

    @action(detail=True, methods=["post"])
    def conciliar(self, request, pk=None):
        conciliacao = self.get_object()
        serializer = ConciliacaoManualSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        movimentacao = MovimentacaoFinanceira.objects.get(
            pk=serializer.validated_data["movimentacao"],
            empresa=conciliacao.empresa,
        )
        conciliacao = conciliar_movimentacao(conciliacao=conciliacao, movimentacao=movimentacao, usuario=request.user)
        return Response(ConciliacaoBancariaSerializer(conciliacao).data)


class OrcamentoViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = Orcamento.objects.select_related("empresa", "centro_custo", "plano_conta")
    serializer_class = OrcamentoSerializer
    tela_auditoria = "orcamentos"
    permissao_base = "financeiro.orcamentos"
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["empresa", "ano", "mes", "centro_custo", "plano_conta"]


class AprovacaoPagamentoViewSet(AuditedFinanceiroMixin, viewsets.ModelViewSet):
    queryset = AprovacaoPagamento.objects.select_related("conta_pagar", "conta_pagar__empresa", "conta_pagar__fornecedor", "solicitante", "aprovador")
    serializer_class = AprovacaoPagamentoSerializer
    tela_auditoria = "aprovacoes_pagamento"
    empresa_field = "conta_pagar__empresa"
    permissao_base = "financeiro.contas_pagar"
    permissao_action_map = {
        "aprovar": "financeiro.contas_pagar.aprovar",
        "reprovar": "financeiro.contas_pagar.aprovar",
    }
    permission_classes = [PermissaoPorAcao]
    filterset_fields = ["conta_pagar", "status", "solicitante", "aprovador"]

    @action(detail=True, methods=["post"])
    def aprovar(self, request, pk=None):
        aprovacao = decidir_aprovacao_pagamento(
            aprovacao=self.get_object(),
            usuario=request.user,
            aprovado=True,
            justificativa=request.data.get("justificativa", ""),
        )
        return Response(AprovacaoPagamentoSerializer(aprovacao).data)

    @action(detail=True, methods=["post"])
    def reprovar(self, request, pk=None):
        aprovacao = decidir_aprovacao_pagamento(
            aprovacao=self.get_object(),
            usuario=request.user,
            aprovado=False,
            justificativa=request.data.get("justificativa", ""),
        )
        return Response(AprovacaoPagamentoSerializer(aprovacao).data)


class FluxoCaixaViewSet(viewsets.ViewSet):
    permissao_base = "financeiro.fluxo_caixa"
    permission_classes = [PermissaoPorAcao]
    serializer_class = FluxoCaixaResumoSerializer

    def list(self, request):
        serializer = FluxoCaixaResumoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        empresa = empresa_do_usuario(request)
        resumo = resumo_fluxo_caixa(
            empresa=empresa,
            data_inicio=serializer.validated_data["data_inicio"],
            data_fim=serializer.validated_data["data_fim"],
        )
        return Response(resumo)

    @action(detail=False, methods=["get"])
    def dashboard(self, request):
        serializer = FluxoCaixaResumoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(
            dashboard_financeiro(
                empresa=empresa_do_usuario(request),
                data_inicio=serializer.validated_data["data_inicio"],
                data_fim=serializer.validated_data["data_fim"],
            )
        )

    @action(detail=False, methods=["get"])
    def dre(self, request):
        serializer = FluxoCaixaResumoSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response(
            dre_gerencial(
                empresa=empresa_do_usuario(request),
                data_inicio=serializer.validated_data["data_inicio"],
                data_fim=serializer.validated_data["data_fim"],
            )
        )


class RelatorioFinanceiroViewSet(viewsets.ViewSet):
    permissao_base = "financeiro.relatorios"
    permissao_action_map = {"create": "financeiro.relatorios.exportar"}
    permission_classes = [PermissaoPorAcao]
    serializer_class = RelatorioRequestSerializer

    def create(self, request):
        serializer = RelatorioRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data_inicio = serializer.validated_data.get("data_inicio") or timezone.localdate().replace(day=1)
        data_fim = serializer.validated_data.get("data_fim") or timezone.localdate()
        return gerar_relatorio_response(
            empresa=empresa_do_usuario(request),
            usuario=request.user,
            tipo=serializer.validated_data["tipo"],
            formato=serializer.validated_data["formato"],
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
