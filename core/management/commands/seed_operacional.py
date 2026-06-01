from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Empresa, Usuario
from financeiro.models import (
    CentroCusto,
    Cliente,
    ContaBancaria,
    ContaPagar,
    ContaReceber,
    Fornecedor,
    MovimentacaoFinanceira,
    PlanoConta,
    Servico,
    StatusContaPagar,
    StatusContaReceber,
    TipoMovimentacao,
    TipoPessoa,
    TipoPlanoConta,
)


class Command(BaseCommand):
    help = "Popula cadastros e movimentacoes operacionais para uso local."

    def handle(self, *args, **options):
        hoje = timezone.localdate()
        empresa = self._empresa()
        responsavel = Usuario.objects.filter(username="admin").first()

        centros = self._centros_custo(empresa)
        planos = self._planos_conta(empresa)
        contas = self._contas_bancarias(empresa)
        clientes = self._clientes(empresa)
        fornecedores = self._fornecedores(empresa)
        servicos = self._servicos(empresa, planos)
        contas_receber = self._contas_receber(empresa, clientes, centros, planos, contas, responsavel, hoje)
        contas_pagar = self._contas_pagar(empresa, fornecedores, centros, planos, contas, responsavel, hoje)
        movimentacoes = self._movimentacoes(empresa, clientes, fornecedores, centros, planos, contas, hoje)

        self.stdout.write(self.style.SUCCESS("Carga operacional concluida."))
        self.stdout.write(f"Empresa: {empresa}")
        self.stdout.write(f"Clientes: {len(clientes)}")
        self.stdout.write(f"Fornecedores: {len(fornecedores)}")
        self.stdout.write(f"Servicos: {len(servicos)}")
        self.stdout.write(f"Planos de contas: {len(planos)}")
        self.stdout.write(f"Centros de custo: {len(centros)}")
        self.stdout.write(f"Contas bancarias: {len(contas)}")
        self.stdout.write(f"Contas a receber: {len(contas_receber)}")
        self.stdout.write(f"Contas a pagar: {len(contas_pagar)}")
        self.stdout.write(f"Transacoes financeiras: {len(movimentacoes)}")

    def _empresa(self):
        empresa, _ = Empresa.objects.update_or_create(
            cnpj="00.000.000/0001-00",
            defaults={
                "razao_social": "Empresa Demo Ltda",
                "nome_fantasia": "Empresa Demo",
                "status": "ativa",
            },
        )
        return empresa

    def _centros_custo(self, empresa):
        dados = [
            ("ADM", "Administrativo"),
            ("FIN", "Financeiro"),
            ("COM", "Comercial"),
            ("MKT", "Marketing"),
            ("TEC", "Tecnologia"),
            ("JUR", "Juridico"),
            ("RH", "Recursos humanos"),
            ("OBR", "Obras e manutencao"),
            ("LOG", "Logistica"),
            ("DIR", "Diretoria"),
        ]
        centros = []
        for codigo, nome in dados:
            centro, _ = CentroCusto.objects.update_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={"nome": nome, "ativo": True},
            )
            centros.append(centro)
        return centros

    def _planos_conta(self, empresa):
        dados = [
            ("1.1", "Receita de servicos", TipoPlanoConta.RECEITA),
            ("1.2", "Receita recorrente", TipoPlanoConta.RECEITA),
            ("1.3", "Receita eventual", TipoPlanoConta.RECEITA),
            ("2.1", "Fornecedores operacionais", TipoPlanoConta.DESPESA),
            ("2.2", "Despesas administrativas", TipoPlanoConta.DESPESA),
            ("2.3", "Marketing e vendas", TipoPlanoConta.DESPESA),
            ("2.4", "Tecnologia e sistemas", TipoPlanoConta.DESPESA),
            ("2.5", "Juridico e contabilidade", TipoPlanoConta.DESPESA),
            ("3.1", "Custo de entrega", TipoPlanoConta.CUSTO),
            ("3.2", "Manutencao predial", TipoPlanoConta.CUSTO),
            ("4.1", "Impostos sobre receita", TipoPlanoConta.IMPOSTO),
            ("5.1", "Taxas bancarias", TipoPlanoConta.TAXA),
            ("6.1", "Comissoes comerciais", TipoPlanoConta.COMISSAO),
            ("7.1", "Investimentos em ativos", TipoPlanoConta.INVESTIMENTO),
        ]
        planos = []
        for codigo, nome, tipo in dados:
            plano, _ = PlanoConta.objects.update_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={
                    "nome": nome,
                    "tipo": tipo,
                    "ativo": True,
                    "vincula_dre": True,
                    "vincula_fluxo_caixa": True,
                },
            )
            planos.append(plano)
        return planos

    def _contas_bancarias(self, empresa):
        dados = [
            ("Banco Demo", "0001", "000123-4", "Conta principal", "15000.00"),
            ("Banco Nacional", "1204", "84721-9", "Recebimentos", "32800.00"),
            ("Banco Empresarial", "0302", "99210-5", "Pagamentos", "21450.00"),
            ("Cooperativa Credito", "4120", "55187-1", "Reserva operacional", "67000.00"),
            ("Banco Digital", "0001", "78291-0", "Conta de taxas", "8500.00"),
        ]
        contas = []
        for banco, agencia, numero, descricao, saldo in dados:
            conta, _ = ContaBancaria.objects.update_or_create(
                empresa=empresa,
                banco=banco,
                numero=numero,
                defaults={
                    "agencia": agencia,
                    "descricao": descricao,
                    "saldo_inicial": Decimal(saldo),
                    "ativa": True,
                },
            )
            contas.append(conta)
        return contas

    def _clientes(self, empresa):
        nomes = [
            "Alfa Comercio Ltda",
            "Beta Incorporadora",
            "Campo Verde Agronegocios",
            "Delta Servicos Medicos",
            "Estrela Norte Transportes",
            "Fenix Participacoes",
            "Garden Mall Administradora",
            "Horizonte Engenharia",
            "Imperio Atacadista",
            "Jardim das Aguas SPE",
            "Kairon Tecnologia",
            "Litoral Urbanismo",
            "Monte Azul Empreendimentos",
            "Nova Rota Logistica",
            "Origem Alimentos",
            "Prime Consultoria",
            "Quality Center",
            "Rio Claro Energia",
            "Solaris Educacional",
            "Terra Forte Imoveis",
        ]
        clientes = []
        for index, nome in enumerate(nomes, start=1):
            cliente, _ = Cliente.objects.update_or_create(
                empresa=empresa,
                documento=self._cnpj(index),
                defaults={
                    "nome": nome,
                    "tipo_pessoa": TipoPessoa.JURIDICA,
                    "email": f"financeiro{index}@cliente.demo",
                    "telefone": f"(65) 9{index:04d}-{1000 + index:04d}",
                    "ativo": True,
                },
            )
            clientes.append(cliente)
        return clientes

    def _fornecedores(self, empresa):
        nomes = [
            "Abastece Centro Oeste",
            "Base Contabil",
            "Cloud Prime Sistemas",
            "Digital Ads Performance",
            "Eco Limpeza Profissional",
            "Forte Seguranca Patrimonial",
            "Grafica Expressa",
            "Help Desk Telecom",
            "Infra Master Engenharia",
            "Juridico Silva Associados",
            "Kappa Equipamentos",
            "Link Internet Dedicada",
            "Maq Predial Manutencao",
            "Nobre Beneficios",
            "Office Paper Suprimentos",
            "Ponto Certo Energia",
            "QualyMed Ocupacional",
            "Rota Sul Fretes",
            "Solucoes RH",
            "TecnoPay Meios de Pagamento",
        ]
        fornecedores = []
        for index, nome in enumerate(nomes, start=101):
            fornecedor, _ = Fornecedor.objects.update_or_create(
                empresa=empresa,
                documento=self._cnpj(index),
                defaults={
                    "nome": nome,
                    "tipo_pessoa": TipoPessoa.JURIDICA,
                    "email": f"contas{index}@fornecedor.demo",
                    "telefone": f"(65) 3{index:03d}-{2000 + index:04d}",
                    "ativo": True,
                },
            )
            fornecedores.append(fornecedor)
        return fornecedores

    def _servicos(self, empresa, planos):
        receitas = [plano for plano in planos if plano.tipo == TipoPlanoConta.RECEITA]
        dados = [
            ("SERV-001", "Mensalidade administrativa", "4800.00"),
            ("SERV-002", "Consultoria financeira", "6200.00"),
            ("SERV-003", "Gestao de contratos", "3500.00"),
            ("SERV-004", "Auditoria operacional", "7800.00"),
            ("SERV-005", "Analise de carteira", "2600.00"),
            ("SERV-006", "Relatorio gerencial", "1900.00"),
            ("SERV-007", "Implantacao de sistema", "12500.00"),
            ("SERV-008", "Suporte recorrente", "2200.00"),
            ("SERV-009", "Processamento financeiro", "4100.00"),
            ("SERV-010", "Treinamento de equipe", "3300.00"),
        ]
        servicos = []
        for index, (codigo, nome, valor) in enumerate(dados):
            servico, _ = Servico.objects.update_or_create(
                empresa=empresa,
                codigo=codigo,
                defaults={
                    "nome": nome,
                    "descricao": f"{nome} para operacao financeira.",
                    "valor_padrao": Decimal(valor),
                    "plano_conta": receitas[index % len(receitas)] if receitas else None,
                    "ativo": True,
                },
            )
            servicos.append(servico)
        return servicos

    def _contas_receber(self, empresa, clientes, centros, planos, contas, responsavel, hoje):
        receitas = [plano for plano in planos if plano.tipo == TipoPlanoConta.RECEITA]
        registros = []
        for index in range(1, 81):
            cliente = clientes[index % len(clientes)]
            vencimento = hoje + timedelta(days=(index % 95) - 35)
            valor = Decimal("1200.00") + Decimal(index % 13) * Decimal("315.50")
            recebido = Decimal("0.00")
            status = StatusContaReceber.ABERTO
            data_recebimento = None
            if index % 8 == 0:
                recebido = valor
                status = StatusContaReceber.RECEBIDO
                data_recebimento = timezone.now() - timedelta(days=index % 20)
            elif vencimento < hoje and index % 5 == 0:
                recebido = (valor * Decimal("0.45")).quantize(Decimal("0.01"))
                status = StatusContaReceber.RECEBIDO_PARCIAL
            elif vencimento < hoje:
                status = StatusContaReceber.VENCIDO
            elif (vencimento - hoje).days <= 7:
                status = StatusContaReceber.A_VENCER

            conta, _ = ContaReceber.objects.update_or_create(
                empresa=empresa,
                cliente=cliente,
                contrato=f"CTR-OP-{index:04d}",
                parcela=1,
                defaults={
                    "descricao": f"Servico mensal {index:04d}",
                    "data_emissao": vencimento - timedelta(days=20 + (index % 12)),
                    "data_vencimento": vencimento,
                    "valor_original": valor,
                    "valor_recebido": recebido,
                    "status": status,
                    "data_recebimento": data_recebimento,
                    "centro_custo": centros[index % len(centros)],
                    "plano_conta": receitas[index % len(receitas)],
                    "conta_bancaria": contas[index % len(contas)],
                    "responsavel": responsavel,
                },
            )
            registros.append(conta)
        return registros

    def _contas_pagar(self, empresa, fornecedores, centros, planos, contas, responsavel, hoje):
        despesas = [plano for plano in planos if plano.tipo in {TipoPlanoConta.DESPESA, TipoPlanoConta.CUSTO, TipoPlanoConta.TAXA}]
        registros = []
        for index in range(1, 76):
            fornecedor = fornecedores[index % len(fornecedores)]
            vencimento = hoje + timedelta(days=(index % 85) - 30)
            valor = Decimal("450.00") + Decimal(index % 17) * Decimal("187.35")
            pago = Decimal("0.00")
            status = StatusContaPagar.ABERTO
            data_baixa = None
            if index % 9 == 0:
                pago = valor
                status = StatusContaPagar.PAGO
                data_baixa = timezone.now() - timedelta(days=index % 15)
            elif vencimento < hoje and index % 6 == 0:
                pago = (valor * Decimal("0.40")).quantize(Decimal("0.01"))
                status = StatusContaPagar.PAGO_PARCIAL
            elif vencimento < hoje:
                status = StatusContaPagar.VENCIDO
            elif (vencimento - hoje).days <= 7:
                status = StatusContaPagar.A_VENCER

            conta, _ = ContaPagar.objects.update_or_create(
                empresa=empresa,
                fornecedor=fornecedor,
                numero_documento=f"NF-OP-{index:04d}",
                defaults={
                    "descricao": f"Despesa operacional {index:04d}",
                    "data_emissao": vencimento - timedelta(days=10 + (index % 18)),
                    "data_vencimento": vencimento,
                    "valor_original": valor,
                    "valor_pago": pago,
                    "status": status,
                    "data_baixa": data_baixa,
                    "forma_pagamento": "Transferencia" if pago else "",
                    "centro_custo": centros[index % len(centros)],
                    "plano_conta": despesas[index % len(despesas)],
                    "conta_bancaria": contas[index % len(contas)],
                    "responsavel": responsavel,
                },
            )
            registros.append(conta)
        return registros

    def _movimentacoes(self, empresa, clientes, fornecedores, centros, planos, contas, hoje):
        receitas = [plano for plano in planos if plano.tipo == TipoPlanoConta.RECEITA]
        despesas = [plano for plano in planos if plano.tipo != TipoPlanoConta.RECEITA]
        registros = []
        for index in range(1, 121):
            entrada = index % 3 != 0
            tipo = TipoMovimentacao.ENTRADA if entrada else TipoMovimentacao.SAIDA
            parceiro = clientes[index % len(clientes)] if entrada else fornecedores[index % len(fornecedores)]
            plano = receitas[index % len(receitas)] if entrada else despesas[index % len(despesas)]
            valor_base = Decimal("900.00") if entrada else Decimal("320.00")
            valor = valor_base + Decimal(index % 19) * Decimal("142.75")
            movimento, _ = MovimentacaoFinanceira.objects.update_or_create(
                empresa=empresa,
                origem_modelo="seed_operacional",
                origem_id=f"MOV-{index:04d}",
                defaults={
                    "tipo": tipo,
                    "descricao": f"{'Recebimento' if entrada else 'Pagamento'} - {parceiro.nome}",
                    "data_movimento": hoje + timedelta(days=(index % 80) - 45),
                    "data_competencia": hoje.replace(day=1),
                    "valor": valor,
                    "conta_bancaria": contas[index % len(contas)],
                    "centro_custo": centros[index % len(centros)],
                    "plano_conta": plano,
                    "conciliado": index % 4 != 0,
                },
            )
            registros.append(movimento)
        return registros

    def _cnpj(self, index):
        return f"{index % 100:02d}.{index % 1000:03d}.{(index * 37) % 1000:03d}/0001-{(index * 11) % 100:02d}"
