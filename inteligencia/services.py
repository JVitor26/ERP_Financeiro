from datetime import timedelta
from decimal import Decimal

from django.db.models import Avg, Count
from django.utils import timezone

from core.models import NivelRisco, TipoEvento
from core.services import registrar_evento
from financeiro.models import ContaPagar, ContaReceber

from .models import AlertaIA, Anomalia, PrevisaoIA, StatusAnaliseIA, TipoAnomalia


def _json_seguro(dados):
    return {
        chave: str(valor) if isinstance(valor, Decimal) or hasattr(valor, "isoformat") else valor
        for chave, valor in dados.items()
    }


def detectar_pagamentos_duplicados(*, empresa):
    grupos = (
        ContaPagar.objects.filter(empresa=empresa, excluido_logicamente=False)
        .values("fornecedor_id", "valor_original", "data_vencimento", "numero_documento")
        .annotate(total=Count("id"))
        .filter(total__gt=1)
    )

    anomalias = []
    for grupo in grupos:
        evidencia = _json_seguro(grupo)
        anomalia = Anomalia.objects.create(
            empresa=empresa,
            tipo=TipoAnomalia.PAGAMENTO_DUPLICADO,
            descricao="Possivel pagamento duplicado por fornecedor, valor, vencimento e documento.",
            nivel_risco=NivelRisco.ALTO,
            evidencia=evidencia,
        )
        AlertaIA.objects.create(
            empresa=empresa,
            titulo="Possivel pagamento duplicado",
            mensagem=anomalia.descricao,
            nivel_risco=NivelRisco.ALTO,
            origem_modelo="Anomalia",
            origem_id=str(anomalia.pk),
        )
        registrar_evento(
            tipo_evento=TipoEvento.ALERTA_IA,
            empresa=empresa,
            modulo="inteligencia",
            tela="anomalias",
            acao="detectar_pagamento_duplicado",
            registro=anomalia,
            nivel_risco=NivelRisco.ALTO,
            metadados=evidencia,
        )
        anomalias.append(anomalia)
    return anomalias


def detectar_fornecedores_fora_do_padrao(*, empresa, fator=Decimal("1.47")):
    media_por_fornecedor = (
        ContaPagar.objects.filter(empresa=empresa, excluido_logicamente=False)
        .values("fornecedor_id")
        .annotate(media=Avg("valor_original"), total=Count("id"))
        .filter(total__gte=3)
    )

    anomalias = []
    for linha in media_por_fornecedor:
        fornecedor_id = linha["fornecedor_id"]
        media = linha["media"] or Decimal("0.00")
        limite = media * fator
        recentes = ContaPagar.objects.filter(
            empresa=empresa,
            fornecedor_id=fornecedor_id,
            excluido_logicamente=False,
            valor_original__gt=limite,
        )
        for conta in recentes:
            evidencia = {"media": str(media), "valor": str(conta.valor_original), "limite": str(limite)}
            anomalia = Anomalia.objects.create(
                empresa=empresa,
                tipo=TipoAnomalia.VALOR_FORA_PADRAO,
                descricao="Conta a pagar acima do padrao historico do fornecedor.",
                nivel_risco=NivelRisco.MEDIO,
                entidade_modelo="ContaPagar",
                entidade_id=str(conta.pk),
                evidencia=evidencia,
            )
            AlertaIA.objects.create(
                empresa=empresa,
                titulo="Pagamento fora do padrao",
                mensagem=anomalia.descricao,
                nivel_risco=NivelRisco.MEDIO,
                origem_modelo="Anomalia",
                origem_id=str(anomalia.pk),
                score=Decimal("0.70"),
            )
            anomalias.append(anomalia)
    return anomalias


def gerar_previsao_baseline_caixa(*, empresa, horizonte_dias=60):
    hoje = timezone.localdate()
    fim = hoje + timedelta(days=horizonte_dias)

    total_receber = sum(
        (conta.saldo_pendente for conta in ContaReceber.objects.filter(empresa=empresa, data_vencimento__range=(hoje, fim))),
        Decimal("0.00"),
    )
    total_pagar = sum(
        (conta.saldo_pendente for conta in ContaPagar.objects.filter(empresa=empresa, data_vencimento__range=(hoje, fim))),
        Decimal("0.00"),
    )

    return PrevisaoIA.objects.create(
        empresa=empresa,
        nome=f"Previsao de caixa {horizonte_dias} dias",
        data_referencia=hoje,
        horizonte_dias=horizonte_dias,
        metrica="saldo_previsto",
        valor_previsto=total_receber - total_pagar,
        confianca=Decimal("0.50"),
        modelo="baseline_fluxo_caixa",
        parametros={"total_receber": str(total_receber), "total_pagar": str(total_pagar)},
    )


def executar_varredura_ia(*, empresa):
    duplicidades = detectar_pagamentos_duplicados(empresa=empresa)
    fora_padrao = detectar_fornecedores_fora_do_padrao(empresa=empresa)
    previsao = gerar_previsao_baseline_caixa(empresa=empresa)
    return {
        "duplicidades": duplicidades,
        "fora_padrao": fora_padrao,
        "previsao": previsao,
    }


def registrar_feedback_analise(*, analise, usuario, status, observacao=""):
    analise.status = status
    analise.evidencia = {
        **analise.evidencia,
        "feedback": {
            "usuario_id": usuario.id if usuario else None,
            "observacao": observacao,
            "registrado_em": timezone.now().isoformat(),
        },
    }
    analise.save(update_fields=["status", "evidencia", "atualizado_em"])
    registrar_evento(
        tipo_evento=TipoEvento.ALTERACAO,
        usuario=usuario,
        empresa=analise.empresa,
        modulo="inteligencia",
        tela="anomalias",
        acao="feedback",
        registro=analise,
        valor_novo={"status": status, "observacao": observacao},
        nivel_risco=NivelRisco.MEDIO if status != StatusAnaliseIA.CONFIRMADO else NivelRisco.ALTO,
    )
    return analise
