# Taxonomia de Eventos

## Tipos iniciais

- `criacao`: registro criado.
- `alteracao`: registro alterado.
- `exclusao_logica`: registro marcado como excluido.
- `baixa`: pagamento ou recebimento baixado.
- `aprovacao`: acao aprovada.
- `reprovacao`: acao reprovada.
- `exportacao`: relatorio ou dado exportado.
- `acesso_sensivel`: dado sensivel acessado.
- `alerta_sistema`: alerta automatico do sistema.
- `alerta_ia`: alerta gerado por analise de IA.
- `integracao`: evento vindo de banco, API ou rotina externa.

## Niveis de risco

- `baixo`: operacao comum sem impacto sensivel.
- `medio`: operacao financeira comum.
- `alto`: alteracao critica, alerta de IA ou acesso sensivel.
- `critico`: suspeita grave, fraude, exclusao indevida ou vazamento.

## Eventos obrigatorios no MVP

- Criacao de conta a pagar.
- Alteracao de conta a pagar.
- Alteracao de valor em conta a pagar.
- Alteracao de vencimento em conta a pagar.
- Baixa de conta a pagar.
- Exclusao logica de conta a pagar.
- Criacao de conta a receber.
- Alteracao de conta a receber.
- Alteracao de valor em conta a receber.
- Alteracao de vencimento em conta a receber.
- Recebimento de conta a receber.
- Exclusao logica de conta a receber.
- Aprovacao de pagamento.
- Reprovacao de pagamento.
- Exportacao de relatorio.
- Deteccao de anomalia por IA.

## Padrao de nomenclatura

`modulo.tela.acao`

Exemplos:

- `financeiro.contas_pagar.criar`
- `financeiro.contas_pagar.baixar`
- `financeiro.contas_receber.renegociar`
- `financeiro.conciliacao.conciliar`
- `core.usuarios.alterar_perfil`
- `inteligencia.anomalias.detectar`
