# Arquitetura Modular

## Visao geral

O ERP e organizado em um motor central e apps de dominio.

## Motor central

Responsabilidades:

- empresas;
- usuarios;
- perfis;
- permissoes;
- modulos;
- auditoria;
- notificacoes;
- configuracoes;
- seguranca;
- eventos de sistema.

No codigo, esse motor esta no app `core`.

## Modulo financeiro

Responsabilidades:

- clientes;
- fornecedores;
- contas a pagar;
- contas a receber;
- fluxo de caixa;
- contas bancarias;
- centro de custo;
- plano de contas;
- conciliacao;
- orcamento;
- aprovacoes.

No codigo, esse dominio esta no app `financeiro`.

## Modulo de inteligencia

Responsabilidades:

- alertas de IA;
- anomalias;
- previsoes;
- analises baseline;
- historico de evidencias;
- geracao de eventos de risco.

No codigo, esse dominio esta no app `inteligencia`.

## Principio de rastreabilidade

Qualquer operacao que crie, altere, baixe, aprove, reprove, exporte ou acesse dado sensivel deve chamar `core.services.registrar_evento`.

O log deve guardar:

- empresa;
- usuario;
- modulo;
- tela;
- acao;
- registro afetado;
- valor anterior;
- valor novo;
- origem;
- justificativa;
- nivel de risco;
- metadados tecnicos.

## Evolucao recomendada

1. Criar APIs REST para os modelos do MVP.
2. Adicionar camada de permissoes por acao.
3. Adicionar dashboard web.
4. Adicionar importador OFX/CSV.
5. Adicionar fila para notificacoes e analises de IA.
6. Migrar banco de desenvolvimento para PostgreSQL.
