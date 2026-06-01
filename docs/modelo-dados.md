# Modelo de dados completo

Este documento descreve os modelos Django implementados no MVP. Para o desenho SQL conceitual, consulte `sql/schema_mvp.sql`.

## 1. Convencoes

### Campos de auditoria temporal

Modelos que herdam `TimeStampedModel` possuem:

- `criado_em`;
- `atualizado_em`.

### Escopo multiempresa

A maioria dos modelos operacionais possui relacionamento com `Empresa`. O isolamento de dados e aplicado nos viewsets por `EmpresaScopedQuerysetMixin`.

### Valores monetarios

Valores financeiros usam `DecimalField(max_digits=14, decimal_places=2)`.

## 2. Core

### Empresa

Tabela logica de tenants do sistema.

Campos:

- `razao_social`: nome juridico.
- `nome_fantasia`: nome de exibicao.
- `cnpj`: unico, opcional.
- `status`: `ativa`, `inativa` ou `suspensa`.
- `timezone`: padrao `America/Cuiaba`.
- `configuracoes`: JSON livre.
- `criado_em`, `atualizado_em`.

Ordenacao:

- `razao_social`.

### Modulo

Representa capacidades instalaveis do ERP.

Campos:

- `codigo`: slug unico.
- `nome`.
- `descricao`.
- `ativo`.
- `schema_configuracao`: JSON com configuracao esperada.
- `criado_em`, `atualizado_em`.

Ordenacao:

- `nome`.

### EmpresaModulo

Relaciona empresa e modulo instalado.

Campos:

- `empresa`;
- `modulo`;
- `ativo`;
- `instalado_em`;
- `configuracoes`;
- `criado_em`, `atualizado_em`.

Restricao:

- `empresa` + `modulo` precisa ser unico.

### Usuario

Usuario customizado baseado em `AbstractUser`.

Campos adicionais:

- `empresa`: opcional, protegida contra exclusao.
- `telefone`;
- `cargo`;
- `mfa_habilitado`;
- `precisa_trocar_senha`;
- `ultimo_ip`.

Campos herdados relevantes:

- `username`;
- `email`;
- `first_name`;
- `last_name`;
- `password`;
- `is_active`;
- `is_staff`;
- `is_superuser`;
- `last_login`;
- `date_joined`.

Ordenacao:

- `username`.

### Perfil

Agrupa permissoes por empresa ou de forma global.

Campos:

- `empresa`: opcional; `null` indica perfil de sistema.
- `nome`;
- `descricao`;
- `sistema`;
- `criado_em`, `atualizado_em`.

Restricao:

- `empresa` + `nome` precisa ser unico.

Ordenacao:

- `nome`.

### Permissao

Permissao granular por modulo, tela e acao.

Campos:

- `codigo`: slug unico, exemplo `financeiro.contas_pagar.baixar`.
- `modulo`: opcional.
- `tela`;
- `acao`;
- `descricao`;
- `sensivel`;
- `criado_em`, `atualizado_em`.

Ordenacao:

- `modulo__codigo`, `tela`, `acao`.

### PerfilPermissao

Vincula perfil e permissao.

Campos:

- `perfil`;
- `permissao`;
- `criado_em`, `atualizado_em`.

Restricao:

- `perfil` + `permissao` precisa ser unico.

### UsuarioPerfil

Vincula usuario e perfil.

Campos:

- `usuario`;
- `perfil`;
- `criado_em`, `atualizado_em`.

Restricao:

- `usuario` + `perfil` precisa ser unico.

### EventLog

Trilha de auditoria imutavel.

Campos:

- `event_id`: UUID unico.
- `tipo_evento`: `criacao`, `alteracao`, `exclusao_logica`, `baixa`, `aprovacao`, `reprovacao`, `exportacao`, `acesso_sensivel`, `alerta_sistema`, `alerta_ia`, `integracao`.
- `usuario`: opcional.
- `empresa`: opcional.
- `modulo`;
- `tela`;
- `acao`;
- `registro_modelo`;
- `registro_id`;
- `valor_anterior`: JSON.
- `valor_novo`: JSON.
- `ip`;
- `dispositivo`;
- `origem`;
- `justificativa`;
- `nivel_risco`: `baixo`, `medio`, `alto`, `critico`.
- `hash_anterior`;
- `hash_evento`;
- `metadados`: JSON.
- `criado_em`.

Indices:

- `empresa`, `criado_em`;
- `tipo_evento`, `nivel_risco`;
- `modulo`, `acao`;
- `registro_modelo`, `registro_id`;
- `hash_evento`.

Regras:

- nao pode ser alterado depois de criado;
- nao pode ser excluido;
- `hash_anterior` aponta para o ultimo evento;
- `hash_evento` e SHA-256 dos dados do evento.

### LoginAttempt

Controle de tentativas falhas de login.

Campos:

- `username`;
- `ip`;
- `falhas`;
- `bloqueado_ate`;
- `ultimo_evento`.

Restricao:

- `username` + `ip` precisa ser unico.

Indice:

- `username`, `ip`, `bloqueado_ate`.

Regras:

- `registrar_falha` incrementa falhas e bloqueia ao atingir limite.
- `limpar` zera falhas e desbloqueia.

### Notificacao

Fila de mensagens operacionais.

Campos:

- `empresa`;
- `usuario`: opcional.
- `canal`: `sistema`, `email`, `whatsapp`, `sms`, `push`.
- `titulo`;
- `mensagem`;
- `status`: `pendente`, `enviada`, `falhou`, `lida`.
- `enviado_em`;
- `lido_em`;
- `metadados`;
- `criado_em`, `atualizado_em`.

Ordenacao:

- `-criado_em`.

## 3. Financeiro

### Tipos e status

`TipoPessoa`:

- `fisica`;
- `juridica`.

`TipoPlanoConta`:

- `receita`;
- `despesa`;
- `custo`;
- `investimento`;
- `imposto`;
- `taxa`;
- `comissao`;
- `repasse`;
- `financiamento`;
- `emprestimo`.

`TipoMovimentacao`:

- `entrada`;
- `saida`.

`StatusContaPagar`:

- `aberto`;
- `a_vencer`;
- `vencido`;
- `pago`;
- `pago_parcial`;
- `cancelado`;
- `em_aprovacao`;
- `reprovado`;
- `agendado`.

`StatusContaReceber`:

- `aberto`;
- `a_vencer`;
- `vencido`;
- `recebido`;
- `recebido_parcial`;
- `cancelado`;
- `renegociado`;
- `em_cobranca`;
- `judicial`;
- `protestado`.

`StatusConciliacao`:

- `pendente`;
- `sugerida`;
- `conciliada`;
- `divergente`;
- `duplicada`.

`StatusAprovacao`:

- `pendente`;
- `aprovado`;
- `reprovado`;
- `cancelado`.

`StatusRelatorio`:

- `pendente`;
- `processando`;
- `pronto`;
- `falhou`.

### CentroCusto

Campos:

- `empresa`;
- `codigo`;
- `nome`;
- `pai`: hierarquia opcional;
- `ativo`;
- `criado_em`, `atualizado_em`.

Restricao:

- `empresa` + `codigo` precisa ser unico.

Ordenacao:

- `codigo`, `nome`.

### PlanoConta

Campos:

- `empresa`;
- `codigo`;
- `nome`;
- `tipo`;
- `pai`: hierarquia opcional;
- `vincula_dre`;
- `vincula_fluxo_caixa`;
- `ativo`;
- `criado_em`, `atualizado_em`.

Restricao:

- `empresa` + `codigo` precisa ser unico.

Ordenacao:

- `codigo`, `nome`.

### ContaBancaria

Campos:

- `empresa`;
- `banco`;
- `agencia`;
- `numero`;
- `descricao`;
- `saldo_inicial`;
- `ativa`;
- `criado_em`, `atualizado_em`.

Ordenacao:

- `banco`, `numero`.

### Cliente

Campos:

- `empresa`;
- `nome`;
- `tipo_pessoa`;
- `documento`;
- `email`;
- `telefone`;
- `ativo`;
- `metadados`;
- `criado_em`, `atualizado_em`.

Indice:

- `empresa`, `documento`.

Ordenacao:

- `nome`.

### Fornecedor

Campos iguais aos de `Cliente`.

Indice:

- `empresa`, `documento`.

Ordenacao:

- `nome`.

### Servico

Campos:

- `empresa`;
- `codigo`;
- `nome`;
- `descricao`;
- `valor_padrao`;
- `plano_conta`;
- `ativo`;
- `metadados`;
- `criado_em`, `atualizado_em`.

Restricao:

- `empresa` + `codigo` precisa ser unico quando `codigo` nao esta vazio.

Indice:

- `empresa`, `nome`.

Ordenacao:

- `nome`.

### LancamentoFinanceiroBase

Base abstrata de contas a pagar e a receber.

Campos:

- `empresa`;
- `descricao`;
- `data_emissao`;
- `data_vencimento`;
- `valor_original`;
- `desconto`;
- `juros`;
- `multa`;
- `acrescimo`;
- `centro_custo`;
- `plano_conta`;
- `conta_bancaria`;
- `observacao`;
- `responsavel`;
- `excluido_logicamente`;
- `excluido_em`;
- `excluido_por`;
- `criado_em`, `atualizado_em`.

Propriedades e regras:

- `valor_total = valor_original + juros + multa + acrescimo - desconto`;
- valores monetarios nao podem ser negativos;
- `valor_original` precisa ser maior que zero;
- vencimento nao pode ser anterior a emissao;
- desconto nao pode ser maior que valor original.

### ContaPagar

Campos especificos:

- `fornecedor`;
- `numero_documento`;
- `nota_fiscal`;
- `valor_pago`;
- `forma_pagamento`;
- `status`;
- `data_baixa`;
- `baixado_por`;
- `comprovante`.

Propriedades:

- `saldo_pendente = max(valor_total - valor_pago, 0)`.

Regras:

- `valor_pago` nao pode ser negativo;
- `valor_pago` nao pode exceder `valor_total`;
- status `pago` exige saldo quitado;
- baixa parcial muda status para `pago_parcial`;
- baixa total muda status para `pago`.

Indices:

- `empresa`, `status`, `data_vencimento`;
- `empresa`, `fornecedor`, `numero_documento`.

Ordenacao:

- `data_vencimento`, `fornecedor__nome`.

### ContaReceber

Campos especificos:

- `cliente`;
- `contrato`;
- `parcela`;
- `valor_recebido`;
- `honorarios`;
- `forma_recebimento`;
- `status`;
- `data_recebimento`;
- `recebido_por`;
- `conta_original`;
- `renegociado_em`;
- `renegociado_por`.

Propriedades:

- `valor_total = valor_original + juros + multa + acrescimo - desconto + honorarios`;
- `saldo_pendente = max(valor_total - valor_recebido, 0)`;
- `dias_atraso` retorna zero para conta nao vencida, recebida ou cancelada.

Regras:

- `valor_recebido` e `honorarios` nao podem ser negativos;
- `valor_recebido` nao pode exceder `valor_total`;
- status `recebido` exige saldo quitado;
- recebimento parcial muda status para `recebido_parcial`;
- recebimento total muda status para `recebido`.

Indices:

- `empresa`, `status`, `data_vencimento`;
- `empresa`, `cliente`, `contrato`.

Ordenacao:

- `data_vencimento`, `cliente__nome`.

### MovimentacaoFinanceira

Campos:

- `empresa`;
- `tipo`;
- `descricao`;
- `data_movimento`;
- `data_competencia`;
- `valor`;
- `conta_bancaria`;
- `centro_custo`;
- `plano_conta`;
- `origem_modelo`;
- `origem_id`;
- `conciliado`;
- `criado_em`, `atualizado_em`.

Indices:

- `empresa`, `tipo`, `data_movimento`;
- `origem_modelo`, `origem_id`.

Ordenacao:

- `-data_movimento`, `-criado_em`.

### ConciliacaoBancaria

Campos:

- `empresa`;
- `conta_bancaria`;
- `data_movimento`;
- `valor`;
- `historico`;
- `documento`;
- `status`;
- `movimentacao`;
- `metadados`;
- `criado_em`, `atualizado_em`.

Indice:

- `empresa`, `status`, `data_movimento`.

Ordenacao:

- `-data_movimento`, `-criado_em`.

### Orcamento

Campos:

- `empresa`;
- `ano`;
- `mes`;
- `centro_custo`;
- `plano_conta`;
- `valor_previsto`;
- `valor_realizado`;
- `criado_em`, `atualizado_em`.

Restricao:

- `empresa`, `ano`, `mes`, `centro_custo`, `plano_conta` precisam formar combinacao unica.

Ordenacao:

- `ano`, `mes`.

### AprovacaoPagamento

Campos:

- `conta_pagar`;
- `solicitante`;
- `aprovador`;
- `status`;
- `justificativa`;
- `decidido_em`;
- `criado_em`, `atualizado_em`.

Ordenacao:

- `-criado_em`.

### RelatorioGerado

Campos:

- `empresa`;
- `usuario`;
- `tipo`;
- `formato`;
- `status`;
- `parametros`;
- `arquivo`;
- `erro`;
- `criado_em`, `atualizado_em`.

Indice:

- `empresa`, `tipo`, `formato`, `criado_em`.

Ordenacao:

- `-criado_em`.

### AnexoFinanceiro

Campos:

- `empresa`;
- `arquivo`;
- `nome_original`;
- `content_type`;
- `tamanho`;
- `origem_modelo`;
- `origem_id`;
- `enviado_por`;
- `criado_em`, `atualizado_em`.

Indice:

- `empresa`, `origem_modelo`, `origem_id`.

Ordenacao:

- `-criado_em`.

## 4. Inteligencia

### StatusAnaliseIA

- `aberto`;
- `em_analise`;
- `confirmado`;
- `descartado`;
- `resolvido`.

### TipoAnomalia

- `pagamento_duplicado`;
- `valor_fora_padrao`;
- `comportamento_usuario`;
- `inadimplencia`;
- `orcamento_estourado`.

### AlertaIA

Campos:

- `empresa`;
- `titulo`;
- `mensagem`;
- `nivel_risco`;
- `status`;
- `origem_modelo`;
- `origem_id`;
- `score`;
- `metadados`;
- `criado_em`, `atualizado_em`.

Indice:

- `empresa`, `status`, `nivel_risco`.

Ordenacao:

- `-criado_em`.

### Anomalia

Campos:

- `empresa`;
- `tipo`;
- `descricao`;
- `nivel_risco`;
- `status`;
- `entidade_modelo`;
- `entidade_id`;
- `evidencia`;
- `criado_em`, `atualizado_em`.

Indice:

- `empresa`, `tipo`, `status`.

Ordenacao:

- `-criado_em`.

### PrevisaoIA

Campos:

- `empresa`;
- `nome`;
- `data_referencia`;
- `horizonte_dias`;
- `metrica`;
- `valor_previsto`;
- `confianca`;
- `modelo`;
- `parametros`;
- `criado_em`, `atualizado_em`.

Indice:

- `empresa`, `metrica`, `data_referencia`.

Ordenacao:

- `-data_referencia`, `metrica`.

## 5. Relacionamentos principais

```text
Empresa 1:N Usuario
Empresa 1:N Perfil
Empresa 1:N EmpresaModulo
Modulo  1:N EmpresaModulo
Modulo  1:N Permissao
Perfil  N:N Permissao via PerfilPermissao
Usuario N:N Perfil via UsuarioPerfil
Empresa 1:N EventLog
Empresa 1:N Notificacao

Empresa 1:N CentroCusto
Empresa 1:N PlanoConta
Empresa 1:N ContaBancaria
Empresa 1:N Cliente
Empresa 1:N Fornecedor
Empresa 1:N Servico
Fornecedor 1:N ContaPagar
Cliente    1:N ContaReceber
ContaPagar 1:N AprovacaoPagamento
ContaBancaria 1:N MovimentacaoFinanceira
MovimentacaoFinanceira 1:N ConciliacaoBancaria

Empresa 1:N AlertaIA
Empresa 1:N Anomalia
Empresa 1:N PrevisaoIA
```
