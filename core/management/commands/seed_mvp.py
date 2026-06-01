from django.core.management.base import BaseCommand

from core.models import Modulo, Perfil, PerfilPermissao, Permissao


MODULOS = [
    ("core", "Motor central", "Empresas, usuarios, permissoes, auditoria e configuracoes."),
    ("financeiro", "Financeiro", "Contas a pagar, receber, fluxo de caixa, conciliacao e orcamento."),
    ("inteligencia", "Inteligencia", "Alertas, anomalias e previsoes financeiras."),
]

PERMISSOES = [
    ("core.usuarios.visualizar", "core", "usuarios", "visualizar", False),
    ("core.usuarios.editar", "core", "usuarios", "editar", True),
    ("core.auditoria.visualizar", "core", "auditoria", "visualizar", True),
    ("financeiro.contas_pagar.visualizar", "financeiro", "contas_pagar", "visualizar", False),
    ("financeiro.contas_pagar.editar", "financeiro", "contas_pagar", "editar", True),
    ("financeiro.contas_pagar.baixar", "financeiro", "contas_pagar", "baixar", True),
    ("financeiro.contas_pagar.aprovar", "financeiro", "contas_pagar", "aprovar", True),
    ("financeiro.contas_pagar.excluir", "financeiro", "contas_pagar", "excluir", True),
    ("financeiro.contas_receber.visualizar", "financeiro", "contas_receber", "visualizar", False),
    ("financeiro.contas_receber.editar", "financeiro", "contas_receber", "editar", True),
    ("financeiro.contas_receber.receber", "financeiro", "contas_receber", "receber", True),
    ("financeiro.contas_receber.excluir", "financeiro", "contas_receber", "excluir", True),
    ("financeiro.fluxo_caixa.visualizar", "financeiro", "fluxo_caixa", "visualizar", False),
    ("financeiro.relatorios.exportar", "financeiro", "relatorios", "exportar", True),
    ("inteligencia.alertas.visualizar", "inteligencia", "alertas", "visualizar", False),
    ("inteligencia.anomalias.gerar", "inteligencia", "anomalias", "gerar", True),
]

for tela in [
    "centros_custo",
    "plano_contas",
    "contas_bancarias",
    "clientes",
    "fornecedores",
    "servicos",
    "orcamentos",
    "movimentacoes",
]:
    for acao in ["visualizar", "editar", "excluir"]:
        codigo = f"financeiro.{tela}.{acao}"
        if not any(permissao[0] == codigo for permissao in PERMISSOES):
            PERMISSOES.append((codigo, "financeiro", tela, acao, acao != "visualizar"))

for codigo, tela, acao, sensivel in [
    ("financeiro.conciliacoes.visualizar", "conciliacoes", "visualizar", False),
    ("financeiro.conciliacoes.editar", "conciliacoes", "editar", True),
    ("financeiro.conciliacoes.importar", "conciliacoes", "importar", True),
    ("financeiro.conciliacoes.conciliar", "conciliacoes", "conciliar", True),
    ("financeiro.fluxo_caixa.visualizar", "fluxo_caixa", "visualizar", False),
    ("financeiro.relatorios.exportar", "relatorios", "exportar", True),
    ("inteligencia.alertas.editar", "alertas", "editar", True),
    ("inteligencia.anomalias.visualizar", "anomalias", "visualizar", False),
    ("inteligencia.anomalias.editar", "anomalias", "editar", True),
    ("inteligencia.previsoes.visualizar", "previsoes", "visualizar", False),
    ("inteligencia.previsoes.editar", "previsoes", "editar", True),
]:
    if not any(permissao[0] == codigo for permissao in PERMISSOES):
        modulo = "inteligencia" if codigo.startswith("inteligencia") else "financeiro"
        PERMISSOES.append((codigo, modulo, tela, acao, sensivel))

PERFIS = {
    "Administrador": PERMISSOES,
    "Financeiro": [permissao for permissao in PERMISSOES if permissao[1] == "financeiro"],
    "Diretoria": [
        permissao
        for permissao in PERMISSOES
        if permissao[3] in {"visualizar", "exportar"} or permissao[1] == "inteligencia"
    ],
    "Auditor": [
        permissao
        for permissao in PERMISSOES
        if permissao[3] in {"visualizar", "exportar"} or permissao[0] == "core.auditoria.visualizar"
    ],
}


class Command(BaseCommand):
    help = "Cria modulos, permissoes e perfis padrao do MVP."

    def handle(self, *args, **options):
        modulos = {}
        for codigo, nome, descricao in MODULOS:
            modulo, _ = Modulo.objects.update_or_create(
                codigo=codigo,
                defaults={"nome": nome, "descricao": descricao, "ativo": True},
            )
            modulos[codigo] = modulo

        permissoes = {}
        for codigo, modulo_codigo, tela, acao, sensivel in PERMISSOES:
            permissao, _ = Permissao.objects.update_or_create(
                codigo=codigo,
                defaults={
                    "modulo": modulos[modulo_codigo],
                    "tela": tela,
                    "acao": acao,
                    "sensivel": sensivel,
                },
            )
            permissoes[codigo] = permissao

        for nome, permissoes_perfil in PERFIS.items():
            perfil, _ = Perfil.objects.update_or_create(
                empresa=None,
                nome=nome,
                defaults={"sistema": True, "descricao": f"Perfil padrao: {nome}"},
            )
            for permissao_config in permissoes_perfil:
                PerfilPermissao.objects.get_or_create(perfil=perfil, permissao=permissoes[permissao_config[0]])

        self.stdout.write(self.style.SUCCESS("Seed do MVP concluido."))
