# Documentacao completa do ERP Financeiro Inteligente

Este documento descreve o sistema implementado no repositorio `ERP_Financeiro`. Ele consolida a visao funcional, tecnica e operacional do MVP para que uma pessoa consiga entender o que existe, como executar, como operar, quais regras existem e onde evoluir.

## 1. Objetivo do sistema

O ERP Financeiro Inteligente e uma aplicacao web multiempresa para gestao financeira operacional. O sistema centraliza cadastros, contas a pagar, contas a receber, movimentacoes, fluxo de caixa, DRE gerencial, conciliacao bancaria, aprovacoes, auditoria, relatorios e uma camada inicial de inteligencia financeira.

O foco do MVP e entregar:

- controle financeiro essencial;
- rastreabilidade de eventos;
- operacao separada por empresa;
- permissoes por perfil, tela e acao;
- painel web executivo;
- API REST documentada;
- base de IA simples para alertas, anomalias e previsoes.

## 2. Stack

- Backend: Django 5 e Django REST Framework.
- Autenticacao: JWT com `djangorestframework-simplejwt`.
- Banco local: SQLite.
- Banco recomendado em producao: PostgreSQL.
- Filtros: `django-filter`.
- Documentacao OpenAPI: `drf-spectacular` e Swagger.
- Exportacao XLSX: `openpyxl`.
- Exportacao PDF: `reportlab`.
- Frontend: HTML, CSS e JavaScript puro.
- Container: Dockerfile e `docker-compose.yml`.

## 3. Organizacao do repositorio

```text
erp_financeiro/        Configuracoes globais, URLs, ASGI e WSGI
core/                  Empresas, usuarios, modulos, permissoes, auditoria e autenticacao
financeiro/            Cadastros financeiros, titulos, baixas, fluxo, DRE, conciliacao e relatorios
inteligencia/          Alertas, anomalias e previsoes
templates/frontend/    HTML do painel web
core/static/frontend/  CSS e JavaScript do painel web
docs/                  Documentacao funcional e tecnica
sql/                   Esquema SQL conceitual do MVP
```

## 4. Arquivos de configuracao

O projeto le variaveis do arquivo `.env` usando `python-dotenv`. O arquivo `.env.example` documenta os valores esperados.

Variaveis principais:

```text
SECRET_KEY
DEBUG
ALLOWED_HOSTS
DATABASE_URL
JWT_ACCESS_MINUTES
JWT_REFRESH_DAYS
LOGIN_FAILURE_LIMIT
LOGIN_LOCKOUT_MINUTES
SECURE_SSL_REDIRECT
SESSION_COOKIE_SECURE
CSRF_COOKIE_SECURE
```

Quando `DATABASE_URL` comeca com `sqlite:///`, o Django usa SQLite no arquivo local. Quando nao comeca com `sqlite:///`, o projeto usa PostgreSQL e le:

```text
POSTGRES_DB
POSTGRES_USER
POSTGRES_PASSWORD
POSTGRES_HOST
POSTGRES_PORT
```

## 5. Execucao local

Preparar ambiente:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Aplicar banco e dados iniciais:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_mvp
.\.venv\Scripts\python.exe manage.py seed_demo
.\.venv\Scripts\python.exe manage.py seed_operacional
```

Executar:

```powershell
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Validar:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test core financeiro inteligencia --verbosity 2
node --check core\static\frontend\js\app.js
node --check core\static\frontend\js\api.js
node --check core\static\frontend\js\data.js
node --check core\static\frontend\js\ui.js
```

## 6. Acessos locais

- Painel web: `http://127.0.0.1:8000/`
- Admin Django: `http://127.0.0.1:8000/admin/`
- Swagger: `http://127.0.0.1:8000/api/docs/`
- Schema OpenAPI: `http://127.0.0.1:8000/api/schema/`
- JWT: `POST /api/auth/token/`

Usuarios criados pelo `seed_demo`:

- `admin` / `Admin@123`
- `demo` / `Demo@123`

## 7. Modulos do sistema

### Core

Responsavel pela base administrativa:

- empresas;
- usuarios;
- modulos;
- instalacao de modulos por empresa;
- perfis;
- permissoes;
- vinculo de perfil com permissao;
- vinculo de usuario com perfil;
- auditoria imutavel;
- tentativas de login;
- notificacoes.

### Financeiro

Responsavel pela operacao financeira:

- clientes;
- fornecedores;
- servicos;
- centros de custo;
- plano de contas;
- contas bancarias;
- contas a pagar;
- contas a receber;
- movimentacoes financeiras;
- conciliacao bancaria;
- orcamentos;
- aprovacoes de pagamento;
- relatorios;
- anexos financeiros.

### Inteligencia

Responsavel pela camada inicial de analise:

- alertas de IA;
- anomalias;
- previsoes;
- varredura de duplicidades;
- analise de fornecedor fora do padrao;
- previsao baseline de caixa;
- feedback sobre analises.

## 8. Frontend web

O painel web fica em `templates/frontend/index.html` e consome os arquivos em `core/static/frontend/`.

Telas disponiveis:

- Login: autenticacao JWT, campo opcional de MFA e mensagem de erro.
- Visao geral: KPIs, grafico de fluxo, alertas de risco, proximos vencimentos e DRE.
- Financeiro: contas a receber, contas a pagar, criacao de titulos, baixa e recebimento.
- Aprovacoes: fila de aprovacoes pendentes e historico de decisoes.
- Cadastros: clientes, fornecedores, servicos, contas bancarias, centros de custo e plano de contas.
- Inteligencia: alertas, anomalias, previsoes, varredura e feedback.
- Auditoria: eventos imutaveis e notificacoes.
- Empresas: empresas e modulos instalados.
- Relatorios: exportacao de fluxo, contas e eventos.

O frontend usa `localStorage` para:

- guardar token de acesso e refresh;
- memorizar se valores monetarios devem ficar ocultos.

O botao de olho mascara valores como `R$ ***` em cards, tabelas e paineis.

## 9. Autenticacao

O login e feito por JWT em `POST /api/auth/token/`. O retorno contem `access`, `refresh` e dados basicos do usuario.

Regras implementadas:

- login bem sucedido registra evento `core.auth.login_sucesso`;
- login falho registra evento `core.auth.login_falhou`;
- tentativas falhas sao contadas por `username` e IP;
- apos o limite configurado, o usuario fica bloqueado temporariamente;
- usuarios com `mfa_habilitado=True` precisam enviar `mfa_code`;
- o codigo MFA aceito no MVP e `000000`;
- refresh de token usa `POST /api/auth/token/refresh/`;
- o painel consulta `GET /api/auth/me/` apos autenticar.

## 10. Multiempresa

O isolamento por empresa e feito por `EmpresaScopedQuerysetMixin`.

Regras:

- superuser enxerga todas as empresas;
- usuario comum enxerga apenas registros da sua empresa;
- quando usuario comum cria registro com campo `empresa`, o backend grava a empresa do usuario;
- usuario sem empresa vinculada recebe erro em endpoints que exigem empresa operacional;
- recursos ligados indiretamente a empresa usam `empresa_field`, por exemplo `conta_pagar__empresa`.

Entidades diretamente escopadas por empresa incluem clientes, fornecedores, servicos, contas bancarias, centros de custo, plano de contas, contas a pagar, contas a receber, movimentacoes, conciliacoes, orcamentos, notificacoes, alertas, anomalias e previsoes.

## 11. Permissoes

Existem duas politicas principais:

- `StaffWritePermission`: leitura para autenticados e escrita apenas para `is_staff`. Usada nos cadastros administrativos do core.
- `PermissaoPorAcao`: valida codigos de permissao em `UsuarioPerfil -> PerfilPermissao -> Permissao`.

O superuser sempre passa.

Mapeamento padrao por metodo:

```text
GET/HEAD/OPTIONS -> visualizar
POST/PUT/PATCH   -> editar
DELETE           -> excluir
```

Actions especificas podem sobrescrever esse mapeamento:

```text
financeiro.contas_pagar.baixar
financeiro.contas_pagar.aprovar
financeiro.contas_receber.receber
financeiro.conciliacoes.importar
financeiro.conciliacoes.conciliar
financeiro.relatorios.exportar
inteligencia.anomalias.gerar
inteligencia.previsoes.editar
```

Perfis padrao criados pelo `seed_mvp`:

- Administrador: todas as permissoes.
- Financeiro: permissoes do modulo financeiro.
- Diretoria: leitura, exportacao e inteligencia.
- Auditor: leitura, exportacao e auditoria.

## 12. Auditoria

O modelo `EventLog` e a trilha imutavel do sistema. Ele nao permite alteracao nem exclusao depois de criado.

Campos relevantes:

- `event_id`: UUID publico do evento;
- `tipo_evento`: criacao, alteracao, exclusao logica, baixa, aprovacao, reprovacao, exportacao, acesso sensivel, alerta de sistema, alerta de IA ou integracao;
- `usuario` e `empresa`;
- `modulo`, `tela` e `acao`;
- `registro_modelo` e `registro_id`;
- `valor_anterior` e `valor_novo`;
- `ip`, `dispositivo` e `origem`;
- `justificativa`;
- `nivel_risco`;
- `hash_anterior` e `hash_evento`;
- `metadados`;
- `criado_em`.

A cadeia de hashes usa SHA-256 sobre os dados principais do evento e o hash anterior, criando rastreabilidade sequencial.

Eventos automaticos sao gerados em:

- criacao e alteracao via viewsets auditados;
- exclusao logica de contas;
- baixa de contas a pagar;
- recebimento de contas a receber;
- aprovacao e reprovacao;
- cancelamentos;
- renegociacao;
- importacao e conciliacao;
- exportacao de relatorios;
- login com sucesso/falha;
- alertas de IA.

## 13. Regras financeiras gerais

Regras de validacao:

- `valor_original` precisa ser maior que zero.
- `desconto`, `juros`, `multa`, `acrescimo`, `honorarios`, `valor_pago` e `valor_recebido` nao podem ser negativos.
- `desconto` nao pode ser maior que `valor_original`.
- `data_vencimento` nao pode ser anterior a `data_emissao`.
- relacionamentos financeiros precisam pertencer a mesma empresa do titulo.
- conta paga nao pode ter campos financeiros criticos alterados.
- conta recebida nao pode ter campos financeiros criticos alterados.
- status `pago` e `recebido` devem ser atingidos por baixa/recebimento, nao por alteracao direta.

## 14. Cadastros financeiros

Cadastros disponiveis:

- Centro de custo: codigo, nome, hierarquia por `pai` e status ativo.
- Plano de contas: codigo, nome, tipo, hierarquia, vinculo com DRE e fluxo.
- Conta bancaria: banco, agencia, numero, descricao, saldo inicial e status ativo.
- Cliente: nome, tipo de pessoa, documento, email, telefone e metadados.
- Fornecedor: nome, tipo de pessoa, documento, email, telefone e metadados.
- Servico: codigo, nome, descricao, valor padrao, plano de contas e metadados.

Restricoes:

- centro de custo e plano de contas possuem codigo unico por empresa;
- servico possui codigo unico por empresa quando codigo nao esta vazio;
- clientes e fornecedores sao indexados por empresa e documento.

## 15. Contas a pagar

Contas a pagar representam titulos de fornecedores.

Campos principais:

- empresa;
- fornecedor;
- descricao;
- data de emissao;
- data de vencimento;
- valor original;
- desconto, juros, multa e acrescimo;
- centro de custo;
- plano de contas;
- conta bancaria;
- numero do documento;
- nota fiscal;
- valor pago;
- forma de pagamento;
- status;
- data de baixa;
- usuario que baixou;
- comprovante;
- responsavel;
- exclusao logica.

Status possiveis:

```text
aberto
a_vencer
vencido
pago
pago_parcial
cancelado
em_aprovacao
reprovado
agendado
```

Acoes:

- criar/editar/listar/detalhar;
- baixar total ou parcialmente;
- solicitar aprovacao;
- cancelar com justificativa;
- anexar comprovante;
- excluir logicamente.

Regras de baixa:

- valor precisa ser maior que zero;
- conta excluida, paga, cancelada ou reprovada nao pode ser baixada;
- conta com aprovacao pendente nao pode ser baixada;
- valor de baixa nao pode ultrapassar saldo pendente;
- baixa parcial muda status para `pago_parcial`;
- baixa total muda status para `pago`;
- baixa com conta bancaria gera `MovimentacaoFinanceira` de saida.

## 16. Contas a receber

Contas a receber representam titulos de clientes.

Campos principais:

- empresa;
- cliente;
- contrato;
- parcela;
- descricao;
- data de emissao;
- data de vencimento;
- valor original;
- desconto, juros, multa, acrescimo e honorarios;
- centro de custo;
- plano de contas;
- conta bancaria;
- valor recebido;
- forma de recebimento;
- status;
- data de recebimento;
- usuario que recebeu;
- conta original em caso de renegociacao;
- dados de renegociacao;
- responsavel;
- exclusao logica.

Status possiveis:

```text
aberto
a_vencer
vencido
recebido
recebido_parcial
cancelado
renegociado
em_cobranca
judicial
protestado
```

Acoes:

- criar/editar/listar/detalhar;
- receber total ou parcialmente;
- renegociar;
- cancelar com justificativa;
- anexar arquivo;
- excluir logicamente.

Regras de recebimento:

- valor precisa ser maior que zero;
- conta excluida, recebida ou cancelada nao pode ser recebida;
- valor recebido nao pode ultrapassar saldo pendente;
- recebimento parcial muda status para `recebido_parcial`;
- recebimento total muda status para `recebido`;
- recebimento com conta bancaria gera `MovimentacaoFinanceira` de entrada.

Regras de renegociacao:

- conta recebida ou cancelada nao pode ser renegociada;
- conta original muda para `renegociado`;
- nova conta e criada com nova data, valor e encargos;
- nova conta aponta para `conta_original`.

## 17. Movimentacoes financeiras

Movimentacoes representam entradas e saidas realizadas. Elas sao geradas por baixas, recebimentos, cargas operacionais ou integracoes futuras.

Campos:

- empresa;
- tipo (`entrada` ou `saida`);
- descricao;
- data do movimento;
- data de competencia;
- valor;
- conta bancaria;
- centro de custo;
- plano de contas;
- origem_modelo;
- origem_id;
- conciliado.

O endpoint de movimentacoes e somente leitura.

## 18. Fluxo de caixa

O fluxo calcula:

- total a pagar pendente no periodo;
- total a receber pendente no periodo;
- entradas realizadas;
- saidas realizadas;
- saldo previsto;
- saldo realizado;
- inadimplencia.

Endpoints:

- `GET /api/financeiro/fluxo-caixa/`
- `GET /api/financeiro/fluxo-caixa/dashboard/`
- `GET /api/financeiro/fluxo-caixa/dre/`

Todos exigem `data_inicio` e `data_fim`.

## 19. DRE gerencial

A DRE usa movimentacoes realizadas no periodo.

Linhas principais:

- Receita bruta;
- Deducoes, impostos, taxas e comissoes;
- Receita liquida;
- Custos variaveis;
- Margem de contribuicao;
- Despesas operacionais;
- Resultado operacional;
- Investimentos e outras saidas;
- Lucro / prejuizo.

Classificacao:

- toda entrada soma em receita bruta;
- saidas com plano `imposto`, `taxa`, `comissao` ou `repasse` entram em deducoes;
- saidas com plano `custo` entram em custos variaveis;
- saidas com plano `despesa` entram em despesas operacionais;
- saidas com plano `investimento` entram em investimentos;
- demais saidas entram em outras saidas.

A resposta tambem traz abertura por centro de custo e por plano de contas.

## 20. Conciliacao bancaria

O modulo de conciliacao importa extratos CSV e vincula linhas bancarias a movimentacoes.

Campos da conciliacao:

- empresa;
- conta bancaria;
- data do movimento;
- valor;
- historico;
- documento;
- status;
- movimentacao vinculada;
- metadados.

Status:

```text
pendente
sugerida
conciliada
divergente
duplicada
```

CSV aceito:

- delimitador `,` ou `;`;
- colunas `data` ou `data_movimento`;
- coluna `valor`;
- coluna `historico` ou `descricao`;
- coluna opcional `documento`.

Sugestao automatica:

- busca movimentacao da mesma empresa e conta bancaria;
- valor igual ao modulo do valor do extrato;
- data em janela de 3 dias antes ou depois;
- movimentacao ainda nao conciliada.

Conciliacao manual:

- vincula a movimentacao informada;
- marca conciliacao como `conciliada`;
- marca movimentacao como `conciliado=True`;
- registra evento.

## 21. Orcamentos

Orcamentos guardam previsoes por periodo e dimensoes financeiras.

Campos:

- empresa;
- ano;
- mes opcional;
- centro de custo opcional;
- plano de contas opcional;
- valor previsto;
- valor realizado.

Restricao:

- a combinacao empresa, ano, mes, centro de custo e plano de contas e unica.

## 22. Aprovacoes de pagamento

Fluxo:

1. Usuario solicita aprovacao em uma conta a pagar.
2. A conta muda para `em_aprovacao`.
3. Registro `AprovacaoPagamento` fica `pendente`.
4. Aprovador aprova ou reprova.
5. Se aprovada, a conta muda para `agendado`.
6. Se reprovada, a conta muda para `reprovado`.

Campos:

- conta a pagar;
- solicitante;
- aprovador;
- status;
- justificativa;
- data de decisao.

Status:

```text
pendente
aprovado
reprovado
cancelado
```

Toda decisao registra evento de risco alto.

## 23. Relatorios

Endpoint:

```text
POST /api/financeiro/relatorios/
```

Tipos:

- `contas_pagar`;
- `contas_receber`;
- `fluxo_caixa`;
- `eventos`.

Formatos:

- `csv`;
- `xlsx`;
- `pdf`.

O backend:

- filtra pelo periodo;
- gera arquivo para download;
- registra evento de exportacao;
- cria `RelatorioGerado` com tipo, formato e parametros.

## 24. Anexos

Anexos financeiros sao gravados em `AnexoFinanceiro`.

Campos:

- empresa;
- arquivo;
- nome original;
- content type;
- tamanho;
- origem_modelo;
- origem_id;
- usuario que enviou.

Acoes implementadas:

- `POST /api/financeiro/contas-pagar/{id}/anexar/`;
- `POST /api/financeiro/contas-receber/{id}/anexar/`.

O upload usa `multipart/form-data` com campo `arquivo`.

## 25. Inteligencia financeira

Modelos:

- `AlertaIA`: mensagem operacional exibivel ao usuario.
- `Anomalia`: evidencia estruturada para analise.
- `PrevisaoIA`: previsao numerica por metrica e horizonte.

Status de analise:

```text
aberto
em_analise
confirmado
descartado
resolvido
```

Tipos de anomalia:

```text
pagamento_duplicado
valor_fora_padrao
comportamento_usuario
inadimplencia
orcamento_estourado
```

Analises implementadas:

- pagamento duplicado por fornecedor, valor, vencimento e documento;
- pagamento fora do padrao historico do fornecedor;
- previsao baseline de caixa para horizonte informado;
- varredura geral que executa duplicidades, fora do padrao e previsao;
- feedback para confirmar, descartar, resolver ou colocar em analise.

## 26. API principal

Documentacao detalhada fica em [api.md](api.md). Resumo:

Autenticacao:

- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/token/verify/`
- `GET /api/auth/me/`

Core:

- `/api/core/empresas/`
- `/api/core/modulos/`
- `/api/core/empresa-modulos/`
- `/api/core/usuarios/`
- `/api/core/perfis/`
- `/api/core/permissoes/`
- `/api/core/perfil-permissoes/`
- `/api/core/usuario-perfis/`
- `/api/core/eventos/`
- `/api/core/notificacoes/`

Financeiro:

- `/api/financeiro/centros-custo/`
- `/api/financeiro/plano-contas/`
- `/api/financeiro/contas-bancarias/`
- `/api/financeiro/clientes/`
- `/api/financeiro/fornecedores/`
- `/api/financeiro/servicos/`
- `/api/financeiro/contas-pagar/`
- `/api/financeiro/contas-receber/`
- `/api/financeiro/movimentacoes/`
- `/api/financeiro/conciliacoes/`
- `/api/financeiro/orcamentos/`
- `/api/financeiro/aprovacoes-pagamento/`
- `/api/financeiro/fluxo-caixa/`
- `/api/financeiro/relatorios/`

Inteligencia:

- `/api/inteligencia/alertas/`
- `/api/inteligencia/anomalias/`
- `/api/inteligencia/previsoes/`

## 27. Paginacao, filtros e busca

A API usa paginacao padrao por pagina.

Parametros comuns:

```text
page
page_size
search
ordering
```

Os viewsets tambem expoem filtros por campos como `empresa`, `status`, `tipo`, `ativo`, `conta_bancaria`, `centro_custo`, `plano_conta`, `usuario`, `perfil`, `modulo` e outros. Os filtros completos estao em [api.md](api.md).

## 28. Comandos de carga e manutencao

### `seed_mvp`

Cria:

- modulos `core`, `financeiro` e `inteligencia`;
- permissoes por modulo, tela e acao;
- perfis padrao.

### `seed_demo`

Cria:

- empresa demo;
- usuario `admin`;
- usuario `demo`;
- modulos instalados;
- cadastros basicos;
- contas a pagar e receber de demonstracao.

### `seed_operacional`

Cria uma massa operacional maior:

- 10 centros de custo;
- 14 planos de conta;
- 5 contas bancarias;
- 20 clientes;
- 20 fornecedores;
- 10 servicos;
- 80 contas a receber;
- 75 contas a pagar;
- 120 movimentacoes financeiras.

### `backup_sqlite`

Copia o banco SQLite atual para `backups/db-YYYYMMDD-HHMMSS.sqlite3`.

## 29. Admin Django

O admin registra os modelos principais:

- Empresa, Modulo, EmpresaModulo;
- Usuario;
- Perfil, Permissao;
- EventLog;
- LoginAttempt;
- Notificacao;
- cadastros financeiros;
- contas a pagar e receber;
- movimentacoes;
- conciliacoes;
- alertas, anomalias e previsoes.

`EventLog` no admin e somente leitura.

## 30. Deploy e producao

Para producao, revisar obrigatoriamente:

- definir `SECRET_KEY` forte;
- usar `DEBUG=False`;
- configurar `ALLOWED_HOSTS`;
- usar PostgreSQL;
- configurar variaveis `POSTGRES_*`;
- habilitar HTTPS;
- usar `SECURE_SSL_REDIRECT=True`;
- usar `SESSION_COOKIE_SECURE=True`;
- usar `CSRF_COOKIE_SECURE=True`;
- avaliar HSTS;
- configurar armazenamento de `MEDIA_ROOT`;
- configurar coleta e servico de arquivos estaticos;
- definir rotina de backup;
- remover ou trocar senhas demo;
- criar usuarios reais e perfis adequados;
- validar permissoes por tela antes de liberar operacao.

## 31. Estado atual do produto

Implementado:

- autenticacao JWT;
- bloqueio por tentativas falhas;
- MFA simples para MVP;
- painel web;
- multiempresa;
- perfis e permissoes;
- cadastros financeiros;
- servicos;
- contas a pagar;
- contas a receber;
- baixas e recebimentos;
- movimentacoes;
- fluxo de caixa;
- DRE gerencial;
- aprovacoes;
- conciliacao CSV;
- relatorios CSV/XLSX/PDF;
- anexos em titulos;
- auditoria imutavel com hash;
- alertas e anomalias;
- previsao baseline;
- dados demo e operacionais;
- Swagger/OpenAPI.

Limitacoes conhecidas do MVP:

- integracao bancaria real ainda nao existe;
- importacao OFX esta no backlog, mas nao implementada;
- exclusao visual controlada ainda e limitada;
- edicao visual completa de todos os cadastros pode evoluir;
- anexos existem na API, mas nao ha fluxo visual completo para todos os casos;
- MFA e simplificado;
- permissoes existem no backend, mas o frontend ainda pode evoluir para esconder acoes por permissao;
- relatorios sao sincronos;
- IA e baseada em heuristicas simples, sem fila e sem modelo treinado.

## 32. Checklist para entrega de mudancas

Antes de publicar alteracoes:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test core financeiro inteligencia --verbosity 2
node --check core\static\frontend\js\app.js
node --check core\static\frontend\js\api.js
node --check core\static\frontend\js\data.js
node --check core\static\frontend\js\ui.js
git status -sb
```
