# Modulo Fiscal

## Visao geral

O modulo fiscal (`fiscal/`) gerencia documentos fiscais, apuracao de impostos, obrigacoes fiscais e configuracao tributaria por empresa e por servico.

Base URL: `/api/fiscal/`

---

## Modelos

### ConfiguracaoFiscalEmpresa

Configuracao tributaria global da empresa. Relacao OneToOne com `Empresa`.

| Campo | Descricao |
|---|---|
| `regime_tributario` | `simples_nacional`, `lucro_presumido`, `lucro_real`, `mei` |
| `inscricao_estadual`, `inscricao_municipal` | Registros fiscais |
| `cnae_principal` | Codigo CNAE |
| `aliquota_iss` | Padrao: 5,00% |
| `aliquota_pis` | Padrao: 0,65% |
| `aliquota_cofins` | Padrao: 3,00% |
| `aliquota_irpj` | Padrao: 15,00% |
| `aliquota_csll` | Padrao: 9,00% |
| `retencao_inss` | Se `True`, aplica retencao de INSS |
| `aliquota_inss` | Padrao: 11,00% |
| `configuracoes_extras` | JSONField para parametros adicionais |

### NotaFiscal

Documento fiscal emitido ou recebido.

| Campo | Descricao |
|---|---|
| `tipo` | `nfe` (NF-e), `nfse` (NFS-e), `nfce` (NFC-e), `cte` (CT-e) |
| `numero`, `serie` | Numeracao fiscal |
| `chave_acesso` | Chave de 44 digitos |
| `protocolo` | Protocolo de autorizacao |
| `data_emissao`, `data_competencia` | Datas |
| `cliente`, `fornecedor` | FK para cadastros financeiros (ambos opcionais) |
| `valor_produtos`, `valor_servicos`, `valor_desconto` | Composicao de valores |
| `valor_iss`, `valor_pis`, `valor_cofins`, `valor_irrf`, `valor_csll`, `valor_inss` | Impostos calculados |
| `valor_total` | Total da nota |
| `status` | `pendente`, `emitida`, `autorizada`, `cancelada`, `rejeitada`, `inutilizada` |
| `xml_nota` | XML completo da nota |
| `pdf_danfe` | Arquivo PDF/DANFE |
| `conta_pagar`, `conta_receber` | Vinculo com titulos financeiros |

### ItemNotaFiscal

Itens (produtos/servicos) da nota fiscal.

| Campo | Descricao |
|---|---|
| `nota_fiscal` | FK para `NotaFiscal` |
| `descricao` | Descricao do item |
| `quantidade`, `valor_unitario`, `valor_total` | Valores |
| `servico` | FK para `Servico` (opcional) |
| `codigo_servico_municipal` | Codigo de servico municipal |
| `aliquota_iss`, `valor_iss` | ISS do item |

### EventoFiscal

Registro imutavel de cada evento sobre uma nota fiscal.

| Campo | Descricao |
|---|---|
| `nota_fiscal` | FK para `NotaFiscal` |
| `tipo_evento` | `emissao`, `autorizacao`, `cancelamento`, `inutilizacao`, `consulta`, `rejeicao` |
| `descricao` | Texto do evento |
| `codigo_retorno`, `mensagem_retorno` | Retorno do servico fiscal |
| `xml_evento` | XML do evento |
| `usuario` | Usuario que provocou o evento |

### ImpostoApurado

Resultado da apuracao de impostos por periodo.

| Campo | Descricao |
|---|---|
| `ano`, `mes` | Competencia |
| `tipo_imposto` | `iss`, `pis`, `cofins`, `irpj`, `csll`, `inss_retido`, `icms`, `ipi` |
| `base_calculo`, `aliquota` | Base e percentual |
| `valor_apurado`, `valor_retido`, `valor_a_pagar` | Valores calculados |
| `data_vencimento` | Vencimento do imposto |
| `conta_pagar` | Conta a pagar gerada automaticamente |

Restricao: unico por `(empresa, ano, mes, tipo_imposto)`.

### ObrigacaoFiscal

Obrigacoes de entrega ou pagamento com prazo.

| Campo | Descricao |
|---|---|
| `descricao` | Nome da obrigacao |
| `tipo` | `declaracao`, `pagamento`, `entrega` |
| `competencia_ano`, `competencia_mes` | Referencia |
| `data_vencimento` | Prazo |
| `status` | `pendente`, `cumprida`, `atrasada`, `dispensada` |

### ConfiguracaoImpostoPorServico

Aliquotas e retencoes configuradas por tipo de servico.

| Campo | Descricao |
|---|---|
| `servico` | FK para `Servico` |
| `tipo_imposto` | Tipo do imposto |
| `aliquota` | Percentual |
| `retencao` | Se `True`, o imposto e retido na fonte |

---

## Endpoints

### Configuracao Fiscal

```
GET    /api/fiscal/configuracao-fiscal/
POST   /api/fiscal/configuracao-fiscal/
GET    /api/fiscal/configuracao-fiscal/{id}/
PUT    /api/fiscal/configuracao-fiscal/{id}/
PATCH  /api/fiscal/configuracao-fiscal/{id}/
```

### Notas Fiscais

```
GET    /api/fiscal/notas-fiscais/
POST   /api/fiscal/notas-fiscais/
GET    /api/fiscal/notas-fiscais/{id}/
PUT    /api/fiscal/notas-fiscais/{id}/
PATCH  /api/fiscal/notas-fiscais/{id}/
POST   /api/fiscal/notas-fiscais/{id}/cancelar/
POST   /api/fiscal/notas-fiscais/{id}/calcular_impostos/
```

Filtros: `status`, `tipo`, `cliente`, `fornecedor`
Busca: `numero`, `chave_acesso`, `cliente__nome`, `fornecedor__nome`
Ordenacao: `data_emissao`, `valor_total`, `numero`
Filtros por query param: `data_ini`, `data_fim`

`POST /cancelar/` — exige justificativa (minimo 15, maximo 255 caracteres):
```json
{ "justificativa": "Nota emitida com dados incorretos do tomador." }
```

Regra: apenas notas com status `emitida` ou `autorizada` podem ser canceladas.

`POST /calcular_impostos/` — calcula ISS, PIS, COFINS e INSS com base na configuracao da empresa:
```json
{
  "nota_fiscal_id": 5,
  "valor_iss": "75.00",
  "valor_pis": "9.75",
  "valor_cofins": "45.00",
  "valor_inss": "0.00"
}
```

Payload para criar nota (itens sao opcionais na criacao):
```json
{
  "tipo": "nfse",
  "data_emissao": "2026-06-01",
  "valor_total": "1500.00",
  "numero": "100",
  "itens": [
    {
      "descricao": "Desenvolvimento de software",
      "quantidade": "1.000",
      "valor_unitario": "1500.00",
      "valor_total": "1500.00"
    }
  ]
}
```

### Eventos Fiscais

```
GET /api/fiscal/eventos-fiscais/
GET /api/fiscal/eventos-fiscais/{id}/
```

Somente leitura. Filtrado automaticamente pelas notas da empresa do usuario.

### Impostos Apurados

```
GET    /api/fiscal/impostos-apurados/
POST   /api/fiscal/impostos-apurados/
GET    /api/fiscal/impostos-apurados/{id}/
PUT    /api/fiscal/impostos-apurados/{id}/
DELETE /api/fiscal/impostos-apurados/{id}/
```

Filtros: `ano`, `mes`, `tipo_imposto`

### Obrigacoes Fiscais

```
GET    /api/fiscal/obrigacoes-fiscais/
POST   /api/fiscal/obrigacoes-fiscais/
GET    /api/fiscal/obrigacoes-fiscais/{id}/
PUT    /api/fiscal/obrigacoes-fiscais/{id}/
PATCH  /api/fiscal/obrigacoes-fiscais/{id}/
DELETE /api/fiscal/obrigacoes-fiscais/{id}/
```

### Configuracao de Imposto por Servico

```
GET    /api/fiscal/config-imposto-servico/
POST   /api/fiscal/config-imposto-servico/
GET    /api/fiscal/config-imposto-servico/{id}/
PUT    /api/fiscal/config-imposto-servico/{id}/
DELETE /api/fiscal/config-imposto-servico/{id}/
```

---

## Regras de negocio

- `empresa` e sempre definida pelo backend a partir do usuario autenticado.
- Cancelamento registra automaticamente um `EventoFiscal` do tipo `cancelamento`.
- `calcular_impostos` usa as aliquotas da `ConfiguracaoFiscalEmpresa` e das `ConfiguracaoImpostoPorServico` dos itens.
- A listagem de notas usa o serializer reduzido (`NotaFiscalListSerializer`); o detalhe usa o serializer completo com itens e eventos.
- Superuser enxerga notas de todas as empresas; usuarios comuns veem apenas sua empresa.

---

## Tela no frontend

A tela Fiscal esta em `/` (modulo `fiscal`) e possui tres abas:

| Aba | Descricao |
|---|---|
| Notas Fiscais | Lista e criacao de notas com badge de status e tipo |
| Impostos Apurados | Tabela com base de calculo, aliquota e valor a pagar por tipo |
| Obrigacoes Fiscais | Prazos com status e vencimento |
