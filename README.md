# ERP Financeiro Inteligente

ERP financeiro modular, multiempresa, rastreavel e preparado para camadas de IA.

## Modulos

| Modulo | Descricao |
|---|---|
| `core` | Empresas, usuarios, perfis, permissoes, auditoria e MFA |
| `financeiro` | Contas a pagar/receber, fluxo de caixa, conciliacao, orcamento, recorrencias, tesouraria, cobrancas, contratos e aplicacoes |
| `contabil` | Motor contabil por partidas dobradas, balancete, balanco patrimonial e DRE |
| `fiscal` | Notas fiscais, apuracao de impostos e obrigacoes fiscais |
| `inteligencia` | Alertas, anomalias e previsoes de IA |

## Stack

- Backend: Django 5 + Django REST Framework
- Autenticacao: JWT (`djangorestframework-simplejwt`) + MFA TOTP (`pyotp`)
- Banco desenvolvimento: SQLite
- Banco producao: PostgreSQL
- Tarefas assincronas: Celery + Redis
- Documentacao API: drf-spectacular + Swagger
- Frontend: HTML, CSS e JavaScript puro

## Estrutura

```text
erp_financeiro/   Configuracoes globais, URLs, Celery
core/             Empresas, usuarios, permissoes, auditoria, MFA
financeiro/       Financeiro operacional e avancado
contabil/         Motor contabil por partidas dobradas
fiscal/           Documentos fiscais e obrigacoes tributarias
inteligencia/     Alertas, anomalias e previsoes
templates/        HTML do painel web
docs/             Documentacao por modulo
sql/              Esquema SQL conceitual
```

## Como executar

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_mvp
python manage.py seed_demo
python manage.py seed_operacional
python manage.py runserver
```

## Comandos uteis

```powershell
# Testes
python manage.py test core financeiro inteligencia --verbosity 2

# Backup e restore do banco
python manage.py backup_db
python manage.py restore_db backups/backup_YYYYMMDD_HHMMSS.db

# Verificacao de integridade do JavaScript
node --check core\static\frontend\js\app.js

# Docker
docker compose up --build
```

## Celery (tarefas agendadas)

```powershell
# Worker
celery -A erp_financeiro worker --loglevel=info

# Beat (agendador)
celery -A erp_financeiro beat --loglevel=info
```

Tarefas configuradas: previsao de caixa (06h), alertas de vencimento (07h), cobranca automatica (08h), importacao bancaria (a cada 4h) e fechamento diario (00h).

## Acessos locais

- Painel web: `http://127.0.0.1:8000/`
- Admin Django: `http://127.0.0.1:8000/admin/`
- Swagger: `http://127.0.0.1:8000/api/docs/`
- JWT: `POST http://127.0.0.1:8000/api/auth/token/`

Usuarios criados pelo `seed_demo`:

- `admin` / `Admin@123`
- `demo` / `Demo@123`

## Documentacao

- [Sistema completo](docs/documentacao-sistema.md)
- [API](docs/api.md)
- [Modulo Contabil](docs/modulo-contabil.md)
- [Modulo Fiscal](docs/modulo-fiscal.md)
- [Financeiro Avancado](docs/modulo-financeiro-avancado.md)
- [MFA](docs/modulo-mfa.md)
- [Infraestrutura](docs/infraestrutura.md)
- [Modelo de dados](docs/modelo-dados.md)
- [Arquitetura](docs/arquitetura.md)
- [Requisitos MVP](docs/requisitos-mvp.md)
