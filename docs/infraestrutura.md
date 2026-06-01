# Infraestrutura

## Visao geral

Este documento cobre os componentes de infraestrutura adicionados apos o MVP: tarefas assincronas com Celery, comandos de backup e restore do banco de dados, e estrutura de logs.

---

## Celery — Tarefas Assincronas

### Configuracao

Arquivo: `erp_financeiro/celery.py`

O Celery e inicializado com o namespace `CELERY_` no Django settings. As tasks sao descobertas automaticamente em todos os apps instalados via `autodiscover_tasks()`.

Para ativar o Celery, configure no `.env`:

```env
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Executar

Worker (processa tarefas):
```powershell
celery -A erp_financeiro worker --loglevel=info
```

Beat (agendador de tarefas periodicas):
```powershell
celery -A erp_financeiro beat --loglevel=info
```

### Tarefas agendadas

| Nome | Task | Horario |
|---|---|---|
| Previsao de caixa | `inteligencia.tasks.previsao_caixa` | Todos os dias as 06:00 |
| Alertas de vencimento | `core.tasks.alertas_vencimento` | Todos os dias as 07:00 |
| Cobranca automatica | `financeiro.tasks.cobranca_automatica` | Todos os dias as 08:00 |
| Importacao bancaria | `financeiro.tasks.importacao_bancaria` | A cada 4 horas (00h, 04h, 08h, 12h, 16h, 20h) |
| Fechamento diario | `financeiro.tasks.fechamento_diario` | Meia-noite (00:00) |

---

## Backup do Banco de Dados

### Comando

```powershell
python manage.py backup_db
```

### Comportamento por banco

**SQLite** — copia o arquivo `db.sqlite3` para a pasta `backups/`:
```
backups/backup_20260601_140530.db
```

**PostgreSQL** — executa `pg_dump` e salva em `.sql.gz` comprimido:
```
backups/backup_20260601_140530.sql.gz
```

O diretorio `backups/` e criado automaticamente se nao existir. O nome do arquivo contem o timestamp no formato `YYYYMMDD_HHMMSS`.

### Pre-requisitos para PostgreSQL

O binario `pg_dump` precisa estar no PATH do servidor. Em sistemas Debian/Ubuntu:
```bash
sudo apt install postgresql-client
```

---

## Restore do Banco de Dados

### Comando

```powershell
python manage.py restore_db <arquivo>
```

### Exemplos

```powershell
# SQLite
python manage.py restore_db backups/backup_20260601_140530.db

# PostgreSQL
python manage.py restore_db backups/backup_20260601_140530.sql.gz
```

### Comportamento

**SQLite** — antes de sobrescrever, cria automaticamente um backup de seguranca:
```
backups/pre_restore_20260601_143000.db
```
Em seguida copia o arquivo informado sobre o `db.sqlite3` atual.

**PostgreSQL** — descomprime o `.sql.gz` e executa via `psql`. Requer `psql` no PATH.

### Importante

O restore sobrescreve o banco atual. Em producao, verifique o backup de seguranca antes de confirmar.

---

## Logs

### Localizacao

```
logs/erp.log        — log geral da aplicacao (INFO e acima)
logs/erp_erros.log  — log exclusivo de erros (ERROR e acima)
```

O diretorio `logs/` e criado automaticamente pelo Django na primeira execucao se o handler estiver configurado.

### Configuracao no settings

Os handlers de arquivo ficam em `LOGGING` no `erp_financeiro/settings.py`. O formato padrao inclui timestamp, nivel, modulo e mensagem.

---

## Testes Automatizados

### Localizacao

```
core/tests/test_auth.py              — testes de autenticacao e bloqueio de login
financeiro/tests/test_contas_pagar.py  — testes de contas a pagar
financeiro/tests/test_contas_receber.py — testes de contas a receber
```

### Executar todos os testes

```powershell
python manage.py test core financeiro --verbosity 2
```

### Executar modulo especifico

```powershell
python manage.py test core.tests.test_auth --verbosity 2
python manage.py test financeiro.tests.test_contas_pagar --verbosity 2
```

---

## Verificacao de integridade do JavaScript

```powershell
node --check core\static\frontend\js\app.js
node --check core\static\frontend\js\api.js
node --check core\static\frontend\js\data.js
node --check core\static\frontend\js\ui.js
```
