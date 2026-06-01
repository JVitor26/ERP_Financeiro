# Documentacao do Sistema ERP Financeiro Inteligente

## 1. Visao geral

O ERP Financeiro Inteligente e um sistema web para controle financeiro multiempresa. Ele centraliza cadastros operacionais, contas a pagar, contas a receber, movimentacoes bancarias, fluxo de caixa, DRE gerencial, aprovacoes, auditoria, notificacoes, relatorios e uma camada inicial de inteligencia financeira.

O sistema foi construido com:

- Backend em Django 5 e Django REST Framework.
- Autenticacao por JWT.
- Banco SQLite para ambiente local.
- Estrutura preparada para PostgreSQL em producao.
- Frontend web em HTML, CSS e JavaScript puro.
- API documentada em Swagger.

## 2. Acessos locais

URLs principais:

- Painel web: `http://127.0.0.1:8000/`
- Admin Django: `http://127.0.0.1:8000/admin/`
- API docs: `http://127.0.0.1:8000/api/docs/`
- Token JWT: `POST /api/auth/token/`

Usuarios locais:

- Superuser: `admin` / `Admin@123`
- Usuario demo: `demo` / `Demo@123`

## 3. Como executar

Ambiente local com virtualenv:

```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py seed_mvp
.\.venv\Scripts\python.exe manage.py seed_operacional
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8000
```

Testes:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test core financeiro inteligencia --verbosity 2
```

Backup SQLite:

```powershell
.\.venv\Scripts\python.exe manage.py backup_sqlite
```

## 4. Organizacao do projeto

```text
erp_financeiro/       Configuracoes, URLs principais e WSGI/ASGI
core/                 Empresas, usuarios, perfis, permissoes, auditoria e autenticacao
financeiro/           Cadastros financeiros, contas, DRE, fluxo, relatorios e conciliacao
inteligencia/         Alertas, anomalias e previsoes
templates/frontend/   Estrutura HTML do painel web
core/static/frontend/ CSS e JavaScript do painel
docs/                 Documentacao do produto e do projeto
sql/                  Modelo SQL conceitual
```

## 5. Autenticacao e seguranca

O login do painel usa JWT via endpoint `/api/auth/token/`.

O endpoint `/api/auth/me/` retorna os dados do usuario autenticado e e usado pelo painel para identificar:

- usuario logado;
- empresa vinculada;
- permissao administrativa;
- informacoes de sessao.

Regras importantes:

- Superuser acessa todos os dados.
- Usuarios comuns ficam restritos a propria empresa.
- Escrita em areas sensiveis depende de permissoes por acao.
- Tentativas de login falhas sao registradas e podem gerar bloqueio temporario.
- Eventos operacionais relevantes sao registrados em auditoria.

## 6. Multiempresa

Cada registro financeiro pertence a uma empresa. A regra de escopo esta centralizada em mixins de queryset:

- superuser ve todas as empresas;
- usuario comum ve apenas registros da empresa vinculada;
- criacoes feitas por usuario comum herdam a empresa do usuario.

Entidades ligadas a empresa:

- clientes;
- fornecedores;
- servicos;
- contas bancarias;
- centros de custo;
- plano de contas;
- contas a pagar;
- contas a receber;
- movimentacoes;
- conciliacoes;
- relatorios;
- notificacoes;
- alertas e previsoes.

## 7. Modulo Core

O modulo `core` cuida da base administrativa do sistema.

Principais entidades:

- `Empresa`: cadastro das empresas/tenants.
- `Usuario`: usuario customizado com vinculo opcional a empresa.
- `Modulo`: capacidades instalaveis do sistema.
- `EmpresaModulo`: modulos ativos por empresa.
- `Perfil`: agrupamento de permissoes.
- `Permissao`: permissao por modulo, tela e acao.
- `PerfilPermissao`: vinculo entre perfil e permissao.
- `UsuarioPerfil`: perfis concedidos a usuarios.
- `EventLog`: trilha de auditoria imutavel.
- `Notificacao`: fila de notificacoes operacionais.

## 8. Modulo Financeiro

O modulo `financeiro` contem a operacao principal.

### Cadastros

Na tela **Cadastros** e possivel criar e consultar:

- clientes;
- fornecedores;
- servicos;
- contas bancarias;
- centros de custo;
- plano de contas.

Campos principais:

- Cliente/Fornecedor: nome, tipo de pessoa, documento, email, telefone e status.
- Servico: codigo, nome, descricao, valor padrao e plano de contas.
- Conta bancaria: banco, agencia, numero, descricao, saldo inicial e status.
- Centro de custo: codigo, nome, pai e status.
- Plano de contas: codigo, nome, tipo, pai, vinculo com DRE e fluxo de caixa.

### Contas a receber

Representa titulos a receber de clientes.

Campos importantes:

- cliente;
- descricao;
- data de emissao;
- data de vencimento;
- valor original;
- descontos, juros, multa e acrescimos;
- centro de custo;
- plano de contas;
- conta bancaria;
- status;
- valor recebido;
- saldo pendente.

Acoes:

- criar recebivel;
- registrar recebimento total ou parcial;
- renegociar;
- cancelar via API;
- anexar arquivo via API.

### Contas a pagar

Representa titulos de fornecedores.

Campos importantes:

- fornecedor;
- descricao;
- data de emissao;
- data de vencimento;
- valor original;
- descontos, juros, multa e acrescimos;
- numero de documento;
- nota fiscal;
- centro de custo;
- plano de contas;
- conta bancaria;
- status;
- valor pago;
- saldo pendente.

Acoes:

- criar pagamento;
- solicitar aprovacao;
- aprovar ou reprovar pagamento;
- baixar pagamento total ou parcial;
- cancelar via API;
- anexar comprovante via API.

### Movimentacoes financeiras

Movimentacoes representam entradas e saidas realizadas.

Elas podem ser criadas por:

- baixa de conta a pagar;
- recebimento de conta a receber;
- carga operacional;
- integracoes futuras.

Campos principais:

- tipo: entrada ou saida;
- descricao;
- data do movimento;
- data de competencia;
- valor;
- conta bancaria;
- centro de custo;
- plano de contas;
- origem;
- conciliado.

## 9. DRE Gerencial

A DRE fica no painel de visao geral.

Ela usa as movimentacoes financeiras realizadas no periodo selecionado. A estrutura atual e:

- `+ Receita bruta`
- `- Deducoes, impostos, taxas e comissoes`
- `= Receita liquida`
- `- Custos variaveis`
- `= Margem de contribuicao`
- `- Despesas operacionais`
- `= Resultado operacional`
- `- Investimentos e outras saidas`
- `= Lucro / prejuizo`

### Abertura por linha principal

As linhas principais da DRE sao clicaveis quando possuem sublinhas. Ao clicar:

- os itens secundarios daquela linha desaparecem;
- a DRE fica resumida naquele grupo;
- ao clicar novamente, a abertura volta a aparecer.

Isso vale para receitas, deducoes, custos, despesas e investimentos/outros quando houver movimentacao.

### Custos dentro da DRE

Os custos aparecem dentro de `Custos variaveis`, agrupados por plano de contas do tipo `custo`.

Exemplo:

- `3.1 - Custo de entrega`
- `3.2 - Manutencao predial`

### Despesas dentro da DRE

As despesas aparecem dentro de `Despesas operacionais`, agrupadas por plano de contas do tipo `despesa`.

Exemplo:

- `2.1 - Fornecedores operacionais`
- `2.2 - Despesas administrativas`
- `2.3 - Marketing e vendas`

### Receitas dentro da DRE

As receitas aparecem dentro de `Receita bruta`, agrupadas por plano de contas com entradas realizadas.

### Cores e sinais

- `+` em verde: entrada/receita.
- `-` em vermelho: saida, deducao, custo ou despesa.
- `=` em verde quando o resultado e positivo.
- `=` em vermelho quando o resultado e negativo.

### Centros de custo

A DRE tambem mostra uma tabela por centro de custo com:

- entradas;
- saidas;
- resultado;
- quantidade de transacoes.

### Plano de contas

A abertura por plano de contas mostra:

- codigo;
- nome;
- tipo;
- entradas;
- saidas;
- resultado.

## 10. Botao de ocultar valores

No topo do painel existe um botao com icone de olho para ocultar ou mostrar valores.

Quando ativado, os valores monetarios aparecem mascarados como:

```text
R$ ***
```

O recurso se aplica a:

- KPIs do dashboard;
- agenda de vencimentos;
- DRE;
- contas a receber;
- contas a pagar;
- aprovacoes;
- cadastros com valores;
- previsoes.

O estado fica salvo no navegador local.

## 11. Aprovacoes

A tela **Aprovacoes** centraliza solicitacoes de pagamento que precisam de decisao.

Fluxo:

1. Usuario solicita aprovacao em uma conta a pagar.
2. A conta muda para `em_aprovacao`.
3. Um aprovador aprova ou reprova.
4. Se aprovada, a conta fica `agendada`.
5. Se reprovada, a conta fica `reprovado`.

Toda decisao gera evento de auditoria.

## 12. Auditoria

A tela **Auditoria** exibe eventos registrados no `EventLog`.

Eventos incluem:

- criacao;
- alteracao;
- exclusao logica;
- baixa;
- aprovacao;
- reprovacao;
- exportacao;
- acesso sensivel;
- alerta de sistema;
- alerta de IA;
- integracao.

O log e imutavel:

- nao pode ser alterado depois de criado;
- nao pode ser excluido;
- possui hash de evento e hash anterior para rastreabilidade.

## 13. Inteligencia financeira

O modulo `inteligencia` contem:

- alertas;
- anomalias;
- previsoes.

A tela permite:

- executar varredura;
- gerar previsao baseline de caixa;
- confirmar ou descartar anomalias.

## 14. Relatorios

A tela **Relatorios** exporta dados auditados.

Tipos disponiveis:

- fluxo de caixa;
- contas a receber;
- contas a pagar;
- eventos de auditoria.

Formatos:

- CSV;
- XLSX;
- PDF.

Toda exportacao gera evento de auditoria.

## 15. Endpoints principais

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
- `/api/core/eventos/`
- `/api/core/notificacoes/`

Financeiro:

- `/api/financeiro/clientes/`
- `/api/financeiro/fornecedores/`
- `/api/financeiro/servicos/`
- `/api/financeiro/contas-bancarias/`
- `/api/financeiro/centros-custo/`
- `/api/financeiro/plano-contas/`
- `/api/financeiro/contas-receber/`
- `/api/financeiro/contas-pagar/`
- `/api/financeiro/movimentacoes/`
- `/api/financeiro/conciliacoes/`
- `/api/financeiro/orcamentos/`
- `/api/financeiro/aprovacoes-pagamento/`
- `/api/financeiro/fluxo-caixa/`
- `/api/financeiro/fluxo-caixa/dashboard/`
- `/api/financeiro/fluxo-caixa/dre/`
- `/api/financeiro/relatorios/`

Inteligencia:

- `/api/inteligencia/alertas/`
- `/api/inteligencia/anomalias/`
- `/api/inteligencia/previsoes/`

## 16. Comandos de carga

### `seed_mvp`

Cria:

- modulos padrao;
- permissoes;
- perfis de acesso.

### `seed_demo`

Cria:

- empresa demo;
- usuarios demo;
- alguns cadastros e titulos basicos.

### `seed_operacional`

Cria uma base operacional mais completa:

- varios clientes;
- varios fornecedores;
- servicos;
- planos de contas;
- centros de custo;
- contas bancarias;
- contas a receber;
- contas a pagar;
- movimentacoes financeiras.

O comando usa `update_or_create`, portanto pode ser rodado novamente sem duplicar os registros principais.

## 17. Regras financeiras importantes

### Valores

- Valor original de conta deve ser maior que zero.
- Valores de desconto, juros, multa e acrescimo nao podem ser negativos.
- Desconto nao pode ser maior que o valor original.
- Data de vencimento nao pode ser anterior a data de emissao.

### Baixas

- Conta paga nao pode receber baixa novamente.
- Conta cancelada nao pode ser baixada.
- Baixa nao pode ultrapassar saldo pendente.
- Baixa parcial atualiza status para pago parcial ou recebido parcial.

### Aprovacoes

- Conta com aprovacao pendente nao pode ser baixada.
- Conta aprovada passa para agendada.
- Conta reprovada passa para reprovado.

### Cancelamento

- Conta paga/recebida nao pode ser cancelada pela regra de servico.
- Cancelamentos precisam de justificativa na API.

## 18. Permissoes

O sistema usa permissoes por modulo, tela e acao.

Formato:

```text
financeiro.contas_pagar.editar
financeiro.contas_pagar.baixar
financeiro.contas_receber.receber
financeiro.relatorios.exportar
```

Acoes comuns:

- visualizar;
- editar;
- excluir;
- baixar;
- receber;
- aprovar;
- exportar;
- importar;
- conciliar.

Perfis padrao:

- Administrador;
- Financeiro;
- Diretoria;
- Auditor.

## 19. Manutencao e validacao

Antes de entregar mudancas:

```powershell
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py test core financeiro inteligencia --verbosity 2
node --check core\static\frontend\js\app.js
node --check core\static\frontend\js\data.js
node --check core\static\frontend\js\ui.js
```

Para verificar a API:

```powershell
.\.venv\Scripts\python.exe manage.py shell
```

Use o `APIClient` do DRF ou acesse a documentacao Swagger em `/api/docs/`.

## 20. Estado atual do produto

Funcionalidades prontas:

- login JWT;
- painel executivo;
- DRE completa com abre/fecha;
- ocultar/mostrar valores;
- cadastros operacionais;
- contas a receber;
- contas a pagar;
- aprovacoes;
- auditoria;
- relatorios;
- dados operacionais de demonstracao;
- API REST;
- admin Django.

Pontos que podem evoluir:

- edicao visual de cadastros ja existentes;
- exclusao visual controlada;
- conciliacao bancaria via tela completa;
- anexos pelo frontend;
- dashboards por empresa em ambiente multiempresa real;
- permissao visual por perfil;
- filtros avancados por centro de custo e plano de contas;
- integracoes bancarias reais;
- filas e tarefas assincronas para IA e relatorios.
