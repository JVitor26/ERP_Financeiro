from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
import csv
import io
from datetime import datetime, timedelta

from django.db.models import Q, Sum
from django.utils import timezone

from core.models import NivelRisco, TipoEvento
from core.services import registrar_evento

from .models import (
    CentroCusto,
    ContaPagar,
    ContaReceber,
    MovimentacaoFinanceira,
    AprovacaoPagamento,
    ConciliacaoBancaria,
    ContaBancaria,
    PlanoConta,
    StatusConciliacao,
    StatusAprovacao,
    StatusContaPagar,
    StatusContaReceber,
    TipoMovimentacao,
    TipoPlanoConta,
)


class BaixaInvalida(ValidationError):
    pass


@transaction.atomic
def baixar_conta_pagar(*, conta_pagar, valor, usuario, conta_bancaria=None, forma_pagamento=""):
    valor = Decimal(valor)
    if valor <= 0:
        raise BaixaInvalida("Nao e permitido baixar conta a pagar sem valor.")

    conta_pagar = ContaPagar.objects.select_for_update().get(pk=conta_pagar.pk)
    saldo_anterior = conta_pagar.saldo_pendente

    if conta_pagar.excluido_logicamente:
        raise BaixaInvalida("Conta excluida nao pode ser baixada.")
    if conta_pagar.status in {StatusContaPagar.PAGO, StatusContaPagar.CANCELADO, StatusContaPagar.REPROVADO}:
        raise BaixaInvalida("Status atual nao permite baixa.")
    if conta_pagar.aprovacoes.filter(status=StatusAprovacao.PENDENTE).exists():
        raise BaixaInvalida("Conta possui aprovacao pendente.")
    if valor > saldo_anterior:
        raise BaixaInvalida("Valor de baixa maior que o saldo pendente.")

    conta_pagar.valor_pago += valor
    conta_pagar.baixado_por = usuario
    conta_pagar.forma_pagamento = forma_pagamento or conta_pagar.forma_pagamento
    if conta_bancaria is not None:
        conta_pagar.conta_bancaria = conta_bancaria
    conta_pagar.atualizar_status_por_saldo()
    conta_pagar.save(
        update_fields=[
            "valor_pago",
            "baixado_por",
            "forma_pagamento",
            "conta_bancaria",
            "status",
            "data_baixa",
            "atualizado_em",
        ]
    )

    if conta_pagar.conta_bancaria:
        MovimentacaoFinanceira.objects.create(
            empresa=conta_pagar.empresa,
            tipo=TipoMovimentacao.SAIDA,
            descricao=conta_pagar.descricao,
            data_movimento=timezone.localdate(),
            data_competencia=conta_pagar.data_emissao,
            valor=valor,
            conta_bancaria=conta_pagar.conta_bancaria,
            centro_custo=conta_pagar.centro_custo,
            plano_conta=conta_pagar.plano_conta,
            origem_modelo="ContaPagar",
            origem_id=str(conta_pagar.pk),
        )

    registrar_evento(
        tipo_evento=TipoEvento.BAIXA,
        usuario=usuario,
        registro=conta_pagar,
        modulo="financeiro",
        tela="contas_pagar",
        acao="baixar_pagamento",
        valor_anterior={"saldo_pendente": str(saldo_anterior)},
        valor_novo={"valor_baixado": str(valor), "saldo_pendente": str(conta_pagar.saldo_pendente)},
        nivel_risco=NivelRisco.MEDIO,
    )
    return conta_pagar


@transaction.atomic
def receber_conta_receber(*, conta_receber, valor, usuario, conta_bancaria=None, forma_recebimento=""):
    valor = Decimal(valor)
    if valor <= 0:
        raise BaixaInvalida("Nao e permitido receber conta sem valor.")

    conta_receber = ContaReceber.objects.select_for_update().get(pk=conta_receber.pk)
    saldo_anterior = conta_receber.saldo_pendente

    if conta_receber.excluido_logicamente:
        raise BaixaInvalida("Conta excluida nao pode ser recebida.")
    if conta_receber.status in {StatusContaReceber.RECEBIDO, StatusContaReceber.CANCELADO}:
        raise BaixaInvalida("Status atual nao permite recebimento.")
    if valor > saldo_anterior:
        raise BaixaInvalida("Valor recebido maior que o saldo pendente.")

    conta_receber.valor_recebido += valor
    conta_receber.recebido_por = usuario
    conta_receber.forma_recebimento = forma_recebimento or conta_receber.forma_recebimento
    if conta_bancaria is not None:
        conta_receber.conta_bancaria = conta_bancaria
    conta_receber.atualizar_status_por_saldo()
    conta_receber.save(
        update_fields=[
            "valor_recebido",
            "recebido_por",
            "forma_recebimento",
            "conta_bancaria",
            "status",
            "data_recebimento",
            "atualizado_em",
        ]
    )

    if conta_receber.conta_bancaria:
        MovimentacaoFinanceira.objects.create(
            empresa=conta_receber.empresa,
            tipo=TipoMovimentacao.ENTRADA,
            descricao=conta_receber.descricao,
            data_movimento=timezone.localdate(),
            data_competencia=conta_receber.data_emissao,
            valor=valor,
            conta_bancaria=conta_receber.conta_bancaria,
            centro_custo=conta_receber.centro_custo,
            plano_conta=conta_receber.plano_conta,
            origem_modelo="ContaReceber",
            origem_id=str(conta_receber.pk),
        )

    registrar_evento(
        tipo_evento=TipoEvento.BAIXA,
        usuario=usuario,
        registro=conta_receber,
        modulo="financeiro",
        tela="contas_receber",
        acao="registrar_recebimento",
        valor_anterior={"saldo_pendente": str(saldo_anterior)},
        valor_novo={"valor_recebido": str(valor), "saldo_pendente": str(conta_receber.saldo_pendente)},
        nivel_risco=NivelRisco.MEDIO,
    )
    return conta_receber


@transaction.atomic
def solicitar_aprovacao_pagamento(*, conta_pagar, usuario, justificativa=""):
    conta_pagar = ContaPagar.objects.select_for_update().get(pk=conta_pagar.pk)
    if conta_pagar.status in {StatusContaPagar.PAGO, StatusContaPagar.CANCELADO}:
        raise BaixaInvalida("Conta paga ou cancelada nao pode entrar em aprovacao.")
    aprovacao, _ = AprovacaoPagamento.objects.get_or_create(
        conta_pagar=conta_pagar,
        status=StatusAprovacao.PENDENTE,
        defaults={"solicitante": usuario, "justificativa": justificativa},
    )
    conta_pagar.status = StatusContaPagar.EM_APROVACAO
    conta_pagar.save(update_fields=["status", "atualizado_em"])
    registrar_evento(
        tipo_evento=TipoEvento.ALERTA_SISTEMA,
        usuario=usuario,
        registro=conta_pagar,
        modulo="financeiro",
        tela="contas_pagar",
        acao="solicitar_aprovacao",
        valor_novo={"aprovacao_id": aprovacao.pk, "justificativa": justificativa},
        nivel_risco=NivelRisco.MEDIO,
    )
    return aprovacao


@transaction.atomic
def decidir_aprovacao_pagamento(*, aprovacao, usuario, aprovado, justificativa=""):
    aprovacao = AprovacaoPagamento.objects.select_for_update().select_related("conta_pagar").get(pk=aprovacao.pk)
    if aprovacao.status != StatusAprovacao.PENDENTE:
        raise BaixaInvalida("Aprovacao ja foi decidida.")

    aprovacao.aprovador = usuario
    aprovacao.status = StatusAprovacao.APROVADO if aprovado else StatusAprovacao.REPROVADO
    aprovacao.justificativa = justificativa or aprovacao.justificativa
    aprovacao.decidido_em = timezone.now()
    aprovacao.save(update_fields=["aprovador", "status", "justificativa", "decidido_em", "atualizado_em"])

    conta = aprovacao.conta_pagar
    conta.status = StatusContaPagar.AGENDADO if aprovado else StatusContaPagar.REPROVADO
    conta.save(update_fields=["status", "atualizado_em"])

    registrar_evento(
        tipo_evento=TipoEvento.APROVACAO if aprovado else TipoEvento.REPROVACAO,
        usuario=usuario,
        registro=conta,
        modulo="financeiro",
        tela="aprovacoes_pagamento",
        acao="aprovar" if aprovado else "reprovar",
        valor_novo={"aprovacao_id": aprovacao.pk, "justificativa": justificativa},
        nivel_risco=NivelRisco.ALTO,
    )
    return aprovacao


@transaction.atomic
def cancelar_conta_pagar(*, conta_pagar, usuario, justificativa):
    conta_pagar = ContaPagar.objects.select_for_update().get(pk=conta_pagar.pk)
    if conta_pagar.status == StatusContaPagar.PAGO:
        raise BaixaInvalida("Conta paga nao pode ser cancelada.")
    status_anterior = conta_pagar.status
    conta_pagar.status = StatusContaPagar.CANCELADO
    conta_pagar.observacao = f"{conta_pagar.observacao}\nCancelamento: {justificativa}".strip()
    conta_pagar.save(update_fields=["status", "observacao", "atualizado_em"])
    registrar_evento(
        tipo_evento=TipoEvento.ALTERACAO,
        usuario=usuario,
        registro=conta_pagar,
        modulo="financeiro",
        tela="contas_pagar",
        acao="cancelar",
        valor_anterior={"status": status_anterior},
        valor_novo={"status": conta_pagar.status, "justificativa": justificativa},
        nivel_risco=NivelRisco.ALTO,
    )
    return conta_pagar


@transaction.atomic
def cancelar_conta_receber(*, conta_receber, usuario, justificativa):
    conta_receber = ContaReceber.objects.select_for_update().get(pk=conta_receber.pk)
    if conta_receber.status == StatusContaReceber.RECEBIDO:
        raise BaixaInvalida("Conta recebida nao pode ser cancelada.")
    status_anterior = conta_receber.status
    conta_receber.status = StatusContaReceber.CANCELADO
    conta_receber.observacao = f"{conta_receber.observacao}\nCancelamento: {justificativa}".strip()
    conta_receber.save(update_fields=["status", "observacao", "atualizado_em"])
    registrar_evento(
        tipo_evento=TipoEvento.ALTERACAO,
        usuario=usuario,
        registro=conta_receber,
        modulo="financeiro",
        tela="contas_receber",
        acao="cancelar",
        valor_anterior={"status": status_anterior},
        valor_novo={"status": conta_receber.status, "justificativa": justificativa},
        nivel_risco=NivelRisco.ALTO,
    )
    return conta_receber


@transaction.atomic
def renegociar_conta_receber(*, conta_receber, usuario, dados):
    conta_receber = ContaReceber.objects.select_for_update().get(pk=conta_receber.pk)
    if conta_receber.status in {StatusContaReceber.RECEBIDO, StatusContaReceber.CANCELADO}:
        raise BaixaInvalida("Status atual nao permite renegociacao.")
    conta_receber.status = StatusContaReceber.RENEGOCIADO
    conta_receber.renegociado_em = timezone.now()
    conta_receber.renegociado_por = usuario
    conta_receber.save(update_fields=["status", "renegociado_em", "renegociado_por", "atualizado_em"])

    nova = ContaReceber.objects.create(
        empresa=conta_receber.empresa,
        cliente=conta_receber.cliente,
        contrato=conta_receber.contrato,
        parcela=conta_receber.parcela,
        descricao=f"Renegociacao - {conta_receber.descricao}",
        data_emissao=timezone.localdate(),
        data_vencimento=dados["nova_data_vencimento"],
        valor_original=dados["valor_original"],
        juros=dados.get("juros", Decimal("0.00")),
        multa=dados.get("multa", Decimal("0.00")),
        desconto=dados.get("desconto", Decimal("0.00")),
        honorarios=dados.get("honorarios", Decimal("0.00")),
        centro_custo=conta_receber.centro_custo,
        plano_conta=conta_receber.plano_conta,
        conta_bancaria=conta_receber.conta_bancaria,
        responsavel=usuario,
        observacao=dados.get("observacao", ""),
        conta_original=conta_receber,
    )
    registrar_evento(
        tipo_evento=TipoEvento.ALTERACAO,
        usuario=usuario,
        registro=conta_receber,
        modulo="financeiro",
        tela="contas_receber",
        acao="renegociar",
        valor_novo={"nova_conta_id": nova.pk},
        nivel_risco=NivelRisco.ALTO,
    )
    return nova


def resumo_fluxo_caixa(*, empresa, data_inicio, data_fim):
    contas_pagar = ContaPagar.objects.filter(
        empresa=empresa,
        excluido_logicamente=False,
        data_vencimento__range=(data_inicio, data_fim),
    ).exclude(status__in=[StatusContaPagar.PAGO, StatusContaPagar.CANCELADO])

    contas_receber = ContaReceber.objects.filter(
        empresa=empresa,
        excluido_logicamente=False,
        data_vencimento__range=(data_inicio, data_fim),
    ).exclude(status__in=[StatusContaReceber.RECEBIDO, StatusContaReceber.CANCELADO])

    entradas_realizadas = MovimentacaoFinanceira.objects.filter(
        empresa=empresa,
        tipo=TipoMovimentacao.ENTRADA,
        data_movimento__range=(data_inicio, data_fim),
    ).aggregate(total=Sum("valor"))["total"] or Decimal("0.00")

    saidas_realizadas = MovimentacaoFinanceira.objects.filter(
        empresa=empresa,
        tipo=TipoMovimentacao.SAIDA,
        data_movimento__range=(data_inicio, data_fim),
    ).aggregate(total=Sum("valor"))["total"] or Decimal("0.00")

    total_a_pagar = sum((conta.saldo_pendente for conta in contas_pagar), Decimal("0.00"))
    total_a_receber = sum((conta.saldo_pendente for conta in contas_receber), Decimal("0.00"))

    vencidas = contas_receber.filter(Q(status=StatusContaReceber.VENCIDO) | Q(data_vencimento__lt=timezone.localdate()))

    return {
        "total_a_pagar": total_a_pagar,
        "total_a_receber": total_a_receber,
        "entradas_realizadas": entradas_realizadas,
        "saidas_realizadas": saidas_realizadas,
        "saldo_previsto": total_a_receber - total_a_pagar,
        "saldo_realizado": entradas_realizadas - saidas_realizadas,
        "inadimplencia": sum((conta.saldo_pendente for conta in vencidas), Decimal("0.00")),
    }


def dashboard_financeiro(*, empresa, data_inicio=None, data_fim=None):
    hoje = timezone.localdate()
    data_inicio = data_inicio or hoje.replace(day=1)
    data_fim = data_fim or hoje
    fluxo = resumo_fluxo_caixa(empresa=empresa, data_inicio=data_inicio, data_fim=data_fim)

    pagar_hoje = ContaPagar.objects.filter(
        empresa=empresa,
        excluido_logicamente=False,
        data_vencimento=hoje,
    ).exclude(status__in=[StatusContaPagar.PAGO, StatusContaPagar.CANCELADO])
    receber_hoje = ContaReceber.objects.filter(
        empresa=empresa,
        excluido_logicamente=False,
        data_vencimento=hoje,
    ).exclude(status__in=[StatusContaReceber.RECEBIDO, StatusContaReceber.CANCELADO])

    receitas_mes = MovimentacaoFinanceira.objects.filter(
        empresa=empresa,
        tipo=TipoMovimentacao.ENTRADA,
        data_movimento__range=(data_inicio, data_fim),
    ).aggregate(total=Sum("valor"))["total"] or Decimal("0.00")
    despesas_mes = MovimentacaoFinanceira.objects.filter(
        empresa=empresa,
        tipo=TipoMovimentacao.SAIDA,
        data_movimento__range=(data_inicio, data_fim),
    ).aggregate(total=Sum("valor"))["total"] or Decimal("0.00")

    return {
        **fluxo,
        "contas_pagar_hoje": sum((conta.saldo_pendente for conta in pagar_hoje), Decimal("0.00")),
        "contas_receber_hoje": sum((conta.saldo_pendente for conta in receber_hoje), Decimal("0.00")),
        "receita_periodo": receitas_mes,
        "despesa_periodo": despesas_mes,
        "resultado_periodo": receitas_mes - despesas_mes,
        "titulos_pagar_abertos": ContaPagar.objects.filter(empresa=empresa, excluido_logicamente=False).exclude(
            status__in=[StatusContaPagar.PAGO, StatusContaPagar.CANCELADO]
        ).count(),
        "titulos_receber_abertos": ContaReceber.objects.filter(empresa=empresa, excluido_logicamente=False).exclude(
            status__in=[StatusContaReceber.RECEBIDO, StatusContaReceber.CANCELADO]
        ).count(),
    }


def dre_gerencial(*, empresa, data_inicio, data_fim):
    movimentos = MovimentacaoFinanceira.objects.filter(
        empresa=empresa,
        data_movimento__range=(data_inicio, data_fim),
    ).select_related("centro_custo", "plano_conta")

    categorias = _apurar_dre(movimentos)
    receita_bruta = categorias["receita_bruta"]
    deducoes = categorias["deducoes"]
    receita_liquida = receita_bruta - deducoes
    custos_variaveis = categorias["custos_variaveis"]
    margem_contribuicao = receita_liquida - custos_variaveis
    despesas_operacionais = categorias["despesas_operacionais"]
    resultado_operacional = margem_contribuicao - despesas_operacionais
    investimentos_outros = categorias["investimentos"] + categorias["outras_saidas"]
    lucro_prejuizo = resultado_operacional - investimentos_outros

    return {
        "receita_bruta": receita_bruta,
        "deducoes": deducoes,
        "receita_liquida": receita_liquida,
        "custos_variaveis": custos_variaveis,
        "margem_contribuicao": margem_contribuicao,
        "despesas_operacionais": despesas_operacionais,
        "investimentos_outros": investimentos_outros,
        "resultado_operacional": resultado_operacional,
        "resultado_financeiro": lucro_prejuizo,
        "lucro_prejuizo": lucro_prejuizo,
        "linhas": [
            _linha_dre("Receita bruta", receita_bruta, "+", "receita"),
            _linha_dre("Deducoes, impostos, taxas e comissoes", deducoes, "-", "deducao"),
            _linha_dre("Receita liquida", receita_liquida, "=", "resultado"),
            _linha_dre("Custos variaveis", custos_variaveis, "-", "custo"),
            _linha_dre("Margem de contribuicao", margem_contribuicao, "=", "resultado"),
            _linha_dre("Despesas operacionais", despesas_operacionais, "-", "despesa"),
            _linha_dre("Resultado operacional", resultado_operacional, "=", "resultado"),
            _linha_dre("Investimentos e outras saidas", investimentos_outros, "-", "investimento"),
            _linha_dre("Lucro / prejuizo", lucro_prejuizo, "=", "resultado"),
        ],
        "centros_custo": _dre_por_centro_custo(empresa=empresa, movimentos=movimentos),
        "planos_contas": _dre_por_plano_conta(empresa=empresa, movimentos=movimentos),
    }


def _apurar_dre(movimentos):
    totais = {
        "receita_bruta": Decimal("0.00"),
        "deducoes": Decimal("0.00"),
        "custos_variaveis": Decimal("0.00"),
        "despesas_operacionais": Decimal("0.00"),
        "investimentos": Decimal("0.00"),
        "outras_saidas": Decimal("0.00"),
    }
    for movimento in movimentos:
        valor = movimento.valor or Decimal("0.00")
        tipo_plano = getattr(movimento.plano_conta, "tipo", "")
        if movimento.tipo == TipoMovimentacao.ENTRADA:
            totais["receita_bruta"] += valor
        elif tipo_plano in {TipoPlanoConta.IMPOSTO, TipoPlanoConta.TAXA, TipoPlanoConta.COMISSAO, TipoPlanoConta.REPASSE}:
            totais["deducoes"] += valor
        elif tipo_plano == TipoPlanoConta.CUSTO:
            totais["custos_variaveis"] += valor
        elif tipo_plano == TipoPlanoConta.DESPESA:
            totais["despesas_operacionais"] += valor
        elif tipo_plano == TipoPlanoConta.INVESTIMENTO:
            totais["investimentos"] += valor
        else:
            totais["outras_saidas"] += valor
    return totais


def _linha_dre(label, valor, operador, grupo):
    return {
        "label": label,
        "valor": valor,
        "operador": operador,
        "grupo": grupo,
    }


def _dre_por_centro_custo(*, empresa, movimentos):
    centros = list(CentroCusto.objects.filter(empresa=empresa).order_by("codigo", "nome"))
    acumulado = {
        centro.pk: {
            "id": centro.pk,
            "codigo": centro.codigo,
            "nome": centro.nome,
            "entradas": Decimal("0.00"),
            "deducoes": Decimal("0.00"),
            "custos": Decimal("0.00"),
            "despesas": Decimal("0.00"),
            "investimentos_outros": Decimal("0.00"),
            "saidas": Decimal("0.00"),
            "resultado": Decimal("0.00"),
            "transacoes": 0,
        }
        for centro in centros
    }
    sem_centro = {
        "id": None,
        "codigo": "SEM",
        "nome": "Sem centro de custo",
        "entradas": Decimal("0.00"),
        "deducoes": Decimal("0.00"),
        "custos": Decimal("0.00"),
        "despesas": Decimal("0.00"),
        "investimentos_outros": Decimal("0.00"),
        "saidas": Decimal("0.00"),
        "resultado": Decimal("0.00"),
        "transacoes": 0,
    }

    for movimento in movimentos:
        row = acumulado.get(movimento.centro_custo_id) if movimento.centro_custo_id else sem_centro
        if row is None:
            row = sem_centro
        _somar_linha_dre(row, movimento)

    rows = list(acumulado.values())
    if sem_centro["transacoes"]:
        rows.append(sem_centro)
    for row in rows:
        row["resultado"] = row["entradas"] - row["saidas"]
    return rows


def _dre_por_plano_conta(*, empresa, movimentos):
    planos = list(PlanoConta.objects.filter(empresa=empresa).order_by("codigo", "nome"))
    acumulado = {
        plano.pk: {
            "id": plano.pk,
            "codigo": plano.codigo,
            "nome": plano.nome,
            "tipo": plano.tipo,
            "entradas": Decimal("0.00"),
            "saidas": Decimal("0.00"),
            "resultado": Decimal("0.00"),
            "transacoes": 0,
        }
        for plano in planos
    }
    sem_plano = {
        "id": None,
        "codigo": "SEM",
        "nome": "Sem plano de contas",
        "tipo": "",
        "entradas": Decimal("0.00"),
        "saidas": Decimal("0.00"),
        "resultado": Decimal("0.00"),
        "transacoes": 0,
    }

    for movimento in movimentos:
        row = acumulado.get(movimento.plano_conta_id) if movimento.plano_conta_id else sem_plano
        if row is None:
            row = sem_plano
        valor = movimento.valor or Decimal("0.00")
        row["transacoes"] += 1
        if movimento.tipo == TipoMovimentacao.ENTRADA:
            row["entradas"] += valor
        else:
            row["saidas"] += valor

    rows = list(acumulado.values())
    if sem_plano["transacoes"]:
        rows.append(sem_plano)
    for row in rows:
        row["resultado"] = row["entradas"] - row["saidas"]
    return rows


def _somar_linha_dre(row, movimento):
    valor = movimento.valor or Decimal("0.00")
    tipo_plano = getattr(movimento.plano_conta, "tipo", "")
    row["transacoes"] += 1
    if movimento.tipo == TipoMovimentacao.ENTRADA:
        row["entradas"] += valor
    elif tipo_plano in {TipoPlanoConta.IMPOSTO, TipoPlanoConta.TAXA, TipoPlanoConta.COMISSAO, TipoPlanoConta.REPASSE}:
        row["deducoes"] += valor
        row["saidas"] += valor
    elif tipo_plano == TipoPlanoConta.CUSTO:
        row["custos"] += valor
        row["saidas"] += valor
    elif tipo_plano == TipoPlanoConta.DESPESA:
        row["despesas"] += valor
        row["saidas"] += valor
    else:
        row["investimentos_outros"] += valor
        row["saidas"] += valor


def importar_conciliacao_csv(*, empresa, conta_bancaria_id, arquivo, usuario=None):
    conta_bancaria = ContaBancaria.objects.get(pk=conta_bancaria_id, empresa=empresa)
    conteudo = arquivo.read()
    if isinstance(conteudo, bytes):
        conteudo = conteudo.decode("utf-8-sig")
    sample = conteudo[:1024]
    dialect = csv.Sniffer().sniff(sample, delimiters=",;")
    reader = csv.DictReader(io.StringIO(conteudo), dialect=dialect)
    criadas = []
    for linha in reader:
        data_raw = linha.get("data") or linha.get("data_movimento")
        valor_raw = (linha.get("valor") or "0").replace(".", "").replace(",", ".")
        historico = linha.get("historico") or linha.get("descricao") or ""
        documento = linha.get("documento") or ""
        conciliacao = ConciliacaoBancaria.objects.create(
            empresa=empresa,
            conta_bancaria=conta_bancaria,
            data_movimento=datetime.fromisoformat(data_raw).date(),
            valor=Decimal(valor_raw),
            historico=historico,
            documento=documento,
            status=StatusConciliacao.PENDENTE,
            metadados={"linha": linha},
        )
        criadas.append(conciliacao)
    registrar_evento(
        tipo_evento=TipoEvento.INTEGRACAO,
        usuario=usuario,
        empresa=empresa,
        modulo="financeiro",
        tela="conciliacoes",
        acao="importar_csv",
        valor_novo={"total_linhas": len(criadas)},
        nivel_risco=NivelRisco.MEDIO,
    )
    return criadas


def sugerir_conciliacoes(*, empresa):
    sugestoes = []
    pendentes = ConciliacaoBancaria.objects.filter(empresa=empresa, status=StatusConciliacao.PENDENTE)
    for item in pendentes:
        candidatos = MovimentacaoFinanceira.objects.filter(
            empresa=empresa,
            conta_bancaria=item.conta_bancaria,
            valor=abs(item.valor),
            data_movimento__range=(item.data_movimento - timedelta(days=3), item.data_movimento + timedelta(days=3)),
            conciliado=False,
        )
        candidato = candidatos.first()
        if candidato:
            item.movimentacao = candidato
            item.status = StatusConciliacao.SUGERIDA
            item.metadados = {**item.metadados, "score": "0.80", "motivo": "valor e data aproximados"}
            item.save(update_fields=["movimentacao", "status", "metadados", "atualizado_em"])
            sugestoes.append(item)
    return sugestoes


@transaction.atomic
def conciliar_movimentacao(*, conciliacao, movimentacao, usuario=None):
    conciliacao = ConciliacaoBancaria.objects.select_for_update().get(pk=conciliacao.pk)
    movimentacao = MovimentacaoFinanceira.objects.select_for_update().get(pk=movimentacao.pk, empresa=conciliacao.empresa)
    if movimentacao.conta_bancaria_id != conciliacao.conta_bancaria_id:
        raise BaixaInvalida("Movimentacao pertence a outra conta bancaria.")
    conciliacao.movimentacao = movimentacao
    conciliacao.status = StatusConciliacao.CONCILIADA
    conciliacao.save(update_fields=["movimentacao", "status", "atualizado_em"])
    movimentacao.conciliado = True
    movimentacao.save(update_fields=["conciliado", "atualizado_em"])
    registrar_evento(
        tipo_evento=TipoEvento.INTEGRACAO,
        usuario=usuario,
        registro=conciliacao,
        modulo="financeiro",
        tela="conciliacoes",
        acao="conciliar",
        valor_novo={"movimentacao_id": movimentacao.pk},
        nivel_risco=NivelRisco.MEDIO,
    )
    return conciliacao
