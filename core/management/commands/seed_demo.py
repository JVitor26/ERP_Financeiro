from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import Empresa, EmpresaModulo, Modulo, Perfil, Usuario, UsuarioPerfil
from financeiro.models import (
    CentroCusto,
    Cliente,
    ContaBancaria,
    ContaPagar,
    ContaReceber,
    Fornecedor,
    PlanoConta,
    Servico,
    TipoPlanoConta,
)


class Command(BaseCommand):
    help = "Cria uma empresa, usuario e dados financeiros de demonstracao."

    def handle(self, *args, **options):
        hoje = timezone.localdate()

        empresa, _ = Empresa.objects.update_or_create(
            cnpj="00.000.000/0001-00",
            defaults={
                "razao_social": "Empresa Demo Ltda",
                "nome_fantasia": "Empresa Demo",
            },
        )

        for modulo in Modulo.objects.filter(codigo__in=["core", "financeiro", "inteligencia"]):
            EmpresaModulo.objects.get_or_create(empresa=empresa, modulo=modulo, defaults={"ativo": True})

        admin = self._usuario("admin", "admin@demo.local", "Admin", "Demo", empresa, "Admin@123", superuser=True)
        demo = self._usuario("demo", "demo@demo.local", "Usuario", "Demo", empresa, "Demo@123")

        for perfil in Perfil.objects.filter(sistema=True):
            UsuarioPerfil.objects.get_or_create(usuario=demo, perfil=perfil)

        centro, _ = CentroCusto.objects.update_or_create(
            empresa=empresa,
            codigo="ADM",
            defaults={"nome": "Administrativo", "ativo": True},
        )
        receita, _ = PlanoConta.objects.update_or_create(
            empresa=empresa,
            codigo="1.1",
            defaults={"nome": "Receitas operacionais", "tipo": TipoPlanoConta.RECEITA},
        )
        despesa, _ = PlanoConta.objects.update_or_create(
            empresa=empresa,
            codigo="2.1",
            defaults={"nome": "Despesas administrativas", "tipo": TipoPlanoConta.DESPESA},
        )
        conta_bancaria, _ = ContaBancaria.objects.update_or_create(
            empresa=empresa,
            banco="Banco Demo",
            numero="000123-4",
            defaults={"agencia": "0001", "descricao": "Conta principal", "saldo_inicial": Decimal("15000.00")},
        )
        cliente, _ = Cliente.objects.update_or_create(
            empresa=empresa,
            documento="11.111.111/0001-11",
            defaults={"nome": "Cliente Exemplo", "email": "cliente@demo.local", "telefone": "(65) 99999-0001"},
        )
        fornecedor, _ = Fornecedor.objects.update_or_create(
            empresa=empresa,
            documento="22.222.222/0001-22",
            defaults={"nome": "Fornecedor Exemplo", "email": "fornecedor@demo.local", "telefone": "(65) 99999-0002"},
        )
        Servico.objects.update_or_create(
            empresa=empresa,
            codigo="SERV-001",
            defaults={
                "nome": "Servico recorrente",
                "descricao": "Servico de demonstracao para lancamentos a receber.",
                "valor_padrao": Decimal("4800.00"),
                "plano_conta": receita,
            },
        )

        ContaPagar.objects.update_or_create(
            empresa=empresa,
            fornecedor=fornecedor,
            numero_documento="NF-1001",
            defaults={
                "descricao": "Servico de tecnologia",
                "data_emissao": hoje - timedelta(days=3),
                "data_vencimento": hoje + timedelta(days=7),
                "valor_original": Decimal("2500.00"),
                "centro_custo": centro,
                "plano_conta": despesa,
                "conta_bancaria": conta_bancaria,
                "responsavel": admin,
            },
        )
        ContaPagar.objects.update_or_create(
            empresa=empresa,
            fornecedor=fornecedor,
            numero_documento="NF-1002",
            defaults={
                "descricao": "Manutencao predial",
                "data_emissao": hoje - timedelta(days=10),
                "data_vencimento": hoje - timedelta(days=2),
                "valor_original": Decimal("850.00"),
                "centro_custo": centro,
                "plano_conta": despesa,
                "conta_bancaria": conta_bancaria,
                "responsavel": admin,
            },
        )
        ContaReceber.objects.update_or_create(
            empresa=empresa,
            cliente=cliente,
            contrato="CTR-2026-001",
            parcela=1,
            defaults={
                "descricao": "Mensalidade contrato",
                "data_emissao": hoje - timedelta(days=5),
                "data_vencimento": hoje + timedelta(days=5),
                "valor_original": Decimal("4800.00"),
                "centro_custo": centro,
                "plano_conta": receita,
                "conta_bancaria": conta_bancaria,
                "responsavel": admin,
            },
        )
        ContaReceber.objects.update_or_create(
            empresa=empresa,
            cliente=cliente,
            contrato="CTR-2026-001",
            parcela=2,
            defaults={
                "descricao": "Mensalidade contrato",
                "data_emissao": hoje - timedelta(days=35),
                "data_vencimento": hoje - timedelta(days=10),
                "valor_original": Decimal("4800.00"),
                "multa": Decimal("96.00"),
                "juros": Decimal("48.00"),
                "centro_custo": centro,
                "plano_conta": receita,
                "conta_bancaria": conta_bancaria,
                "responsavel": admin,
            },
        )

        self.stdout.write(self.style.SUCCESS("Dados de demonstracao criados."))
        self.stdout.write("Admin: admin / Admin@123")
        self.stdout.write("Usuario demo: demo / Demo@123")

    def _usuario(self, username, email, first_name, last_name, empresa, password, superuser=False):
        usuario, _ = Usuario.objects.update_or_create(
            username=username,
            defaults={
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "empresa": empresa,
                "is_staff": superuser,
                "is_superuser": superuser,
                "is_active": True,
            },
        )
        usuario.set_password(password)
        usuario.save(update_fields=["password"])
        return usuario
