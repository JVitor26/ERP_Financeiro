from decimal import Decimal, ROUND_HALF_UP
from datetime import date

from django.db import transaction
from django.db.models import Sum, Q
from django.utils import timezone

from financeiro.models import ContaPagar, Fornecedor, StatusContaPagar

from .models import (
    ConfiguracaoFiscalEmpresa,
    ConfiguracaoImpostoPorServico,
    ImpostoApurado,
    NotaFiscal,
    ObrigacaoFiscal,
    RegimeTributario,
    StatusNotaFiscal,
    TipoImposto,
)


def _arredondar(valor):
    return Decimal(valor).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def calcular_impostos_nota(nota_fiscal):
    """
    Calcula ISS, PIS, COFINS (e INSS se retencao ativa) para a nota fiscal
    com base na ConfiguracaoFiscalEmpresa e nas aliquotas por servico.
    Retorna um dict com os valores calculados e atualiza a nota.
    """
    try:
        config = ConfiguracaoFiscalEmpresa.objects.get(empresa=nota_fiscal.empresa)
    except ConfiguracaoFiscalEmpresa.DoesNotExist:
        return {
            "erro": "Configuracao fiscal da empresa nao encontrada.",
            "valor_iss": Decimal("0.00"),
            "valor_pis": Decimal("0.00"),
            "valor_cofins": Decimal("0.00"),
            "valor_inss": Decimal("0.00"),
        }

    valor_iss_total = Decimal("0.00")
    valor_pis_total = Decimal("0.00")
    valor_cofins_total = Decimal("0.00")
    valor_inss_total = Decimal("0.00")
    valor_servicos_total = Decimal("0.00")

    for item in nota_fiscal.itens.select_related("servico").all():
        valor_item = _arredondar(item.valor_total)
        valor_servicos_total += valor_item

        # Aliquota ISS: prioriza configuracao por servico, senao usa config da empresa
        aliquota_iss = config.aliquota_iss
        aliquota_pis = config.aliquota_pis
        aliquota_cofins = config.aliquota_cofins

        if item.servico:
            configs_servico = ConfiguracaoImpostoPorServico.objects.filter(
                empresa=nota_fiscal.empresa, servico=item.servico
            )
            for cs in configs_servico:
                if cs.tipo_imposto == TipoImposto.ISS:
                    aliquota_iss = cs.aliquota
                elif cs.tipo_imposto == TipoImposto.PIS:
                    aliquota_pis = cs.aliquota
                elif cs.tipo_imposto == TipoImposto.COFINS:
                    aliquota_cofins = cs.aliquota

        iss_item = _arredondar(valor_item * aliquota_iss / Decimal("100"))
        pis_item = _arredondar(valor_item * aliquota_pis / Decimal("100"))
        cofins_item = _arredondar(valor_item * aliquota_cofins / Decimal("100"))

        valor_iss_total += iss_item
        valor_pis_total += pis_item
        valor_cofins_total += cofins_item

        # Atualiza aliquota e valor ISS no item
        item.aliquota_iss = aliquota_iss
        item.valor_iss = iss_item
        item.save(update_fields=["aliquota_iss", "valor_iss"])

    if config.retencao_inss:
        valor_inss_total = _arredondar(
            valor_servicos_total * config.aliquota_inss / Decimal("100")
        )

    resultado = {
        "nota_fiscal_id": nota_fiscal.pk,
        "valor_iss": valor_iss_total,
        "valor_pis": valor_pis_total,
        "valor_cofins": valor_cofins_total,
        "valor_inss": valor_inss_total,
    }

    nota_fiscal.valor_servicos = valor_servicos_total
    nota_fiscal.valor_iss = valor_iss_total
    nota_fiscal.valor_pis = valor_pis_total
    nota_fiscal.valor_cofins = valor_cofins_total
    nota_fiscal.valor_inss = valor_inss_total
    nota_fiscal.save(
        update_fields=[
            "valor_servicos",
            "valor_iss",
            "valor_pis",
            "valor_cofins",
            "valor_inss",
        ]
    )

    return resultado


@transaction.atomic
def apurar_impostos_periodo(empresa, ano, mes):
    """
    Agrupa as notas fiscais autorizadas do periodo (ano/mes) e calcula
    os impostos totais. Cria ou atualiza ImpostoApurado para cada tipo.
    Gera ContaPagar para impostos com valor_a_pagar > 0.
    Retorna lista de ImpostoApurado criados/atualizados.
    """
    try:
        config = ConfiguracaoFiscalEmpresa.objects.get(empresa=empresa)
    except ConfiguracaoFiscalEmpresa.DoesNotExist:
        return []

    notas = NotaFiscal.objects.filter(
        empresa=empresa,
        data_emissao__year=ano,
        data_emissao__month=mes,
        status__in=[StatusNotaFiscal.AUTORIZADA, StatusNotaFiscal.EMITIDA],
    )

    totais = notas.aggregate(
        total_servicos=Sum("valor_servicos"),
        total_iss=Sum("valor_iss"),
        total_pis=Sum("valor_pis"),
        total_cofins=Sum("valor_cofins"),
        total_irrf=Sum("valor_irrf"),
        total_csll=Sum("valor_csll"),
        total_inss=Sum("valor_inss"),
    )

    def _v(val):
        return val or Decimal("0.00")

    impostos_dados = []

    # ISS
    base_iss = _v(totais["total_servicos"])
    if base_iss > 0:
        impostos_dados.append(
            {
                "tipo": TipoImposto.ISS,
                "base": base_iss,
                "aliquota": config.aliquota_iss,
                "apurado": _v(totais["total_iss"]),
                "retido": Decimal("0.00"),
            }
        )

    # PIS
    base_pis = _v(totais["total_servicos"])
    if base_pis > 0:
        impostos_dados.append(
            {
                "tipo": TipoImposto.PIS,
                "base": base_pis,
                "aliquota": config.aliquota_pis,
                "apurado": _v(totais["total_pis"]),
                "retido": Decimal("0.00"),
            }
        )

    # COFINS
    base_cofins = _v(totais["total_servicos"])
    if base_cofins > 0:
        impostos_dados.append(
            {
                "tipo": TipoImposto.COFINS,
                "base": base_cofins,
                "aliquota": config.aliquota_cofins,
                "apurado": _v(totais["total_cofins"]),
                "retido": Decimal("0.00"),
            }
        )

    # IRPJ / IRRF (somente lucro presumido/real)
    if config.regime_tributario in [RegimeTributario.LUCRO_PRESUMIDO, RegimeTributario.LUCRO_REAL]:
        base_irpj = _v(totais["total_servicos"])
        if base_irpj > 0:
            impostos_dados.append(
                {
                    "tipo": TipoImposto.IRPJ,
                    "base": base_irpj,
                    "aliquota": config.aliquota_irpj,
                    "apurado": _arredondar(base_irpj * config.aliquota_irpj / Decimal("100")),
                    "retido": _v(totais["total_irrf"]),
                }
            )

        base_csll = _v(totais["total_servicos"])
        if base_csll > 0:
            impostos_dados.append(
                {
                    "tipo": TipoImposto.CSLL,
                    "base": base_csll,
                    "aliquota": config.aliquota_csll,
                    "apurado": _arredondar(base_csll * config.aliquota_csll / Decimal("100")),
                    "retido": _v(totais["total_csll"]),
                }
            )

    # INSS retido
    if config.retencao_inss:
        base_inss = _v(totais["total_servicos"])
        if base_inss > 0:
            impostos_dados.append(
                {
                    "tipo": TipoImposto.INSS_RETIDO,
                    "base": base_inss,
                    "aliquota": config.aliquota_inss,
                    "apurado": _v(totais["total_inss"]),
                    "retido": Decimal("0.00"),
                }
            )

    # Vencimento padrao: ultimo dia util do mes seguinte (simplificado)
    if mes == 12:
        vencimento = date(ano + 1, 1, 20)
    else:
        vencimento = date(ano, mes + 1, 20)

    resultado = []

    # Busca ou cria um fornecedor "Receita Federal" para CP de impostos
    fornecedor_rf, _ = Fornecedor.objects.get_or_create(
        empresa=empresa,
        nome="Governo / Impostos",
        defaults={"tipo_pessoa": "juridica", "ativo": True},
    )

    for dado in impostos_dados:
        valor_a_pagar = _arredondar(max(dado["apurado"] - dado["retido"], Decimal("0.00")))

        imposto, created = ImpostoApurado.objects.update_or_create(
            empresa=empresa,
            ano=ano,
            mes=mes,
            tipo_imposto=dado["tipo"],
            defaults={
                "base_calculo": dado["base"],
                "aliquota": dado["aliquota"],
                "valor_apurado": dado["apurado"],
                "valor_retido": dado["retido"],
                "valor_a_pagar": valor_a_pagar,
                "data_vencimento": vencimento,
            },
        )

        # Gera ContaPagar para imposto a pagar
        if valor_a_pagar > 0 and imposto.conta_pagar_id is None:
            tipo_display = dict(TipoImposto.choices).get(dado["tipo"], dado["tipo"])
            cp = ContaPagar.objects.create(
                empresa=empresa,
                fornecedor=fornecedor_rf,
                descricao=f"{tipo_display} {mes:02d}/{ano}",
                data_emissao=date(ano, mes, 1),
                data_vencimento=vencimento,
                valor_original=valor_a_pagar,
                status=StatusContaPagar.ABERTO,
            )
            imposto.conta_pagar = cp
            imposto.save(update_fields=["conta_pagar"])

        resultado.append(imposto)

    return resultado


@transaction.atomic
def gerar_obrigacoes_mes(empresa, ano, mes):
    """
    Cria ObrigacaoFiscal para o mes com base no regime tributario da empresa.
    Retorna a lista de obrigacoes criadas.
    """
    try:
        config = ConfiguracaoFiscalEmpresa.objects.get(empresa=empresa)
    except ConfiguracaoFiscalEmpresa.DoesNotExist:
        return []

    if mes == 12:
        proximo_mes = 1
        proximo_ano = ano + 1
    else:
        proximo_mes = mes + 1
        proximo_ano = ano

    obrigacoes_base = [
        {
            "descricao": "DAS - Simples Nacional",
            "tipo": "pagamento",
            "data_vencimento": date(proximo_ano, proximo_mes, 20),
            "regime": [RegimeTributario.SIMPLES_NACIONAL, RegimeTributario.MEI],
        },
        {
            "descricao": "DCTFWEB",
            "tipo": "declaracao",
            "data_vencimento": date(proximo_ano, proximo_mes, 15),
            "regime": [RegimeTributario.LUCRO_PRESUMIDO, RegimeTributario.LUCRO_REAL],
        },
        {
            "descricao": "PIS/COFINS",
            "tipo": "pagamento",
            "data_vencimento": date(proximo_ano, proximo_mes, 25),
            "regime": [RegimeTributario.LUCRO_PRESUMIDO, RegimeTributario.LUCRO_REAL],
        },
        {
            "descricao": "IRPJ/CSLL Estimativa",
            "tipo": "pagamento",
            "data_vencimento": date(proximo_ano, proximo_mes, 30),
            "regime": [RegimeTributario.LUCRO_REAL],
        },
        {
            "descricao": "ISS Municipal",
            "tipo": "pagamento",
            "data_vencimento": date(proximo_ano, proximo_mes, 10),
            "regime": [
                RegimeTributario.SIMPLES_NACIONAL,
                RegimeTributario.LUCRO_PRESUMIDO,
                RegimeTributario.LUCRO_REAL,
                RegimeTributario.MEI,
            ],
        },
    ]

    criadas = []
    for ob in obrigacoes_base:
        if config.regime_tributario not in ob["regime"]:
            continue
        obrigacao, created = ObrigacaoFiscal.objects.get_or_create(
            empresa=empresa,
            descricao=ob["descricao"],
            competencia_ano=ano,
            competencia_mes=mes,
            defaults={
                "tipo": ob["tipo"],
                "data_vencimento": ob["data_vencimento"],
                "status": "pendente",
            },
        )
        if created:
            criadas.append(obrigacao)

    return criadas
