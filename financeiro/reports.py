import csv
from io import BytesIO, StringIO

from django.http import HttpResponse
from openpyxl import Workbook
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from core.models import EventLog
from core.models import NivelRisco, TipoEvento
from core.services import registrar_evento

from .models import ContaPagar, ContaReceber, MovimentacaoFinanceira, RelatorioGerado


REPORT_CONFIG = {
    "contas_pagar": {
        "headers": ["id", "fornecedor", "descricao", "vencimento", "valor_total", "valor_pago", "status"],
        "queryset": lambda empresa, inicio, fim: ContaPagar.objects.filter(
            empresa=empresa,
            excluido_logicamente=False,
            data_vencimento__range=(inicio, fim),
        ).select_related("fornecedor"),
        "row": lambda obj: [
            obj.id,
            obj.fornecedor.nome,
            obj.descricao,
            obj.data_vencimento.isoformat(),
            obj.valor_total,
            obj.valor_pago,
            obj.status,
        ],
    },
    "contas_receber": {
        "headers": ["id", "cliente", "descricao", "vencimento", "valor_total", "valor_recebido", "status"],
        "queryset": lambda empresa, inicio, fim: ContaReceber.objects.filter(
            empresa=empresa,
            excluido_logicamente=False,
            data_vencimento__range=(inicio, fim),
        ).select_related("cliente"),
        "row": lambda obj: [
            obj.id,
            obj.cliente.nome,
            obj.descricao,
            obj.data_vencimento.isoformat(),
            obj.valor_total,
            obj.valor_recebido,
            obj.status,
        ],
    },
    "fluxo_caixa": {
        "headers": ["id", "tipo", "descricao", "data", "valor", "conta_bancaria", "conciliado"],
        "queryset": lambda empresa, inicio, fim: MovimentacaoFinanceira.objects.filter(
            empresa=empresa,
            data_movimento__range=(inicio, fim),
        ).select_related("conta_bancaria"),
        "row": lambda obj: [
            obj.id,
            obj.tipo,
            obj.descricao,
            obj.data_movimento.isoformat(),
            obj.valor,
            obj.conta_bancaria.numero,
            obj.conciliado,
        ],
    },
    "eventos": {
        "headers": ["id", "tipo", "modulo", "tela", "acao", "risco", "criado_em"],
        "queryset": lambda empresa, inicio, fim: EventLog.objects.filter(
            empresa=empresa,
            criado_em__date__range=(inicio, fim),
        ),
        "row": lambda obj: [
            obj.id,
            obj.tipo_evento,
            obj.modulo,
            obj.tela,
            obj.acao,
            obj.nivel_risco,
            obj.criado_em.isoformat(),
        ],
    },
}


def gerar_relatorio_response(*, empresa, usuario, tipo, formato, data_inicio, data_fim):
    if tipo not in REPORT_CONFIG:
        raise ValueError("Tipo de relatorio nao suportado.")
    config = REPORT_CONFIG[tipo]
    rows = [config["row"](obj) for obj in config["queryset"](empresa, data_inicio, data_fim)]
    headers = config["headers"]

    if formato == "csv":
        response = _csv_response(headers, rows, f"{tipo}.csv")
    elif formato == "xlsx":
        response = _xlsx_response(headers, rows, f"{tipo}.xlsx")
    elif formato == "pdf":
        response = _pdf_response(headers, rows, f"{tipo}.pdf", tipo)
    else:
        raise ValueError("Formato de relatorio nao suportado.")

    registrar_evento(
        tipo_evento=TipoEvento.EXPORTACAO,
        usuario=usuario,
        empresa=empresa,
        modulo="financeiro",
        tela="relatorios",
        acao=f"exportar_{tipo}_{formato}",
        valor_novo={"tipo": tipo, "formato": formato, "linhas": len(rows)},
        nivel_risco=NivelRisco.ALTO,
    )
    RelatorioGerado.objects.create(
        empresa=empresa,
        usuario=usuario,
        tipo=tipo,
        formato=formato,
        parametros={
            "data_inicio": data_inicio.isoformat(),
            "data_fim": data_fim.isoformat(),
            "linhas": len(rows),
        },
    )
    return response


def _csv_response(headers, rows, filename):
    output = StringIO()
    writer = csv.writer(output, delimiter=";")
    writer.writerow(headers)
    writer.writerows(rows)
    response = HttpResponse(output.getvalue(), content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _xlsx_response(headers, rows, filename):
    wb = Workbook()
    ws = wb.active
    ws.title = "Relatorio"
    ws.append(headers)
    for row in rows:
        ws.append(list(row))
    output = BytesIO()
    wb.save(output)
    response = HttpResponse(
        output.getvalue(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def _pdf_response(headers, rows, filename, titulo):
    output = BytesIO()
    pdf = canvas.Canvas(output, pagesize=A4)
    width, height = A4
    y = height - 40
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(40, y, f"Relatorio: {titulo}")
    y -= 25
    pdf.setFont("Helvetica", 8)
    pdf.drawString(40, y, " | ".join(headers))
    y -= 16
    for row in rows:
        if y < 40:
            pdf.showPage()
            y = height - 40
            pdf.setFont("Helvetica", 8)
        pdf.drawString(40, y, " | ".join(str(item) for item in row)[:150])
        y -= 14
    pdf.save()
    response = HttpResponse(output.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
