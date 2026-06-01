# Arquitetura do ERP Financeiro Inteligente

## 1. Visao geral

O sistema e um monolito Django modular. A separacao principal ocorre por apps de dominio:

- `core`: base administrativa, seguranca, multiempresa, auditoria e permissoes.
- `financeiro`: operacao financeira, fluxo de caixa, DRE, conciliacao, aprovacoes e relatorios.
- `inteligencia`: alertas, anomalias e previsoes.

O frontend e servido pelo Django como uma aplicacao HTML/CSS/JavaScript pura e consome a API REST do proprio backend.

## 2. Camadas

```text
Browser
  |
  | HTML/CSS/JS
  v
Django URLs
  |
  | DRF ViewSets / APIViews
  v
Serializers
  |
  | validacao e normalizacao
  v
Services
  |
  | regras de negocio e transacoes
  v
Models
  |
  | ORM
  v
Database
```

## 3. Entrada HTTP

Arquivo principal:

```text
erp_financeiro/urls.py
```

Rotas globais:

- `/`: painel web;
- `/admin/`: admin Django;
- `/api/auth/token/`: login JWT;
- `/api/auth/token/refresh/`: refresh JWT;
- `/api/auth/token/verify/`: verificacao JWT;
- `/api/auth/me/`: usuario logado;
- `/api/schema/`: schema OpenAPI;
- `/api/docs/`: Swagger;
- `/api/core/`: rotas do core;
- `/api/financeiro/`: rotas financeiras;
- `/api/inteligencia/`: rotas de inteligencia.

## 4. Configuracao Django

Arquivo:

```text
erp_financeiro/settings.py
```

Responsabilidades:

- carregar `.env`;
- configurar apps instalados;
- configurar middleware;
- escolher SQLite ou PostgreSQL;
- definir `AUTH_USER_MODEL=core.Usuario`;
- configurar REST Framework;
- configurar JWT;
- configurar Swagger/OpenAPI;
- configurar arquivos estaticos e media;
- configurar seguranca HTTP.

## 5. Autenticacao

Implementacao:

```text
core/auth.py
core/auth_views.py
```

Fluxo:

1. Usuario envia credenciais para `POST /api/auth/token/`.
2. Backend verifica bloqueio por `LoginAttempt`.
3. Backend autentica usuario.
4. Se MFA estiver habilitado, exige `mfa_code=000000`.
5. Falhas incrementam tentativas e registram evento.
6. Sucesso limpa tentativas, atualiza `ultimo_ip` e `last_login`.
7. Backend retorna tokens JWT e dados basicos do usuario.

Tokens:

- access token: vida em minutos por `JWT_ACCESS_MINUTES`;
- refresh token: vida em dias por `JWT_REFRESH_DAYS`;
- refresh token rotaciona;
- token antigo entra em blacklist apos rotacao.

## 6. Autorizacao

Implementacao:

```text
core/permissions.py
```

Politicas:

- `StaffWritePermission`: usada nos recursos administrativos do core.
- `PermissaoPorAcao`: usada nos recursos operacionais.

`PermissaoPorAcao` gera o codigo esperado a partir de:

- `permissao_base` definida no viewset;
- action do DRF;
- metodo HTTP;
- `permissao_action_map` quando a action tem regra propria.

Exemplo:

```text
permissao_base = financeiro.contas_pagar
GET list       = financeiro.contas_pagar.visualizar
POST create    = financeiro.contas_pagar.editar
DELETE destroy = financeiro.contas_pagar.excluir
baixar         = financeiro.contas_pagar.baixar
```

## 7. Multiempresa

Implementacao:

```text
core/views.py
```

Mixin:

```text
EmpresaScopedQuerysetMixin
```

Regras:

- usuario anonimo nao ve dados;
- superuser ve tudo;
- usuario comum ve apenas registros da propria empresa;
- criacao/alteracao por usuario comum injeta `empresa_id` do usuario quando o campo direto e `empresa`;
- escopos indiretos usam `empresa_field`, por exemplo `conta_pagar__empresa`.

Esse mecanismo e usado por core, financeiro e inteligencia.

## 8. Auditoria

Implementacao:

```text
core/models.py
core/services.py
core/audit.py
```

Modelo:

```text
EventLog
```

Caracteristicas:

- imutavel;
- nao permite update;
- nao permite delete;
- encadeado por `hash_anterior`;
- assinado por `hash_evento`;
- guarda usuario, empresa, modulo, tela, acao, registro e snapshots JSON.

Mixins auditados:

- `AuditedCoreMixin`;
- `AuditedFinanceiroMixin`;
- `SoftDeleteLancamentoMixin`.

Eventos tambem sao registrados manualmente em services de regras de negocio.

## 9. App Core

Arquivos principais:

```text
core/models.py
core/serializers.py
core/views.py
core/urls.py
core/permissions.py
core/auth.py
core/services.py
core/audit.py
```

Responsabilidades:

- gerenciar empresas;
- gerenciar usuarios;
- gerenciar modulos;
- gerenciar perfis e permissoes;
- registrar auditoria;
- rastrear tentativas de login;
- expor notificacoes;
- prover utilitarios de snapshots e request context.

Recursos expostos:

- empresas;
- modulos;
- empresa-modulos;
- usuarios;
- perfis;
- permissoes;
- perfil-permissoes;
- usuario-perfis;
- eventos;
- notificacoes.

## 10. App Financeiro

Arquivos principais:

```text
financeiro/models.py
financeiro/serializers.py
financeiro/views.py
financeiro/services.py
financeiro/reports.py
financeiro/urls.py
```

Responsabilidades:

- manter cadastros financeiros;
- validar titulos;
- baixar contas a pagar;
- receber contas a receber;
- renegociar recebiveis;
- cancelar titulos;
- gerar movimentacoes;
- calcular fluxo e DRE;
- importar e conciliar extratos CSV;
- controlar aprovacoes;
- gerar relatorios.

Viewsets com regras simples usam serializers e mixins auditados. Fluxos com regra de negocio mais forte ficam em `financeiro/services.py` e usam transacoes atomicas.

## 11. Services financeiros

Principais funcoes:

- `baixar_conta_pagar`;
- `receber_conta_receber`;
- `solicitar_aprovacao_pagamento`;
- `decidir_aprovacao_pagamento`;
- `cancelar_conta_pagar`;
- `cancelar_conta_receber`;
- `renegociar_conta_receber`;
- `resumo_fluxo_caixa`;
- `dashboard_financeiro`;
- `dre_gerencial`;
- `importar_conciliacao_csv`;
- `sugerir_conciliacoes`;
- `conciliar_movimentacao`.

Fluxos transacionais usam `transaction.atomic` e `select_for_update` para evitar atualizacoes concorrentes em titulos e conciliacoes.

## 12. Relatorios

Implementacao:

```text
financeiro/reports.py
```

Tipos:

- contas a pagar;
- contas a receber;
- fluxo de caixa;
- eventos.

Formatos:

- CSV;
- XLSX;
- PDF.

Cada exportacao:

- monta queryset por empresa e periodo;
- gera `HttpResponse` com arquivo;
- registra evento de exportacao;
- cria `RelatorioGerado`.

## 13. App Inteligencia

Arquivos principais:

```text
inteligencia/models.py
inteligencia/serializers.py
inteligencia/views.py
inteligencia/services.py
inteligencia/urls.py
```

Responsabilidades:

- registrar alertas;
- registrar anomalias;
- registrar previsoes;
- detectar pagamentos duplicados;
- detectar valores fora do padrao por fornecedor;
- gerar previsao baseline de caixa;
- registrar feedback humano sobre anomalias.

A IA do MVP e heuristica. Nao ha modelo treinado, fila assincrona ou integracao externa.

## 14. Frontend

Arquivos:

```text
templates/frontend/index.html
core/static/frontend/css/app.css
core/static/frontend/js/app.js
core/static/frontend/js/api.js
core/static/frontend/js/data.js
core/static/frontend/js/ui.js
```

Responsabilidades por arquivo:

- `index.html`: estrutura das telas e sprites SVG.
- `app.css`: layout, responsividade e estados visuais.
- `api.js`: cliente HTTP, tokens, refresh e tratamento de erros.
- `data.js`: endpoints, labels, formatadores, datas e helpers.
- `ui.js`: componentes de tabela, modal, toast, badges, grafico e download.
- `app.js`: estado da aplicacao, carregamento de dados e eventos de tela.

O frontend carrega o workspace em paralelo usando `Promise.all` e renderiza as telas a partir do estado em memoria.

## 15. Dados iniciais

Comandos:

```text
seed_mvp
seed_demo
seed_operacional
```

`seed_mvp` cria estrutura de autorizacao.

`seed_demo` cria empresa, usuarios e base pequena.

`seed_operacional` cria uma massa maior para testar dashboard, DRE, contas e relatorios.

Os comandos usam `update_or_create` onde faz sentido, entao podem ser repetidos sem duplicar os principais cadastros identificados.

## 16. Banco de dados

Ambiente local:

```text
sqlite:///db.sqlite3
```

Producao recomendada:

```text
PostgreSQL
```

O banco e selecionado por `DATABASE_URL`. Quando nao for SQLite, o Django usa as variaveis `POSTGRES_*`.

## 17. Arquivos e media

Configuracao:

```text
MEDIA_URL = media/
MEDIA_ROOT = BASE_DIR / media
```

Usos:

- comprovantes de contas a pagar;
- anexos financeiros;
- relatorios persistidos, quando aplicavel.

Em producao, `MEDIA_ROOT` deve ser protegido por controle de acesso e backup.

## 18. Segurança operacional

Pontos ja existentes:

- JWT;
- token refresh com rotacao;
- blacklist de refresh antigo;
- bloqueio por falhas de login;
- MFA simples;
- filtro multiempresa;
- permissoes por perfil;
- auditoria imutavel;
- logs com IP e user agent quando disponivel;
- configuracoes de cookies seguros e HSTS via ambiente.

Pontos para endurecer em producao:

- trocar `SECRET_KEY`;
- `DEBUG=False`;
- HTTPS obrigatorio;
- cookies seguros;
- HSTS;
- politica real de MFA;
- politicas de backup e restore;
- armazenamento seguro de media;
- revisao de permissoes por perfil;
- remocao dos usuarios demo.

## 19. Evolucoes arquiteturais recomendadas

- Separar tarefas demoradas em fila assincrona.
- Rodar relatorios grandes em background.
- Adicionar importacao OFX.
- Integrar APIs bancarias reais.
- Criar permissao visual no frontend.
- Adicionar trilhas de auditoria mais granulares para leitura sensivel.
- Adicionar testes de API por endpoint.
- Adicionar testes end-to-end do painel.
- Migrar media para armazenamento externo em producao.
- Criar observabilidade com logs estruturados.
