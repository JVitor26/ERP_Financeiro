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

## 5. Core — novos modelos

### MFASecret

Armazena o secret TOTP e os backup codes do usuario.

Campos:

- `usuario`: OneToOne com o usuario.
- `secret`: secret TOTP em base32.
- `ativado_em`: `null` enquanto nao confirmado.
- `backup_codes`: JSONField com lista de codigos em texto puro.
- `criado_em`, `atualizado_em`.

### HistoricoSenha

Armazena hashes de senhas anteriores para impedir reutilizacao.

Campos:

- `usuario`: FK para o usuario.
- `senha_hash`: hash bcrypt da senha anterior.
- `criado_em`.

---

## 6. Financeiro avancado

### PeriodicidadeChoices

- `diaria`, `semanal`, `mensal`, `trimestral`, `semestral`, `anual`.

### StatusRecorrencia

- `ativa`, `pausada`, `cancelada`, `encerrada`.

### RecorrenciaFinanceira

Campos:

- `empresa`;
- `tipo`: `pagar`, `receber`;
- `descricao`;
- `valor`;
- `periodicidade`;
- `data_inicio`, `data_fim` (null = indeterminado);
- `dia_vencimento`: dia do mes para periodicidades mensais e superiores;
- `plano_conta`, `centro_custo`, `conta_bancaria`;
- `fornecedor`, `cliente`;
- `status`;
- `total_gerado`: contador de lancamentos gerados (somente leitura);
- `ultima_geracao`;
- `responsavel`;
- `observacao`;
- `criado_em`, `atualizado_em`.

Metodo: `proxima_data_vencimento()` — calcula a proxima data considerando periodicidade e `dia_vencimento`.

Indice: `empresa`, `status`, `tipo`.

### PeriodoFechamento

Campos:

- `empresa`;
- `ano`, `mes`;
- `status`: `aberto`, `fechado`, `reaberto`;
- `fechado_em`, `fechado_por`;
- `reaberto_em`, `reaberto_por`;
- `justificativa`;
- `criado_em`, `atualizado_em`.

Restricao: `empresa` + `ano` + `mes` precisa ser unico.

### RateioLancamento

Distribui um lancamento por centro de custo ou plano de conta.

Campos:

- `empresa`;
- `origem_modelo`, `origem_id`: identificam o lancamento de origem;
- `centro_custo`, `plano_conta`;
- `percentual`: 0,00 a 100,00;
- `valor`;
- `observacao`;
- `criado_em`, `atualizado_em`.

Metodo de classe: `total_percentual_da_origem()` — soma os percentuais de uma mesma origem.

Indice: `empresa`, `origem_modelo`, `origem_id`.

### AlcadaAprovacao

Regra de aprovacao por valor ou contexto.

Campos:

- `empresa`;
- `nome`;
- `valor_minimo`, `valor_maximo` (null = sem limite);
- `centro_custo`, `plano_conta`, `fornecedor`;
- `tipo_aprovacao`: `sequencial`, `paralela`;
- `prazo_aprovacao_horas`;
- `ativo`;
- `criado_em`, `atualizado_em`.

### AlcadaAprovador

Aprovadores vinculados a uma alcada.

Campos:

- `alcada`;
- `usuario`;
- `ordem`: para aprovacao sequencial;
- `criado_em`, `atualizado_em`.

Restricao: `alcada` + `usuario` precisa ser unico.

### CredencialBancaria

Campos:

- `empresa`;
- `banco`;
- `descricao`;
- `tipo_integracao`: `api`, `ofx`, `remessa`;
- `client_id`, `client_secret` (write-only);
- `certificado`: arquivo de certificado digital;
- `conta_bancaria`;
- `ativa`;
- `configuracoes`, `metadados`;
- `criado_em`, `atualizado_em`.

### ImportacaoOFX

Campos:

- `empresa`;
- `conta_bancaria`;
- `arquivo`, `nome_arquivo`;
- `status`: `pendente`, `processando`, `processado`, `erro`;
- `total_lancamentos`, `lancamentos_importados`, `lancamentos_duplicados`;
- `data_inicio_extrato`, `data_fim_extrato`;
- `erro`;
- `importado_por`;
- `criado_em`, `atualizado_em`.

### RegraConciliacao

Campos:

- `empresa`;
- `nome`;
- `campo_comparacao`: `valor`, `data`, `documento`, `historico`;
- `operador`: `igual`, `contem`, `comeca_com`, `regex`;
- `valor_referencia`;
- `peso`;
- `ativa`;
- `auto_conciliar_acima`;
- `criado_em`, `atualizado_em`.

### CobrancaFinanceira

Campos:

- `empresa`;
- `conta_receber`;
- `tipo`: `boleto`, `pix`;
- `status`: `criado`, `registrado`, `aguardando`, `pago`, `vencido`, `cancelado`;
- `nosso_numero`, `linha_digitavel`;
- `codigo_pix`, `qrcode_base64`;
- `data_vencimento`, `valor`;
- `data_pagamento`, `valor_pago`;
- `url_boleto`;
- `metadados`;
- `criado_em`, `atualizado_em`.

### RegraCobrancan

Automacao de envio de cobrancas.

Campos:

- `empresa`;
- `nome`;
- `gatilho`: `antes_vencimento`, `no_vencimento`, `apos_vencimento`, `cobranca_final`;
- `dias_offset`: ex. `-3` (3 dias antes), `0`, `+7` (7 dias depois);
- `canal`: `sistema`, `email`, `whatsapp`, `sms`;
- `modelo_mensagem`;
- `ativo`;
- `criado_em`, `atualizado_em`.

### HistoricoCobranca

Registro imutavel de cada envio de cobranca.

Campos:

- `empresa`;
- `conta_receber`;
- `canal`;
- `mensagem_enviada`;
- `status_envio`: `enviado`, `falhou`;
- `enviado_em`.

### TransferenciaInterna

Campos:

- `empresa`;
- `conta_origem`, `conta_destino`;
- `data_transferencia`;
- `valor`, `tarifa`;
- `descricao`;
- `movimentacao_saida`, `movimentacao_entrada`: FKs para `MovimentacaoFinanceira` geradas automaticamente;
- `realizado_por`;
- `comprovante`;
- `criado_em`, `atualizado_em`.

### ContratoFinanceiro

Campos:

- `empresa`;
- `tipo`: `emprestimo`, `financiamento`, `leasing`;
- `descricao`, `credor`;
- `valor_principal`, `taxa_juros_mensal`, `total_parcelas`;
- `data_inicio`, `data_fim`;
- `status`: `ativo`, `quitado`, `inadimplente`, `cancelado`;
- `saldo_devedor`;
- `conta_bancaria`, `plano_conta`;
- `observacao`;
- `criado_em`, `atualizado_em`.

### ParcelaContratoFinanceiro

Campos:

- `contrato`;
- `numero_parcela`;
- `data_vencimento`;
- `valor_principal`, `valor_juros`, `valor_total`;
- `status`: `pendente`, `pago`, `atrasado`, `cancelado`;
- `conta_pagar`;
- `data_pagamento`;
- `criado_em`, `atualizado_em`.

Ordenacao: `contrato`, `numero_parcela`.

### AplicacaoFinanceira

Campos:

- `empresa`;
- `banco`, `descricao`;
- `tipo`: `cdb`, `lci`, `lca`, `fundos`, `poupanca`, `tesouro`, `outros`;
- `conta_bancaria`;
- `data_aplicacao`, `valor_aplicado`;
- `rendimento_percentual`;
- `data_vencimento`;
- `data_resgate`, `valor_resgatado`, `valor_imposto`;
- `saldo_atual`;
- `status`: `ativa`, `vencida`, `resgatada`, `cancelada`;
- `observacao`;
- `criado_em`, `atualizado_em`.

---

## 7. Contabil

### NaturezaConta

- `ativo`, `passivo`, `patrimonio_liquido`, `receita`, `despesa`, `custo`, `resultado`.

### TipoLancamentoContabil

- `manual`, `automatico`, `estorno`, `ajuste`.

### StatusFechamento

- `aberto`, `em_fechamento`, `fechado`, `reaberto`.

### ContaContabil

Campos:

- `empresa`;
- `codigo`: unico por empresa;
- `nome`;
- `natureza`;
- `tipo_saldo`: `devedora`, `credora` (definido automaticamente pela natureza se omitido);
- `pai`: hierarquia de contas;
- `aceita_lancamento`: `False` para contas sinteticas;
- `plano_conta_financeiro`: FK para `PlanoConta` (opcional);
- `ativo`;
- `criado_em`, `atualizado_em`.

Restricao: `empresa` + `codigo` precisa ser unico.

Indices: `empresa`, `natureza`; `empresa`, `ativo`.

### CentroResultadoContabil

Campos:

- `empresa`;
- `codigo`, `nome`;
- `pai`;
- `ativo`;
- `criado_em`, `atualizado_em`.

Restricao: `empresa` + `codigo` precisa ser unico.

### HistoricoPadrao

Campos:

- `empresa`;
- `codigo`, `descricao`;
- `criado_em`, `atualizado_em`.

Restricao: `empresa` + `codigo` precisa ser unico.

### CompetenciaContabil

Campos:

- `empresa`;
- `ano`, `mes`;
- `status`;
- `fechado_em`, `fechado_por`;
- `reaberto_em`, `reaberto_por`;
- `justificativa_reabertura`;
- `criado_em`, `atualizado_em`.

Restricao: `empresa` + `ano` + `mes` precisa ser unico.

### LancamentoContabil

Campos:

- `empresa`;
- `numero`: sequencial automatico por empresa, imutavel;
- `data_lancamento`, `data_competencia`;
- `tipo`;
- `historico`, `historico_padrao`;
- `origem_modelo`, `origem_id`;
- `usuario`;
- `estornado`;
- `lancamento_original`: FK para estorno de origem;
- `excluido_logicamente`, `justificativa_exclusao`;
- `criado_em`, `atualizado_em`.

Regras: debitos e creditos das partidas devem ser iguais; lancamentos em competencia fechada sao bloqueados.

Indices: `empresa`, `data_lancamento`; `empresa`, `data_competencia`; `origem_modelo`, `origem_id`.

### PartidaContabil

Campos:

- `lancamento`;
- `conta`;
- `centro_resultado` (opcional);
- `tipo_partida`: `debito`, `credito`;
- `valor`: maior que zero;
- `historico_complementar`;
- `criado_em`, `atualizado_em`.

Regra: contas sinteticas (`aceita_lancamento=False`) nao aceitam partidas.

Indices: `lancamento`, `tipo_partida`; `conta`.

---

## 8. Fiscal

### RegimeTributario

- `simples_nacional`, `lucro_presumido`, `lucro_real`, `mei`.

### TipoImposto

- `iss`, `pis`, `cofins`, `irpj`, `csll`, `inss_retido`, `icms`, `ipi`.

### StatusNotaFiscal

- `pendente`, `emitida`, `autorizada`, `cancelada`, `rejeitada`, `inutilizada`.

### TipoNotaFiscal

- `nfe`, `nfse`, `nfce`, `cte`.

### ConfiguracaoFiscalEmpresa

Campos:

- `empresa`: OneToOne;
- `regime_tributario`;
- `inscricao_estadual`, `inscricao_municipal`;
- `cnae_principal`;
- `aliquota_iss`, `aliquota_pis`, `aliquota_cofins`, `aliquota_irpj`, `aliquota_csll`;
- `retencao_inss`, `aliquota_inss`;
- `configuracoes_extras`;
- `criado_em`, `atualizado_em`.

### NotaFiscal

Campos:

- `empresa`;
- `tipo`;
- `numero`, `serie`, `chave_acesso`, `protocolo`;
- `data_emissao`, `data_competencia`;
- `cliente`, `fornecedor`;
- `valor_produtos`, `valor_servicos`, `valor_desconto`;
- `valor_iss`, `valor_pis`, `valor_cofins`, `valor_irrf`, `valor_csll`, `valor_inss`, `valor_total`;
- `status`;
- `xml_nota`, `pdf_danfe`;
- `conta_pagar`, `conta_receber`;
- `observacao`;
- `criado_em`, `atualizado_em`.

Indice: `empresa`, `status`, `data_emissao`.

### ItemNotaFiscal

Campos:

- `nota_fiscal`;
- `descricao`, `quantidade`, `valor_unitario`, `valor_total`;
- `servico`;
- `codigo_servico_municipal`;
- `aliquota_iss`, `valor_iss`;
- `criado_em`, `atualizado_em`.

### EventoFiscal

Campos:

- `nota_fiscal`;
- `tipo_evento`: `emissao`, `autorizacao`, `cancelamento`, `inutilizacao`, `consulta`, `rejeicao`;
- `descricao`, `codigo_retorno`, `mensagem_retorno`;
- `xml_evento`;
- `usuario`;
- `criado_em`, `atualizado_em`.

Ordenacao: `-criado_em`.

### ImpostoApurado

Campos:

- `empresa`;
- `ano`, `mes`;
- `tipo_imposto`;
- `base_calculo`, `aliquota`;
- `valor_apurado`, `valor_retido`, `valor_a_pagar`;
- `data_vencimento`;
- `conta_pagar`;
- `criado_em`, `atualizado_em`.

Restricao: `empresa` + `ano` + `mes` + `tipo_imposto` precisa ser unico.

### ObrigacaoFiscal

Campos:

- `empresa`;
- `descricao`;
- `tipo`: `declaracao`, `pagamento`, `entrega`;
- `competencia_ano`, `competencia_mes`;
- `data_vencimento`;
- `status`: `pendente`, `cumprida`, `atrasada`, `dispensada`;
- `observacao`;
- `criado_em`, `atualizado_em`.

### ConfiguracaoImpostoPorServico

Campos:

- `empresa`;
- `servico`;
- `tipo_imposto`;
- `aliquota`;
- `retencao`;
- `criado_em`, `atualizado_em`.

Restricao: `empresa` + `servico` + `tipo_imposto` precisa ser unico.

---

## 9. Relacionamentos principais

```text
--- Core ---
Empresa 1:N Usuario
Empresa 1:N Perfil
Empresa 1:N EmpresaModulo
Modulo  1:N EmpresaModulo
Modulo  1:N Permissao
Perfil  N:N Permissao via PerfilPermissao
Usuario N:N Perfil via UsuarioPerfil
Empresa 1:N EventLog
Empresa 1:N Notificacao
Usuario 1:1 MFASecret
Usuario 1:N HistoricoSenha

--- Financeiro base ---
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

--- Financeiro avancado ---
Empresa 1:N RecorrenciaFinanceira
Empresa 1:N PeriodoFechamento
Empresa 1:N RateioLancamento
Empresa 1:N AlcadaAprovacao
AlcadaAprovacao 1:N AlcadaAprovador
Empresa 1:N CredencialBancaria
Empresa 1:N ImportacaoOFX
Empresa 1:N RegraConciliacao
ContaReceber 1:N CobrancaFinanceira
Empresa 1:N RegraCobrancan
ContaReceber 1:N HistoricoCobranca
ContaBancaria 1:N TransferenciaInterna
Empresa 1:N ContratoFinanceiro
ContratoFinanceiro 1:N ParcelaContratoFinanceiro
Empresa 1:N AplicacaoFinanceira

--- Contabil ---
Empresa 1:N ContaContabil
Empresa 1:N CentroResultadoContabil
Empresa 1:N HistoricoPadrao
Empresa 1:N CompetenciaContabil
Empresa 1:N LancamentoContabil
LancamentoContabil 1:N PartidaContabil
ContaContabil 1:N PartidaContabil
PlanoConta 1:N ContaContabil

--- Fiscal ---
Empresa 1:1 ConfiguracaoFiscalEmpresa
Empresa 1:N NotaFiscal
NotaFiscal 1:N ItemNotaFiscal
NotaFiscal 1:N EventoFiscal
Empresa 1:N ImpostoApurado
Empresa 1:N ObrigacaoFiscal
Empresa 1:N ConfiguracaoImpostoPorServico
Servico 1:N ConfiguracaoImpostoPorServico

--- Inteligencia ---
Empresa 1:N AlertaIA
Empresa 1:N Anomalia
Empresa 1:N PrevisaoIA
```
