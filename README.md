# ERP Financeiro Inteligente

Base inicial para um ERP financeiro modular, rastreavel e preparado para camadas de IA.

O projeto foi estruturado para um MVP com:

- empresas, usuarios, perfis e permissoes;
- controle de modulos instalaveis por empresa;
- contas a pagar e contas a receber;
- centros de custo, plano de contas e contas bancarias;
- fluxo de caixa operacional;
- conciliacao bancaria;
- logs de eventos para auditoria;
- primeira camada de alertas, anomalias e previsoes de IA.

## Stack proposta

- Backend: Django 5.x
- API: Django REST Framework
- Banco inicial: SQLite para desenvolvimento
- Banco recomendado para producao: PostgreSQL
- IA: servicos internos desacoplados por app, evoluindo para filas e modelos dedicados

## Estrutura

```text
erp_financeiro/       Configuracoes do projeto Django
core/                 Empresas, usuarios, permissoes, modulos e auditoria
financeiro/           Contas, fluxo de caixa, conciliacao e orcamento
inteligencia/         Alertas, anomalias e previsoes
docs/                 Requisitos, arquitetura, backlog e modelo de dados
sql/                  Esquema SQL conceitual do MVP
```

## Como executar quando Python estiver disponivel

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py makemigrations
python manage.py migrate
python manage.py seed_mvp
python manage.py seed_demo
python manage.py createsuperuser
python manage.py runserver
```

Neste ambiente foi criado um `.venv` local com Python 3.12 para executar o projeto.

## Comandos uteis

```powershell
.\.venv\Scripts\python.exe manage.py test core financeiro inteligencia --verbosity 2
.\.venv\Scripts\python.exe manage.py backup_sqlite
docker compose up --build
```

## Acessos locais

- Admin: `http://127.0.0.1:8000/admin/`
- API docs: `http://127.0.0.1:8000/api/docs/`
- JWT: `POST http://127.0.0.1:8000/api/auth/token/`

Usuario demo:

- `admin` / `Admin@123`
- `demo` / `Demo@123`

## Documentos principais

- [Documentacao completa do sistema](docs/documentacao-sistema.md)
- [Requisitos do MVP](docs/requisitos-mvp.md)
- [Arquitetura modular](docs/arquitetura.md)
- [Backlog inicial](docs/backlog-mvp.md)
- [Modelo de dados](docs/modelo-dados.md)
- [Taxonomia de eventos](docs/taxonomia-eventos.md)
- [API inicial](docs/api.md)
