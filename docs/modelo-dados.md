# Modelo de Dados do MVP

## Core

### empresas

Armazena a unidade contratante do ERP. Todo dado financeiro deve estar associado a uma empresa.

Campos principais:

- razao_social
- nome_fantasia
- cnpj
- status
- timezone
- configuracoes

### usuarios

Usuario autenticavel do sistema, vinculado opcionalmente a uma empresa.

Campos principais:

- username
- email
- empresa
- telefone
- cargo
- mfa_habilitado
- precisa_trocar_senha

### perfis e permissoes

Permitem controle por modulo, tela e acao.

Exemplos de permissoes:

- financeiro.contas_pagar.visualizar
- financeiro.contas_pagar.editar
- financeiro.contas_pagar.baixar
- financeiro.relatorios.exportar
- core.auditoria.visualizar

### modulos e empresa_modulos

Controlam instalacao independente de cada modulo por empresa.

### logs_eventos

Tabela estrategica do produto. Registra cada evento operacional, financeiro, administrativo e automatico.

## Financeiro

### clientes e fornecedores

Cadastros base para contas a receber e contas a pagar.

### centros_custo

Hierarquia de setores, projetos ou unidades.

### plano_contas

Classificacao financeira vinculavel a DRE e fluxo de caixa.

### contas_bancarias

Contas usadas para baixas, recebimentos e conciliacao.

### contas_pagar

Controla titulos de fornecedores, baixa parcial, status, comprovantes e auditoria.

### contas_receber

Controla titulos de clientes, recebimento parcial, atraso, renegociacao e cobranca.

### movimentacoes_financeiras

Entradas e saidas realizadas, geradas por baixas ou lancamentos manuais.

### conciliacoes_bancarias

Linhas de extrato importadas e vinculadas a movimentacoes.

### orcamentos

Planejamento por periodo, centro de custo e plano de contas.

## Inteligencia

### alertas_ia

Alertas exibiveis ao usuario.

### anomalias

Evidencias estruturadas de comportamentos fora do padrao.

### previsoes_ia

Previsoes por metrica, horizonte e modelo.
