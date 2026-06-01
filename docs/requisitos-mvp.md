# Requisitos do MVP

## 1. Objetivo

Entregar a primeira versao operacional do ERP Financeiro Inteligente com controle financeiro essencial, multiempresa, rastreabilidade de eventos e uma camada inicial de inteligencia financeira.

## 2. Escopo incluido

- Cadastro de empresas.
- Cadastro de usuarios.
- Perfis e permissoes por modulo, tela e acao.
- Controle de modulos instalados por empresa.
- Cadastro de clientes.
- Cadastro de fornecedores.
- Cadastro de servicos.
- Centro de custo hierarquico.
- Plano de contas por empresa.
- Contas bancarias.
- Contas a pagar com baixa parcial e total.
- Contas a receber com recebimento parcial e total.
- Renegociacao de contas a receber.
- Cancelamento auditado de contas a pagar e receber.
- Exclusao logica de contas a pagar e receber.
- Anexos financeiros em titulos.
- Fluxo de caixa previsto e realizado.
- Movimentacoes financeiras.
- DRE gerencial.
- Conciliacao bancaria por CSV.
- Sugestao e conciliacao manual.
- Orcamentos.
- Aprovacoes de pagamento.
- Log de eventos para auditoria.
- Notificacoes.
- Relatorios CSV, XLSX e PDF.
- Alertas de IA para duplicidade e valores fora do padrao.
- Previsao baseline de caixa.
- Dashboard financeiro.
- Painel web responsivo.
- API REST com Swagger.

## 3. Escopo fora do MVP

- Fiscal completo.
- Contabil completo.
- RH, estoque, vendas e CRM completos.
- Integracoes bancarias via API em producao.
- Importacao OFX.
- WhatsApp/SMS em producao.
- Fila assincrona para relatorios e IA.
- Modelos avancados de machine learning.
- Aplicativo mobile.
- MFA real com provedor externo.
- Controle visual completo de permissao no frontend.

## 4. Regras obrigatorias

- Nenhum registro financeiro sensivel deve ser apagado definitivamente quando houver regra de exclusao logica.
- Toda acao relevante deve gerar `EventLog`.
- `EventLog` deve ser imutavel.
- Baixa de pagamento ou recebimento exige valor maior que zero.
- Baixas parciais devem manter saldo pendente.
- Alteracao de vencimento, valor, status e exclusao logica deve ser auditada.
- Dados operacionais devem ser associados a uma empresa.
- Usuario comum deve acessar somente dados da propria empresa.
- Superuser pode acessar todas as empresas.
- Permissoes devem ser avaliadas por modulo, tela e acao.
- Relatorios exportados devem gerar evento.
- Login com sucesso/falha deve gerar evento.
- Tentativas de login falhas devem poder bloquear temporariamente o acesso.

## 5. Indicadores iniciais

- Saldo previsto.
- Saldo realizado.
- Total a pagar.
- Total a receber.
- Contas a pagar hoje.
- Contas a receber hoje.
- Contas vencidas.
- Inadimplencia.
- Receita do periodo.
- Despesa do periodo.
- Resultado financeiro.
- Titulos abertos a pagar.
- Titulos abertos a receber.
- Anomalias abertas.
- Alertas por nivel de risco.
- DRE por linha gerencial.
- Resultado por centro de custo.
- Resultado por plano de contas.

## 6. Estado de implementacao

Concluido no MVP:

- core administrativo;
- app financeiro operacional;
- app de inteligencia inicial;
- frontend web;
- API REST;
- Swagger;
- autenticacao JWT;
- multiempresa;
- permissoes;
- auditoria;
- relatorios;
- comandos de seed;
- backup SQLite local.

Pendente ou recomendado para proximas versoes:

- importacao OFX;
- integracao bancaria real;
- tarefas assincronas;
- permissao visual completa;
- relatorios grandes em background;
- dashboards multiempresa avancados;
- modelos de IA mais sofisticados;
- deploy produtivo com PostgreSQL e HTTPS.
