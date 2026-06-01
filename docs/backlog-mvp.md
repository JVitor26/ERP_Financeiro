# Backlog e roadmap

Este arquivo registra o que foi planejado para o MVP, o que ja esta implementado e o que permanece como evolucao.

## 1. MVP implementado

### Fundacao

- Projeto Django criado.
- Apps `core`, `financeiro` e `inteligencia` criados.
- Modelagem de empresas, usuarios, perfis, permissoes e modulos.
- `EventLog` imutavel criado.
- Modelos registrados no admin.
- Requisitos, arquitetura, API e modelo de dados documentados.

### Financeiro base

- Centros de custo.
- Plano de contas.
- Contas bancarias.
- Clientes.
- Fornecedores.
- Servicos.
- Contas a pagar.
- Contas a receber.
- Baixa parcial e total.
- Recebimento parcial e total.
- Eventos de baixa.
- Cancelamento auditado.
- Exclusao logica.
- Renegociacao de recebiveis.
- Anexos financeiros.

### Fluxo e auditoria

- Movimentacoes financeiras.
- Resumo de fluxo de caixa.
- Dashboard financeiro.
- DRE gerencial.
- Filtros por empresa e periodo.
- Auditoria de alteracoes criticas.
- Hash sequencial em eventos.
- Login com auditoria.
- Bloqueio por tentativas falhas.

### Dashboard e relatorios

- API de cards financeiros.
- Grafico de entradas e saidas no frontend.
- DRE no frontend.
- Agenda de vencimentos.
- Relatorio de contas a pagar.
- Relatorio de contas a receber.
- Relatorio de fluxo de caixa.
- Relatorio de eventos.
- Exportacao CSV.
- Exportacao XLSX.
- Exportacao PDF.
- Historico de exportacao por auditoria.

### Inteligencia baseline

- Detector de pagamentos duplicados.
- Detector de valores fora do padrao por fornecedor.
- Previsao simples de caixa.
- Painel de alertas.
- Painel de anomalias.
- Feedback de analise.
- Eventos automaticos de risco.

### Conciliacao

- Importacao CSV.
- Sugestao de conciliacao por valor e data aproximada.
- Conciliacao manual.
- Status de conciliacao.
- Marcacao de movimentacao como conciliada.

## 2. Evolucao de curto prazo

- Importacao OFX.
- Tela completa para anexos.
- Edicao visual completa de registros existentes.
- Exclusao visual controlada com confirmacao e justificativa.
- Filtros avancados no frontend por centro de custo e plano de contas.
- Controle visual de permissoes por perfil.
- Melhorar tela de conciliacao com revisao de sugestoes.
- Criar testes de API por endpoint.
- Criar testes de frontend para fluxos principais.

## 3. Evolucao de medio prazo

- PostgreSQL como ambiente padrao de homologacao.
- Deploy produtivo com HTTPS.
- Fila assincrona para relatorios.
- Fila assincrona para varreduras de IA.
- Jobs agendados para previsoes recorrentes.
- Logs estruturados.
- Rotina formal de backup e restore.
- Auditoria de acesso a dados sensiveis.
- Integracao bancaria por API.

## 4. Evolucao de longo prazo

- Motor contabil.
- Modulo fiscal.
- Integracao com notas fiscais.
- App mobile.
- Modelos de machine learning treinados.
- Alertas por email, WhatsApp, SMS e push em producao.
- Conector com BI externo.
- Permissoes multiempresa avancadas por grupo economico.
