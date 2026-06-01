# Modulo Contabil

## Visao geral

O modulo contabil (`contabil/`) implementa o motor de escrituracao contabil por partidas dobradas. Ele e separado do modulo financeiro operacional e se integra a ele por meio da associacao entre `PlanoConta` (financeiro) e `ContaContabil` (contabil).

Base URL: `/api/contabil/`

---

## Modelos

### ContaContabil

Representa uma conta do plano de contas contabil da empresa.

| Campo | Tipo | Descricao |
|---|---|---|
| `codigo` | CharField | Codigo unico por empresa (ex: `1.1.01`) |
| `nome` | CharField | Nome da conta |
| `natureza` | CharField | `ativo`, `passivo`, `patrimonio_liquido`, `receita`, `despesa`, `custo`, `resultado` |
| `tipo_saldo` | CharField | `devedora` ou `credora` — definido automaticamente pela natureza se omitido |
| `pai` | FK self | Conta pai (hierarquia de contas) |
| `aceita_lancamento` | BooleanField | `False` para contas sinteticas (agrupadores) |
| `plano_conta_financeiro` | FK PlanoConta | Vinculo com plano financeiro |
| `ativo` | BooleanField | Se `False`, a conta nao aparece em listagens padrao |

Regras:
- Contas com natureza `ativo`, `despesa` ou `custo` sao devedoras; demais sao credoras.
- Tentativa de salvar com `tipo_saldo` incompativel com a natureza gera `ValidationError`.
- Codigo unico por empresa (`uniq_conta_contabil_empresa_codigo`).

### CentroResultadoContabil

Centro de resultado contabil com hierarquia. Campos: `codigo`, `nome`, `pai`, `ativo`.

### HistoricoPadrao

Textos padronizados para historico de lancamentos. Campos: `codigo`, `descricao`.

### CompetenciaContabil

Controla o status de cada mes/ano contabil por empresa.

| Campo | Descricao |
|---|---|
| `ano`, `mes` | Periodo contabil |
| `status` | `aberto`, `em_fechamento`, `fechado`, `reaberto` |
| `fechado_em`, `fechado_por` | Auditoria de fechamento |
| `reaberto_em`, `reaberto_por`, `justificativa_reabertura` | Auditoria de reabertura |

Regra: lancamentos com `data_competencia` em periodo fechado sao bloqueados pelo `clean()` do `LancamentoContabil`.

### LancamentoContabil

Cabecalho do lancamento contabil por partidas dobradas.

| Campo | Descricao |
|---|---|
| `numero` | Sequencial automatico por empresa |
| `data_lancamento` | Data do lancamento no diario |
| `data_competencia` | Data de competencia economica |
| `tipo` | `manual`, `automatico`, `estorno`, `ajuste` |
| `historico` | Texto livre |
| `historico_padrao` | FK para `HistoricoPadrao` (opcional) |
| `origem_modelo`, `origem_id` | Rastreabilidade (ex: `financeiro.ContaPagar`, `42`) |
| `usuario` | Usuario responsavel |
| `estornado` | Marcado quando um estorno e gerado |
| `lancamento_original` | FK para o lancamento estornado (se aplicavel) |
| `excluido_logicamente`, `justificativa_exclusao` | Exclusao logica com auditoria |

Validacao: soma dos debitos deve ser igual a soma dos creditos (`clean()` verifica apos salvar partidas).

### PartidaContabil

Uma linha de debito ou credito dentro de um `LancamentoContabil`.

| Campo | Descricao |
|---|---|
| `lancamento` | FK para `LancamentoContabil` |
| `conta` | FK para `ContaContabil` |
| `centro_resultado` | FK para `CentroResultadoContabil` (opcional) |
| `tipo_partida` | `debito` ou `credito` |
| `valor` | Decimal — deve ser maior que zero |
| `historico_complementar` | Texto adicional da partida |

Regra: contas sinteticas (`aceita_lancamento=False`) nao aceitam partidas.

---

## Endpoints

### Contas Contabeis

```
GET    /api/contabil/contas-contabeis/
POST   /api/contabil/contas-contabeis/
GET    /api/contabil/contas-contabeis/{id}/
PUT    /api/contabil/contas-contabeis/{id}/
PATCH  /api/contabil/contas-contabeis/{id}/
DELETE /api/contabil/contas-contabeis/{id}/
GET    /api/contabil/contas-contabeis/arvore/
```

Filtros: `natureza`, `ativo`, `aceita_lancamento`, `pai`
Busca: `codigo`, `nome`
Ordenacao: `codigo`, `nome`, `natureza`

`GET /arvore/` retorna hierarquia completa em formato aninhado (raizes com filhos).

### Centros de Resultado Contabil

```
GET    /api/contabil/centros-resultado/
POST   /api/contabil/centros-resultado/
GET    /api/contabil/centros-resultado/{id}/
PUT    /api/contabil/centros-resultado/{id}/
DELETE /api/contabil/centros-resultado/{id}/
```

Filtros: `ativo`, `pai`

### Historicos Padrao

```
GET    /api/contabil/historicos-padrao/
POST   /api/contabil/historicos-padrao/
GET    /api/contabil/historicos-padrao/{id}/
PUT    /api/contabil/historicos-padrao/{id}/
DELETE /api/contabil/historicos-padrao/{id}/
```

Busca: `codigo`, `descricao`

### Competencias Contabeis

```
GET    /api/contabil/competencias/
POST   /api/contabil/competencias/
GET    /api/contabil/competencias/{id}/
POST   /api/contabil/competencias/{id}/fechar/
POST   /api/contabil/competencias/{id}/reabrir/
```

`POST /fechar/` — nao requer payload. Fecha a competencia, registra `fechado_em` e `fechado_por`.

`POST /reabrir/` — payload obrigatorio:
```json
{ "justificativa": "Correcao de lancamento aprovada pela diretoria." }
```

### Lancamentos Contabeis

```
GET    /api/contabil/lancamentos/
POST   /api/contabil/lancamentos/
GET    /api/contabil/lancamentos/{id}/
PUT    /api/contabil/lancamentos/{id}/
DELETE /api/contabil/lancamentos/{id}/
POST   /api/contabil/lancamentos/{id}/estornar/
```

Filtros: `tipo`, `estornado`, `excluido_logicamente`
Busca: `historico`, `numero`, `origem_modelo`, `origem_id`
Filtros adicionais por query param: `data_ini`, `data_fim`, `conta`

`POST /estornar/` — cria lancamento de estorno com partidas invertidas:
```json
{ "motivo": "Lancamento incorreto", "data_estorno": "2026-06-01" }
```

Payload para criar lancamento:
```json
{
  "data_lancamento": "2026-06-01",
  "data_competencia": "2026-06-01",
  "historico": "Recebimento de cliente X",
  "partidas": [
    { "conta": 10, "tipo_partida": "debito", "valor": "1500.00" },
    { "conta": 25, "tipo_partida": "credito", "valor": "1500.00" }
  ]
}
```

---

## Relatorios Contabeis

Base URL: `/api/contabil/relatorios/`

### Diario Contabil

```
GET /api/contabil/relatorios/diario/?data_ini=2026-01-01&data_fim=2026-06-30
```

Retorna todos os lancamentos no periodo com suas partidas, ordenados cronologicamente.

Resposta:
```json
{
  "data_ini": "2026-01-01",
  "data_fim": "2026-06-30",
  "total_lancamentos": 42,
  "lancamentos": [...]
}
```

### Razao Contabil

```
GET /api/contabil/relatorios/razao/?conta=10&data_ini=2026-01-01&data_fim=2026-06-30
```

Parametro `conta` (ID) e obrigatorio. Retorna saldos e todas as partidas da conta no periodo.

Resposta:
```json
{
  "conta": { "id": 10, "codigo": "1.1.01", "nome": "Caixa" },
  "data_ini": "...",
  "data_fim": "...",
  "debitos": "5000.00",
  "creditos": "3000.00",
  "saldo": "2000.00",
  "partidas": [...]
}
```

### Balancete

```
GET /api/contabil/relatorios/balancete/?ano=2026&mes=6
```

Retorna saldo de todas as contas ativas no mes/ano informados. Parametros `ano` e `mes` sao obrigatorios.

Resposta:
```json
{
  "empresa": "Empresa Exemplo",
  "ano": 2026,
  "mes": 6,
  "contas": [
    { "codigo": "1.1.01", "nome": "Caixa", "debitos": "...", "creditos": "...", "saldo": "..." }
  ]
}
```

### Balanco Patrimonial

```
GET /api/contabil/relatorios/balanco-patrimonial/?data_ini=2026-01-01&data_fim=2026-06-30
```

Agrupa contas por natureza (Ativo, Passivo, Patrimonio Liquido) com totais.

Resposta contem: `ativo`, `passivo`, `patrimonio_liquido`, `total_ativo`, `total_passivo_pl`, `diferenca`.

### DRE Contabil

```
GET /api/contabil/relatorios/dre/?data_ini=2026-01-01&data_fim=2026-06-30
```

Demonstracao do Resultado do Exercicio: Receitas - Despesas - Custos = Lucro/Prejuizo.

Resposta contem: `receitas`, `despesas`, `custos`, `resultado_antes_impostos`, `contas_resultado`, `resultado_liquido`.

---

## Regras de negocio

- Todo lancamento deve ter partidas balanceadas (total debitos = total creditos).
- Lancamentos em competencias fechadas sao bloqueados na criacao.
- Estorno gera novo lancamento com partidas invertidas e marca o original como `estornado=True`.
- Exclusao logica preserva o lancamento no banco com `excluido_logicamente=True`.
- Numero do lancamento e sequencial automatico por empresa e imutavel.
- Superuser enxerga dados de todas as empresas; usuarios comuns veem apenas sua empresa.
