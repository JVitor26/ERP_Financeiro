# Taxonomia de eventos

O sistema usa `EventLog` como trilha imutavel de auditoria. Cada evento possui tipo, modulo, tela, acao, nivel de risco, registro afetado, snapshots e hashes de rastreabilidade.

## 1. Tipos de evento

- `criacao`: registro criado ou login bem sucedido.
- `alteracao`: registro alterado, cancelado, renegociado ou feedback registrado.
- `exclusao_logica`: registro marcado como excluido sem remocao fisica.
- `baixa`: pagamento ou recebimento baixado.
- `aprovacao`: aprovacao de pagamento.
- `reprovacao`: reprovacao de pagamento.
- `exportacao`: relatorio ou dado exportado.
- `acesso_sensivel`: acesso a dado sensivel.
- `alerta_sistema`: alerta operacional do sistema, como login falho ou solicitacao de aprovacao.
- `alerta_ia`: alerta gerado por analise de inteligencia.
- `integracao`: importacao, conciliacao ou evento vindo de rotina externa.

## 2. Niveis de risco

- `baixo`: operacao comum sem impacto sensivel.
- `medio`: operacao operacional ou financeira comum.
- `alto`: alteracao critica, aprovacao, cancelamento, exportacao ou alerta relevante.
- `critico`: suspeita grave, fraude, exclusao indevida ou vazamento.

## 3. Padrao de nomenclatura de acao

O padrao funcional e:

```text
modulo.tela.acao
```

Exemplos:

- `core.auth.login_sucesso`
- `core.auth.login_falhou`
- `core.usuarios.criar`
- `core.usuarios.alterar`
- `financeiro.contas_pagar.criar`
- `financeiro.contas_pagar.alterar`
- `financeiro.contas_pagar.baixar_pagamento`
- `financeiro.contas_pagar.solicitar_aprovacao`
- `financeiro.contas_pagar.cancelar`
- `financeiro.contas_pagar.excluir_logicamente`
- `financeiro.contas_receber.registrar_recebimento`
- `financeiro.contas_receber.renegociar`
- `financeiro.conciliacoes.importar_csv`
- `financeiro.conciliacoes.conciliar`
- `financeiro.relatorios.exportar_contas_pagar_xlsx`
- `inteligencia.anomalias.detectar_pagamento_duplicado`
- `inteligencia.anomalias.feedback`

## 4. Eventos obrigatorios

Core:

- login com sucesso;
- login falho;
- criacao e alteracao de empresas;
- criacao e alteracao de usuarios;
- criacao e alteracao de perfis;
- criacao e alteracao de permissoes;
- criacao e alteracao de notificacoes.

Financeiro:

- criacao de conta a pagar;
- alteracao de conta a pagar;
- alteracao de valor em conta a pagar;
- alteracao de vencimento em conta a pagar;
- baixa de conta a pagar;
- solicitacao de aprovacao;
- aprovacao de pagamento;
- reprovacao de pagamento;
- cancelamento de conta a pagar;
- exclusao logica de conta a pagar;
- criacao de conta a receber;
- alteracao de conta a receber;
- alteracao de valor em conta a receber;
- alteracao de vencimento em conta a receber;
- recebimento de conta a receber;
- renegociacao de conta a receber;
- cancelamento de conta a receber;
- exclusao logica de conta a receber;
- importacao de conciliacao;
- conciliacao manual;
- exportacao de relatorio.

Inteligencia:

- deteccao de pagamento duplicado;
- deteccao de valor fora do padrao;
- geracao de alerta;
- geracao de previsao;
- feedback de anomalia.

## 5. Conteudo esperado do evento

Campos esperados:

- `tipo_evento`;
- `usuario`;
- `empresa`;
- `modulo`;
- `tela`;
- `acao`;
- `registro_modelo`;
- `registro_id`;
- `valor_anterior`;
- `valor_novo`;
- `ip`;
- `dispositivo`;
- `origem`;
- `justificativa`;
- `nivel_risco`;
- `metadados`.

## 6. Imutabilidade

`EventLog` nao permite:

- update;
- delete.

Ao salvar um novo evento:

1. O sistema busca o ultimo `hash_evento`.
2. Grava esse valor em `hash_anterior`.
3. Calcula `hash_evento` usando SHA-256.
4. Persiste o registro.

Essa cadeia permite detectar alteracoes indevidas na trilha.
