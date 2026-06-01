from decimal import Decimal

from django.db.models import Q, Sum
from django.utils import timezone

from .models import (
    CompetenciaContabil,
    ContaContabil,
    LancamentoContabil,
    NaturezaConta,
    PartidaContabil,
    TipoLancamentoContabil,
)


def calcular_saldo_conta(conta_contabil, data_ini, data_fim):
    """Retorna débitos, créditos e saldo líquido de uma conta num período."""
    partidas = PartidaContabil.objects.filter(
        conta=conta_contabil,
        lancamento__excluido_logicamente=False,
        lancamento__data_lancamento__range=(data_ini, data_fim),
    )
    debitos = partidas.filter(tipo_partida="debito").aggregate(total=Sum("valor"))["total"] or Decimal("0.00")
    creditos = partidas.filter(tipo_partida="credito").aggregate(total=Sum("valor"))["total"] or Decimal("0.00")

    if conta_contabil.tipo_saldo == "devedora":
        saldo = debitos - creditos
    else:
        saldo = creditos - debitos

    return {"debitos": debitos, "creditos": creditos, "saldo": saldo}


def gerar_balancete(empresa, ano, mes):
    """Retorna lista de contas com saldos para o mês/ano informados."""
    from datetime import date
    import calendar

    data_ini = date(ano, mes, 1)
    data_fim = date(ano, mes, calendar.monthrange(ano, mes)[1])

    contas = ContaContabil.objects.filter(empresa=empresa, aceita_lancamento=True, ativo=True)
    resultado = []
    for conta in contas:
        saldos = calcular_saldo_conta(conta, data_ini, data_fim)
        if saldos["debitos"] or saldos["creditos"]:
            resultado.append(
                {
                    "codigo": conta.codigo,
                    "nome": conta.nome,
                    "natureza": conta.natureza,
                    **saldos,
                }
            )
    return resultado


def gerar_dre(empresa, ano, mes):
    """Retorna resumo de receitas, despesas, custos e resultado do período."""
    from datetime import date
    import calendar

    data_ini = date(ano, mes, 1)
    data_fim = date(ano, mes, calendar.monthrange(ano, mes)[1])

    receitas = Decimal("0.00")
    despesas = Decimal("0.00")
    custos = Decimal("0.00")

    contas = ContaContabil.objects.filter(empresa=empresa, aceita_lancamento=True, ativo=True)
    for conta in contas:
        saldos = calcular_saldo_conta(conta, data_ini, data_fim)
        if conta.natureza == NaturezaConta.RECEITA:
            receitas += saldos["saldo"]
        elif conta.natureza == NaturezaConta.DESPESA:
            despesas += saldos["saldo"]
        elif conta.natureza == NaturezaConta.CUSTO:
            custos += saldos["saldo"]

    resultado = receitas - despesas - custos
    return {
        "receitas": receitas,
        "despesas": despesas,
        "custos": custos,
        "resultado": resultado,
    }


def gerar_balanco_patrimonial(empresa, data_base):
    """Retorna ativo, passivo e PL consolidados até a data_base."""
    partidas_qs = PartidaContabil.objects.filter(
        conta__empresa=empresa,
        lancamento__excluido_logicamente=False,
        lancamento__data_lancamento__lte=data_base,
    )

    def soma_natureza(natureza):
        contas_ids = ContaContabil.objects.filter(
            empresa=empresa, natureza=natureza, aceita_lancamento=True
        ).values_list("id", flat=True)
        debitos = (
            partidas_qs.filter(conta_id__in=contas_ids, tipo_partida="debito").aggregate(t=Sum("valor"))["t"]
            or Decimal("0.00")
        )
        creditos = (
            partidas_qs.filter(conta_id__in=contas_ids, tipo_partida="credito").aggregate(t=Sum("valor"))["t"]
            or Decimal("0.00")
        )
        return debitos - creditos if natureza == NaturezaConta.ATIVO else creditos - debitos

    ativo = soma_natureza(NaturezaConta.ATIVO)
    passivo = soma_natureza(NaturezaConta.PASSIVO)
    patrimonio = soma_natureza(NaturezaConta.PATRIMONIO_LIQUIDO)

    return {"ativo": ativo, "passivo": passivo, "patrimonio_liquido": patrimonio}


def gerar_lancamento_automatico(empresa, usuario, historico, data, partidas_data, origem_modelo="", origem_id=""):
    """
    Cria um LancamentoContabil automático.
    partidas_data: lista de dicts com {conta_id, tipo_partida, valor}
    """
    from django.db import transaction

    with transaction.atomic():
        lancamento = LancamentoContabil.objects.create(
            empresa=empresa,
            data_lancamento=data,
            data_competencia=data,
            tipo=TipoLancamentoContabil.AUTOMATICO,
            historico=historico,
            origem_modelo=origem_modelo,
            origem_id=str(origem_id),
            usuario=usuario,
        )
        for p in partidas_data:
            PartidaContabil.objects.create(
                lancamento=lancamento,
                conta_id=p["conta_id"],
                tipo_partida=p["tipo_partida"],
                valor=p["valor"],
            )
    return lancamento
