from .models import EventLog, NivelRisco, TipoEvento


def registrar_evento(
    *,
    tipo_evento,
    modulo,
    acao,
    usuario=None,
    empresa=None,
    tela="",
    registro=None,
    registro_modelo="",
    registro_id="",
    valor_anterior=None,
    valor_novo=None,
    ip=None,
    dispositivo="",
    origem="sistema",
    justificativa="",
    nivel_risco=NivelRisco.BAIXO,
    metadados=None,
):
    if registro is not None:
        registro_modelo = registro_modelo or registro.__class__.__name__
        registro_id = registro_id or str(registro.pk)
        empresa = empresa or getattr(registro, "empresa", None)

    return EventLog.objects.create(
        tipo_evento=tipo_evento,
        usuario=usuario,
        empresa=empresa,
        modulo=modulo,
        tela=tela,
        acao=acao,
        registro_modelo=registro_modelo,
        registro_id=registro_id,
        valor_anterior=valor_anterior,
        valor_novo=valor_novo,
        ip=ip,
        dispositivo=dispositivo,
        origem=origem,
        justificativa=justificativa,
        nivel_risco=nivel_risco,
        metadados=metadados or {},
    )


def registrar_criacao(modulo, registro, usuario=None, tela="", metadados=None):
    return registrar_evento(
        tipo_evento=TipoEvento.CRIACAO,
        modulo=modulo,
        tela=tela,
        acao="criar",
        usuario=usuario,
        registro=registro,
        valor_novo={"id": registro.pk},
        metadados=metadados,
    )
