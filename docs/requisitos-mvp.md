# Requisitos do MVP

## Objetivo

Entregar a primeira versao operacional do ERP Financeiro Inteligente com controle financeiro essencial, rastreabilidade completa dos eventos e uma camada inicial de analise por IA.

## Escopo incluido

- Cadastro de empresas.
- Cadastro de usuarios.
- Perfis e permissoes por modulo, tela e acao.
- Controle de modulos instalados por empresa.
- Cadastro de clientes e fornecedores.
- Centro de custo hierarquico.
- Plano de contas por empresa.
- Contas bancarias.
- Contas a pagar com baixa parcial e total.
- Contas a receber com recebimento parcial e total.
- Fluxo de caixa previsto e realizado.
- Movimentacoes financeiras.
- Conciliacao bancaria inicial por lancamentos importados.
- Log de eventos para auditoria.
- Alertas de IA para duplicidade e valores fora do padrao.
- Previsao baseline de caixa.
- Dashboard financeiro inicial.

## Escopo fora do MVP

- Fiscal completo.
- Contabil completo.
- RH, estoque, vendas e CRM completos.
- Integracoes bancarias via API em producao.
- WhatsApp/SMS em producao.
- Modelos avancados de machine learning.
- Aplicativo mobile.

## Regras obrigatorias

- Nenhum registro financeiro deve ser apagado definitivamente.
- Toda acao relevante deve gerar `EventLog`.
- Baixa de pagamento ou recebimento exige valor maior que zero.
- Baixas parciais devem manter saldo pendente.
- Alteracao de vencimento, valor, status e exclusao logica deve ser auditada.
- Dados devem ser sempre associados a uma empresa.
- Permissoes devem ser avaliadas por modulo, tela e acao.

## Indicadores iniciais

- Saldo previsto.
- Saldo realizado.
- Total a pagar.
- Total a receber.
- Contas vencidas.
- Inadimplencia.
- Receita do mes.
- Despesa do mes.
- Resultado financeiro.
- Anomalias abertas.
