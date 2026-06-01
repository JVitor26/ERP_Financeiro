# Modulo Financeiro Avancado

## Visao geral

Este documento cobre os recursos avancados do modulo financeiro (`financeiro/views_advanced.py`), implementados apos o MVP inicial. Todas as rotas ficam sob `/api/financeiro/`.

---

## Recorrencias Financeiras

### Descricao

Lancamentos recorrentes que geram contas a pagar ou a receber automaticamente em intervalo configurado.

### Endpoint

```
GET    /api/financeiro/recorrencias/
POST   /api/financeiro/recorrencias/
GET    /api/financeiro/recorrencias/{id}/
PUT    /api/financeiro/recorrencias/{id}/
DELETE /api/financeiro/recorrencias/{id}/
POST   /api/financeiro/recorrencias/{id}/pausar/
POST   /api/financeiro/recorrencias/{id}/reativar/
POST   /api/financeiro/recorrencias/{id}/cancelar/
```

Filtros: `tipo`, `status`, `periodicidade`
Busca: `descricao`

### Campos principais

| Campo | Opcoes |
|---|---|
| `tipo` | `pagar`, `receber` |
| `periodicidade` | `diaria`, `semanal`, `mensal`, `trimestral`, `semestral`, `anual` |
| `status` | `ativa`, `pausada`, `cancelada` |
| `data_inicio`, `data_fim` | Vigencia (fim pode ser nulo = indeterminado) |
| `valor` | Valor de cada geracao |
| `dia_vencimento` | Dia do mes para periodicidades mensais e acima |
| `total_gerado` | Contador de lancamentos gerados (somente leitura) |

Payload de criacao:
```json
{
  "tipo": "pagar",
  "descricao": "Aluguel mensal",
  "valor": "3500.00",
  "periodicidade": "mensal",
  "data_inicio": "2026-01-01",
  "dia_vencimento": 10
}
```

---

## Periodo de Fechamento Financeiro

### Descricao

Bloqueia alteracoes em titulos financeiros de um periodo especifico. Diferente da competencia contabil, age sobre o modulo financeiro.

### Endpoint

```
GET    /api/financeiro/periodos-fechamento/
POST   /api/financeiro/periodos-fechamento/
GET    /api/financeiro/periodos-fechamento/{id}/
POST   /api/financeiro/periodos-fechamento/{id}/fechar/
POST   /api/financeiro/periodos-fechamento/{id}/reabrir/
```

`POST /reabrir/` exige:
```json
{ "justificativa": "Correcao de titulo do periodo." }
```

---

## Rateio de Lancamento

### Descricao

Distribui um lancamento financeiro por multiplos centros de custo ou planos de conta.

### Endpoint

```
GET    /api/financeiro/rateios/
POST   /api/financeiro/rateios/
GET    /api/financeiro/rateios/{id}/
DELETE /api/financeiro/rateios/{id}/
```

Filtros: `origem_modelo`, `centro_custo`, `plano_conta`

---

## Alcada de Aprovacao

### Descricao

Define regras de aprovacao por valor, centro de custo ou fornecedor, com suporte a multiplos aprovadores.

### Endpoint

```
GET    /api/financeiro/alcadas-aprovacao/
POST   /api/financeiro/alcadas-aprovacao/
GET    /api/financeiro/alcadas-aprovacao/{id}/
PUT    /api/financeiro/alcadas-aprovacao/{id}/
DELETE /api/financeiro/alcadas-aprovacao/{id}/
```

Filtros: `ativo`
Busca: `nome`

A resposta inclui os aprovadores aninhados (array `aprovadores`).

---

## Credencial Bancaria

### Descricao

Armazena credenciais de integracao bancaria (Open Finance, API do banco). O `client_secret` e somente escrita — nao e retornado nas leituras.

### Endpoint

```
GET    /api/financeiro/credenciais-bancarias/
POST   /api/financeiro/credenciais-bancarias/
GET    /api/financeiro/credenciais-bancarias/{id}/
PUT    /api/financeiro/credenciais-bancarias/{id}/
DELETE /api/financeiro/credenciais-bancarias/{id}/
```

Filtros: `ativa`, `tipo_integracao`

---

## Importacao OFX

### Descricao

Importa extratos bancarios no formato OFX. O arquivo e processado sincronamente no `perform_create` — cada transacao gera uma `ConciliacaoBancaria` pendente. Duplicidades sao detectadas pelo campo `FITID` do OFX.

### Endpoint

```
GET    /api/financeiro/importacoes-ofx/
POST   /api/financeiro/importacoes-ofx/    (multipart/form-data)
GET    /api/financeiro/importacoes-ofx/{id}/
```

Filtros: `status`, `conta_bancaria`

Payload (multipart):
```
arquivo: <arquivo .ofx>
conta_bancaria: <id>
```

Status do processamento: `pendente` → `processando` → `processado` (ou `erro`).

Campos de resultado (somente leitura): `total_lancamentos`, `lancamentos_importados`, `lancamentos_duplicados`, `data_inicio_extrato`, `data_fim_extrato`, `erro`.

---

## Regra de Conciliacao

### Descricao

Define criterios automaticos para sugestao de conciliacao bancaria (por valor, historico, documento, etc.).

### Endpoint

```
GET    /api/financeiro/regras-conciliacao/
POST   /api/financeiro/regras-conciliacao/
GET    /api/financeiro/regras-conciliacao/{id}/
PUT    /api/financeiro/regras-conciliacao/{id}/
DELETE /api/financeiro/regras-conciliacao/{id}/
```

Filtros: `ativa`
Busca: `nome`

---

## Cobranca Financeira (Boleto / PIX)

### Descricao

Representa uma cobranca emitida para um cliente (boleto ou PIX). Pode estar vinculada a uma `ContaReceber`.

### Endpoint

```
GET    /api/financeiro/cobrancas/
POST   /api/financeiro/cobrancas/
GET    /api/financeiro/cobrancas/{id}/
PUT    /api/financeiro/cobrancas/{id}/
DELETE /api/financeiro/cobrancas/{id}/
POST   /api/financeiro/cobrancas/{id}/gerar_pix/
```

Filtros: `tipo`, `status`
Ordenacao: `data_vencimento`, `valor`

`POST /gerar_pix/` — gera codigo PIX simulado (stub) e salva em `codigo_pix`.

---

## Regua de Cobranca

### Descricao

Automacao de envio de cobrancas por canal (e-mail, WhatsApp, sistema) em funcao de gatilhos (antes do vencimento, no dia, apos o vencimento).

### Endpoint

```
GET    /api/financeiro/regras-cobranca/
POST   /api/financeiro/regras-cobranca/
GET    /api/financeiro/regras-cobranca/{id}/
PUT    /api/financeiro/regras-cobranca/{id}/
DELETE /api/financeiro/regras-cobranca/{id}/
```

Filtros: `ativo`, `gatilho`, `canal`
Busca: `nome`

---

## Historico de Cobranca

Registro de cada envio de cobranca. Somente leitura.

```
GET /api/financeiro/historico-cobranca/
GET /api/financeiro/historico-cobranca/{id}/
```

Filtros: `canal`, `status_envio`

---

## Transferencia Interna

### Descricao

Transferencia entre contas bancarias da mesma empresa. Ao criar, gera automaticamente duas `MovimentacaoFinanceira`: uma saida na conta origem e uma entrada na conta destino.

### Endpoint

```
GET    /api/financeiro/transferencias-internas/
POST   /api/financeiro/transferencias-internas/
GET    /api/financeiro/transferencias-internas/{id}/
DELETE /api/financeiro/transferencias-internas/{id}/
```

Filtros: `conta_origem`, `conta_destino`
Ordenacao: `data_transferencia`, `valor`

Payload:
```json
{
  "conta_origem": 1,
  "conta_destino": 2,
  "data_transferencia": "2026-06-01",
  "valor": "10000.00",
  "tarifa": "5.00",
  "descricao": "Transferencia para conta de investimentos"
}
```

---

## Contrato Financeiro (Emprestimos e Financiamentos)

### Descricao

Controla contratos de emprestimo ou financiamento com geracao de cronograma de parcelas.

### Endpoint

```
GET    /api/financeiro/contratos-financeiros/
POST   /api/financeiro/contratos-financeiros/
GET    /api/financeiro/contratos-financeiros/{id}/
PUT    /api/financeiro/contratos-financeiros/{id}/
DELETE /api/financeiro/contratos-financeiros/{id}/
POST   /api/financeiro/contratos-financeiros/{id}/gerar_parcelas/
```

Filtros: `tipo`, `status`
Busca: `descricao`, `credor`

`POST /gerar_parcelas/` — gera as parcelas do contrato calculando juros mensais. So pode ser chamado uma vez por contrato.

Resposta:
```json
{ "detail": "12 parcelas geradas.", "parcelas": [101, 102, 103, ...] }
```

---

## Aplicacao Financeira

### Descricao

Controla aplicacoes financeiras (CDB, LCI, poupanca, etc.) com registro de rendimento, resgate e imposto.

### Endpoint

```
GET    /api/financeiro/aplicacoes-financeiras/
POST   /api/financeiro/aplicacoes-financeiras/
GET    /api/financeiro/aplicacoes-financeiras/{id}/
PUT    /api/financeiro/aplicacoes-financeiras/{id}/
DELETE /api/financeiro/aplicacoes-financeiras/{id}/
POST   /api/financeiro/aplicacoes-financeiras/{id}/resgatar/
```

Filtros: `tipo`, `status`
Busca: `descricao`, `banco`

`POST /resgatar/` — registra o resgate e zera o saldo:
```json
{
  "valor_resgatado": "10500.00",
  "valor_imposto": "75.00",
  "data_resgate": "2026-06-01"
}
```

---

## Tela Tesouraria no frontend

A aba Tesouraria possui tres sub-abas:

| Aba | Endpoint consumido |
|---|---|
| Transferencias | `/api/financeiro/transferencias-internas/` |
| Emprestimos | `/api/financeiro/contratos-financeiros/` |
| Aplicacoes | `/api/financeiro/aplicacoes-financeiras/` |
