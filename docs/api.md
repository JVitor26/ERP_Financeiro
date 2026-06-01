# API completa

Base local:

```text
http://127.0.0.1:8000/api/
```

Swagger:

```text
GET /api/docs/
GET /api/schema/
```

## 1. Autenticacao

### Gerar token

```text
POST /api/auth/token/
```

Payload:

```json
{
  "username": "admin",
  "password": "Admin@123",
  "mfa_code": "000000"
}
```

`mfa_code` e opcional, exceto quando `mfa_habilitado=True` para o usuario. Nesse caso deve ser um codigo TOTP valido gerado pelo aplicativo autenticador ou um backup code.

Resposta:

```json
{
  "refresh": "...",
  "access": "...",
  "user": {
    "id": 1,
    "username": "admin",
    "empresa_id": 1,
    "is_staff": true,
    "is_superuser": true
  }
}
```

### Atualizar token

```text
POST /api/auth/token/refresh/
```

Payload:

```json
{
  "refresh": "..."
}
```

### Validar token

```text
POST /api/auth/token/verify/
```

Payload:

```json
{
  "token": "..."
}
```

### Usuario autenticado

```text
GET /api/auth/me/
```

Retorna os campos do `UsuarioSerializer`, incluindo empresa, telefone, cargo, flags de staff e MFA.

## 2. Convencoes da API

### Autorizacao

Enviar:

```text
Authorization: Bearer <access_token>
```

### Paginacao

Listagens retornam uma resposta paginada pelo DRF. Use:

```text
?page=1&page_size=50
```

### Busca e ordenacao

Quando disponivel:

```text
?search=texto
?ordering=campo
?ordering=-campo
```

### Multiempresa

Superuser acessa todas as empresas. Usuario comum acessa apenas dados da propria empresa. Ao criar registros com campo `empresa`, usuarios comuns recebem a empresa do proprio usuario automaticamente nos viewsets com escopo direto.

### Erros comuns

- `400`: validacao de payload, regra de negocio ou datas invalidas.
- `401`: token ausente, invalido ou expirado.
- `403`: usuario sem permissao.
- `404`: registro inexistente ou fora do escopo da empresa.

## 3. Core

### Empresas

```text
GET    /api/core/empresas/
POST   /api/core/empresas/
GET    /api/core/empresas/{id}/
PATCH  /api/core/empresas/{id}/
PUT    /api/core/empresas/{id}/
DELETE /api/core/empresas/{id}/
```

Campos:

- `razao_social`;
- `nome_fantasia`;
- `cnpj`;
- `status`: `ativa`, `inativa`, `suspensa`;
- `timezone`;
- `configuracoes`.

Busca:

- `razao_social`;
- `nome_fantasia`;
- `cnpj`.

Ordenacao:

- `razao_social`;
- `criado_em`.

Escrita exige `is_staff`.

### Modulos

```text
GET    /api/core/modulos/
POST   /api/core/modulos/
GET    /api/core/modulos/{id}/
PATCH  /api/core/modulos/{id}/
PUT    /api/core/modulos/{id}/
DELETE /api/core/modulos/{id}/
```

Campos:

- `codigo`;
- `nome`;
- `descricao`;
- `ativo`;
- `schema_configuracao`.

Filtros:

- `ativo`.

Busca:

- `codigo`;
- `nome`.

Escrita exige `is_staff`.

### Empresa modulos

```text
GET    /api/core/empresa-modulos/
POST   /api/core/empresa-modulos/
GET    /api/core/empresa-modulos/{id}/
PATCH  /api/core/empresa-modulos/{id}/
PUT    /api/core/empresa-modulos/{id}/
DELETE /api/core/empresa-modulos/{id}/
```

Campos:

- `empresa`;
- `modulo`;
- `ativo`;
- `instalado_em`;
- `configuracoes`.

Filtros:

- `empresa`;
- `modulo`;
- `ativo`.

Restricao:

- uma empresa nao pode ter o mesmo modulo duplicado.

### Usuarios

```text
GET    /api/core/usuarios/
POST   /api/core/usuarios/
GET    /api/core/usuarios/{id}/
PATCH  /api/core/usuarios/{id}/
PUT    /api/core/usuarios/{id}/
DELETE /api/core/usuarios/{id}/
```

Campos aceitos:

- `username`;
- `password`;
- `email`;
- `first_name`;
- `last_name`;
- `empresa`;
- `telefone`;
- `cargo`;
- `mfa_habilitado`;
- `is_active`;
- `is_staff`.

`password` e somente escrita. `date_joined` e somente leitura.

Filtros:

- `empresa`;
- `is_active`;
- `is_staff`.

Busca:

- `username`;
- `email`;
- `first_name`;
- `last_name`.

Escrita exige `is_staff`.

### Perfis

```text
GET    /api/core/perfis/
POST   /api/core/perfis/
GET    /api/core/perfis/{id}/
PATCH  /api/core/perfis/{id}/
PUT    /api/core/perfis/{id}/
DELETE /api/core/perfis/{id}/
```

Campos:

- `empresa`;
- `nome`;
- `descricao`;
- `sistema`.

Filtros:

- `empresa`;
- `sistema`.

Busca:

- `nome`;
- `descricao`.

Restricao:

- `empresa` + `nome` precisa ser unico.

### Permissoes

```text
GET    /api/core/permissoes/
POST   /api/core/permissoes/
GET    /api/core/permissoes/{id}/
PATCH  /api/core/permissoes/{id}/
PUT    /api/core/permissoes/{id}/
DELETE /api/core/permissoes/{id}/
```

Campos:

- `codigo`;
- `modulo`;
- `tela`;
- `acao`;
- `descricao`;
- `sensivel`.

Filtros:

- `modulo`;
- `tela`;
- `acao`;
- `sensivel`.

Busca:

- `codigo`;
- `tela`;
- `acao`;
- `descricao`.

### Perfil permissoes

```text
GET    /api/core/perfil-permissoes/
POST   /api/core/perfil-permissoes/
GET    /api/core/perfil-permissoes/{id}/
PATCH  /api/core/perfil-permissoes/{id}/
PUT    /api/core/perfil-permissoes/{id}/
DELETE /api/core/perfil-permissoes/{id}/
```

Campos:

- `perfil`;
- `permissao`.

Filtros:

- `perfil`;
- `permissao`.

Restricao:

- `perfil` + `permissao` precisa ser unico.

### Usuario perfis

```text
GET    /api/core/usuario-perfis/
POST   /api/core/usuario-perfis/
GET    /api/core/usuario-perfis/{id}/
PATCH  /api/core/usuario-perfis/{id}/
PUT    /api/core/usuario-perfis/{id}/
DELETE /api/core/usuario-perfis/{id}/
```

Campos:

- `usuario`;
- `perfil`.

Filtros:

- `usuario`;
- `perfil`.

Restricao:

- `usuario` + `perfil` precisa ser unico.

### Eventos de auditoria

```text
GET /api/core/eventos/
GET /api/core/eventos/{id}/
```

Somente leitura.

Filtros:

- `empresa`;
- `tipo_evento`;
- `modulo`;
- `acao`;
- `nivel_risco`.

Busca:

- `registro_modelo`;
- `registro_id`;
- `justificativa`;
- `acao`.

Ordenacao:

- `criado_em`;
- `nivel_risco`.

Campos extras de leitura:

- `usuario_nome`;
- `empresa_nome`.

### Notificacoes

```text
GET    /api/core/notificacoes/
POST   /api/core/notificacoes/
GET    /api/core/notificacoes/{id}/
PATCH  /api/core/notificacoes/{id}/
PUT    /api/core/notificacoes/{id}/
DELETE /api/core/notificacoes/{id}/
```

Campos:

- `empresa`;
- `usuario`;
- `canal`: `sistema`, `email`, `whatsapp`, `sms`, `push`;
- `titulo`;
- `mensagem`;
- `status`: `pendente`, `enviada`, `falhou`, `lida`;
- `enviado_em`;
- `lido_em`;
- `metadados`.

Filtros:

- `empresa`;
- `usuario`;
- `canal`;
- `status`.

Busca:

- `titulo`;
- `mensagem`.

## 4. Financeiro

### Centros de custo

```text
GET    /api/financeiro/centros-custo/
POST   /api/financeiro/centros-custo/
GET    /api/financeiro/centros-custo/{id}/
PATCH  /api/financeiro/centros-custo/{id}/
PUT    /api/financeiro/centros-custo/{id}/
DELETE /api/financeiro/centros-custo/{id}/
```

Campos:

- `empresa`;
- `codigo`;
- `nome`;
- `pai`;
- `ativo`.

Filtros:

- `empresa`;
- `ativo`;
- `pai`.

Busca:

- `codigo`;
- `nome`.

Ordenacao:

- `codigo`;
- `nome`.

### Plano de contas

```text
GET    /api/financeiro/plano-contas/
POST   /api/financeiro/plano-contas/
GET    /api/financeiro/plano-contas/{id}/
PATCH  /api/financeiro/plano-contas/{id}/
PUT    /api/financeiro/plano-contas/{id}/
DELETE /api/financeiro/plano-contas/{id}/
```

Campos:

- `empresa`;
- `codigo`;
- `nome`;
- `tipo`;
- `pai`;
- `vincula_dre`;
- `vincula_fluxo_caixa`;
- `ativo`.

Tipos:

```text
receita
despesa
custo
investimento
imposto
taxa
comissao
repasse
financiamento
emprestimo
```

Filtros:

- `empresa`;
- `tipo`;
- `ativo`;
- `pai`.

Busca:

- `codigo`;
- `nome`.

### Contas bancarias

```text
GET    /api/financeiro/contas-bancarias/
POST   /api/financeiro/contas-bancarias/
GET    /api/financeiro/contas-bancarias/{id}/
PATCH  /api/financeiro/contas-bancarias/{id}/
PUT    /api/financeiro/contas-bancarias/{id}/
DELETE /api/financeiro/contas-bancarias/{id}/
```

Campos:

- `empresa`;
- `banco`;
- `agencia`;
- `numero`;
- `descricao`;
- `saldo_inicial`;
- `ativa`.

Filtros:

- `empresa`;
- `ativa`;
- `banco`.

Busca:

- `banco`;
- `numero`;
- `descricao`.

### Clientes

```text
GET    /api/financeiro/clientes/
POST   /api/financeiro/clientes/
GET    /api/financeiro/clientes/{id}/
PATCH  /api/financeiro/clientes/{id}/
PUT    /api/financeiro/clientes/{id}/
DELETE /api/financeiro/clientes/{id}/
```

Campos:

- `empresa`;
- `nome`;
- `tipo_pessoa`: `fisica` ou `juridica`;
- `documento`;
- `email`;
- `telefone`;
- `ativo`;
- `metadados`.

Filtros:

- `empresa`;
- `ativo`;
- `tipo_pessoa`.

Busca:

- `nome`;
- `documento`;
- `email`.

### Fornecedores

```text
GET    /api/financeiro/fornecedores/
POST   /api/financeiro/fornecedores/
GET    /api/financeiro/fornecedores/{id}/
PATCH  /api/financeiro/fornecedores/{id}/
PUT    /api/financeiro/fornecedores/{id}/
DELETE /api/financeiro/fornecedores/{id}/
```

Campos e filtros iguais aos de clientes.

### Servicos

```text
GET    /api/financeiro/servicos/
POST   /api/financeiro/servicos/
GET    /api/financeiro/servicos/{id}/
PATCH  /api/financeiro/servicos/{id}/
PUT    /api/financeiro/servicos/{id}/
DELETE /api/financeiro/servicos/{id}/
```

Campos:

- `empresa`;
- `codigo`;
- `nome`;
- `descricao`;
- `valor_padrao`;
- `plano_conta`;
- `ativo`;
- `metadados`.

Filtros:

- `empresa`;
- `ativo`;
- `plano_conta`.

Busca:

- `codigo`;
- `nome`;
- `descricao`.

Ordenacao:

- `nome`;
- `codigo`;
- `valor_padrao`.

Validacoes:

- `valor_padrao` nao pode ser negativo;
- `plano_conta` precisa pertencer a mesma empresa.

### Contas a pagar

```text
GET    /api/financeiro/contas-pagar/
POST   /api/financeiro/contas-pagar/
GET    /api/financeiro/contas-pagar/{id}/
PATCH  /api/financeiro/contas-pagar/{id}/
PUT    /api/financeiro/contas-pagar/{id}/
DELETE /api/financeiro/contas-pagar/{id}/
```

Campos principais:

- `empresa`;
- `fornecedor`;
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
- `numero_documento`;
- `nota_fiscal`;
- `forma_pagamento`;
- `status`;
- `comprovante`.

Campos somente leitura:

- `valor_pago`;
- `data_baixa`;
- `baixado_por`;
- `excluido_logicamente`;
- `excluido_em`;
- `excluido_por`;
- `saldo_pendente`;
- `valor_total`.

Filtros:

- `empresa`;
- `status`;
- `fornecedor`;
- `centro_custo`;
- `plano_conta`;
- `conta_bancaria`.

Busca:

- `descricao`;
- `fornecedor__nome`;
- `numero_documento`;
- `nota_fiscal`.

Ordenacao:

- `data_vencimento`;
- `valor_original`;
- `status`.

DELETE executa exclusao logica.

#### Baixar conta a pagar

```text
POST /api/financeiro/contas-pagar/{id}/baixar/
```

Payload:

```json
{
  "valor": "500.00",
  "conta_bancaria": 1,
  "forma_pagamento": "Transferencia"
}
```

`conta_bancaria` e `forma_pagamento` sao opcionais.

#### Solicitar aprovacao

```text
POST /api/financeiro/contas-pagar/{id}/solicitar_aprovacao/
```

Payload:

```json
{
  "justificativa": "Pagamento acima do limite operacional."
}
```

Justificativa e obrigatoria e precisa ter pelo menos 5 caracteres.

#### Cancelar conta a pagar

```text
POST /api/financeiro/contas-pagar/{id}/cancelar/
```

Payload:

```json
{
  "justificativa": "Titulo emitido em duplicidade."
}
```

#### Anexar comprovante

```text
POST /api/financeiro/contas-pagar/{id}/anexar/
```

Enviar `multipart/form-data` com campo `arquivo`.

### Contas a receber

```text
GET    /api/financeiro/contas-receber/
POST   /api/financeiro/contas-receber/
GET    /api/financeiro/contas-receber/{id}/
PATCH  /api/financeiro/contas-receber/{id}/
PUT    /api/financeiro/contas-receber/{id}/
DELETE /api/financeiro/contas-receber/{id}/
```

Campos principais:

- `empresa`;
- `cliente`;
- `contrato`;
- `parcela`;
- `descricao`;
- `data_emissao`;
- `data_vencimento`;
- `valor_original`;
- `desconto`;
- `juros`;
- `multa`;
- `acrescimo`;
- `honorarios`;
- `centro_custo`;
- `plano_conta`;
- `conta_bancaria`;
- `observacao`;
- `responsavel`;
- `forma_recebimento`;
- `status`.

Campos somente leitura:

- `valor_recebido`;
- `data_recebimento`;
- `recebido_por`;
- `conta_original`;
- `renegociado_em`;
- `renegociado_por`;
- `excluido_logicamente`;
- `excluido_em`;
- `excluido_por`;
- `saldo_pendente`;
- `valor_total`;
- `dias_atraso`.

Filtros:

- `empresa`;
- `status`;
- `cliente`;
- `centro_custo`;
- `plano_conta`;
- `conta_bancaria`.

Busca:

- `descricao`;
- `cliente__nome`;
- `contrato`.

Ordenacao:

- `data_vencimento`;
- `valor_original`;
- `status`.

DELETE executa exclusao logica.

#### Receber

```text
POST /api/financeiro/contas-receber/{id}/receber/
```

Payload:

```json
{
  "valor": "500.00",
  "conta_bancaria": 1,
  "forma_recebimento": "Pix"
}
```

#### Renegociar

```text
POST /api/financeiro/contas-receber/{id}/renegociar/
```

Payload:

```json
{
  "nova_data_vencimento": "2026-06-30",
  "valor_original": "1200.00",
  "juros": "20.00",
  "multa": "10.00",
  "desconto": "0.00",
  "honorarios": "0.00",
  "observacao": "Renegociacao solicitada pelo cliente."
}
```

#### Cancelar

```text
POST /api/financeiro/contas-receber/{id}/cancelar/
```

Payload:

```json
{
  "justificativa": "Contrato cancelado."
}
```

#### Anexar

```text
POST /api/financeiro/contas-receber/{id}/anexar/
```

Enviar `multipart/form-data` com campo `arquivo`.

### Movimentacoes

```text
GET /api/financeiro/movimentacoes/
GET /api/financeiro/movimentacoes/{id}/
```

Somente leitura.

Filtros:

- `empresa`;
- `tipo`;
- `conta_bancaria`;
- `centro_custo`;
- `plano_conta`;
- `conciliado`.

Busca:

- `descricao`;
- `origem_modelo`;
- `origem_id`.

Ordenacao:

- `data_movimento`;
- `valor`.

### Conciliacoes

```text
GET    /api/financeiro/conciliacoes/
POST   /api/financeiro/conciliacoes/
GET    /api/financeiro/conciliacoes/{id}/
PATCH  /api/financeiro/conciliacoes/{id}/
PUT    /api/financeiro/conciliacoes/{id}/
DELETE /api/financeiro/conciliacoes/{id}/
```

Campos:

- `empresa`;
- `conta_bancaria`;
- `data_movimento`;
- `valor`;
- `historico`;
- `documento`;
- `status`;
- `movimentacao`;
- `metadados`.

Filtros:

- `empresa`;
- `conta_bancaria`;
- `status`.

Busca:

- `historico`;
- `documento`.

Ordenacao:

- `data_movimento`;
- `valor`.

#### Importar CSV

```text
POST /api/financeiro/conciliacoes/importar_csv/
```

Enviar `multipart/form-data`:

- `arquivo`;
- `conta_bancaria`.

Colunas aceitas no CSV:

- `data` ou `data_movimento`;
- `valor`;
- `historico` ou `descricao`;
- `documento` opcional.

#### Sugerir conciliacoes

```text
POST /api/financeiro/conciliacoes/sugerir/
```

Nao exige payload.

#### Conciliar manualmente

```text
POST /api/financeiro/conciliacoes/{id}/conciliar/
```

Payload:

```json
{
  "movimentacao": 10
}
```

### Orcamentos

```text
GET    /api/financeiro/orcamentos/
POST   /api/financeiro/orcamentos/
GET    /api/financeiro/orcamentos/{id}/
PATCH  /api/financeiro/orcamentos/{id}/
PUT    /api/financeiro/orcamentos/{id}/
DELETE /api/financeiro/orcamentos/{id}/
```

Campos:

- `empresa`;
- `ano`;
- `mes`;
- `centro_custo`;
- `plano_conta`;
- `valor_previsto`;
- `valor_realizado`.

Filtros:

- `empresa`;
- `ano`;
- `mes`;
- `centro_custo`;
- `plano_conta`.

### Aprovacoes de pagamento

```text
GET    /api/financeiro/aprovacoes-pagamento/
POST   /api/financeiro/aprovacoes-pagamento/
GET    /api/financeiro/aprovacoes-pagamento/{id}/
PATCH  /api/financeiro/aprovacoes-pagamento/{id}/
PUT    /api/financeiro/aprovacoes-pagamento/{id}/
DELETE /api/financeiro/aprovacoes-pagamento/{id}/
```

Campos principais:

- `conta_pagar`;
- `justificativa`.

Campos somente leitura:

- `solicitante`;
- `aprovador`;
- `status`;
- `decidido_em`;
- `solicitante_nome`;
- `aprovador_nome`;
- `conta_pagar_detalhes`.

Filtros:

- `conta_pagar`;
- `status`;
- `solicitante`;
- `aprovador`.

#### Aprovar

```text
POST /api/financeiro/aprovacoes-pagamento/{id}/aprovar/
```

Payload:

```json
{
  "justificativa": "Pagamento aprovado."
}
```

#### Reprovar

```text
POST /api/financeiro/aprovacoes-pagamento/{id}/reprovar/
```

Payload:

```json
{
  "justificativa": "Documento invalido."
}
```

### Fluxo de caixa

```text
GET /api/financeiro/fluxo-caixa/?data_inicio=2026-05-01&data_fim=2026-05-31
```

Resposta:

```json
{
  "total_a_pagar": "1000.00",
  "total_a_receber": "2500.00",
  "entradas_realizadas": "1800.00",
  "saidas_realizadas": "700.00",
  "saldo_previsto": "1500.00",
  "saldo_realizado": "1100.00",
  "inadimplencia": "300.00"
}
```

### Dashboard financeiro

```text
GET /api/financeiro/fluxo-caixa/dashboard/?data_inicio=2026-05-01&data_fim=2026-05-31
```

Inclui os campos do fluxo e tambem:

- `contas_pagar_hoje`;
- `contas_receber_hoje`;
- `receita_periodo`;
- `despesa_periodo`;
- `resultado_periodo`;
- `titulos_pagar_abertos`;
- `titulos_receber_abertos`.

### DRE

```text
GET /api/financeiro/fluxo-caixa/dre/?data_inicio=2026-05-01&data_fim=2026-05-31
```

Retorna:

- totais principais;
- `linhas`;
- `centros_custo`;
- `planos_contas`.

### Relatorios

```text
POST /api/financeiro/relatorios/
```

Payload:

```json
{
  "tipo": "contas_pagar",
  "formato": "xlsx",
  "data_inicio": "2026-05-01",
  "data_fim": "2026-05-31"
}
```

Tipos:

- `contas_pagar`;
- `contas_receber`;
- `eventos`;
- `fluxo_caixa`.

Formatos:

- `csv`;
- `xlsx`;
- `pdf`.

Resposta:

- arquivo para download;
- `Content-Disposition` com nome do arquivo.

## 5. Inteligencia

### Alertas

```text
GET    /api/inteligencia/alertas/
POST   /api/inteligencia/alertas/
GET    /api/inteligencia/alertas/{id}/
PATCH  /api/inteligencia/alertas/{id}/
PUT    /api/inteligencia/alertas/{id}/
DELETE /api/inteligencia/alertas/{id}/
```

Campos:

- `empresa`;
- `titulo`;
- `mensagem`;
- `nivel_risco`;
- `status`;
- `origem_modelo`;
- `origem_id`;
- `score`;
- `metadados`.

Filtros:

- `empresa`;
- `nivel_risco`;
- `status`;
- `origem_modelo`;
- `origem_id`.

Busca:

- `titulo`;
- `mensagem`.

Ordenacao:

- `criado_em`;
- `nivel_risco`;
- `score`.

### Anomalias

```text
GET    /api/inteligencia/anomalias/
POST   /api/inteligencia/anomalias/
GET    /api/inteligencia/anomalias/{id}/
PATCH  /api/inteligencia/anomalias/{id}/
PUT    /api/inteligencia/anomalias/{id}/
DELETE /api/inteligencia/anomalias/{id}/
```

Campos:

- `empresa`;
- `tipo`;
- `descricao`;
- `nivel_risco`;
- `status`;
- `entidade_modelo`;
- `entidade_id`;
- `evidencia`.

Filtros:

- `empresa`;
- `tipo`;
- `nivel_risco`;
- `status`;
- `entidade_modelo`;
- `entidade_id`.

Busca:

- `descricao`;
- `entidade_modelo`;
- `entidade_id`.

#### Detectar duplicidades

```text
POST /api/inteligencia/anomalias/detectar_duplicidades/
```

Gera anomalias para possiveis pagamentos duplicados.

#### Varredura geral

```text
POST /api/inteligencia/anomalias/varredura/
```

Executa:

- duplicidades;
- fornecedores fora do padrao;
- previsao baseline.

#### Feedback

```text
POST /api/inteligencia/anomalias/{id}/feedback/
```

Payload:

```json
{
  "status": "confirmado",
  "observacao": "Conferencia confirmou duplicidade."
}
```

Status aceitos:

```text
aberto
em_analise
confirmado
descartado
resolvido
```

### Previsoes

```text
GET    /api/inteligencia/previsoes/
POST   /api/inteligencia/previsoes/
GET    /api/inteligencia/previsoes/{id}/
PATCH  /api/inteligencia/previsoes/{id}/
PUT    /api/inteligencia/previsoes/{id}/
DELETE /api/inteligencia/previsoes/{id}/
```

Campos:

- `empresa`;
- `nome`;
- `data_referencia`;
- `horizonte_dias`;
- `metrica`;
- `valor_previsto`;
- `confianca`;
- `modelo`;
- `parametros`.

Filtros:

- `empresa`;
- `metrica`;
- `modelo`;
- `data_referencia`.

Busca:

- `nome`;
- `metrica`;
- `modelo`.

#### Gerar previsao baseline

```text
POST /api/inteligencia/previsoes/gerar_baseline_caixa/
```

Payload:

```json
{
  "horizonte_dias": 60
}
```

## 6. MFA

### Iniciar configuracao

```text
POST /api/auth/mfa/setup/
```

Gera secret TOTP e QR code. Nao requer payload. Retorna:

```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_base64": "<png em base64>",
  "otpauth_uri": "otpauth://totp/..."
}
```

### Ativar MFA

```text
POST /api/auth/mfa/ativar/
```

Payload:

```json
{ "codigo": "123456" }
```

Valida o TOTP e ativa MFA. Retorna 8 backup codes de uso unico.

### Verificar codigo

```text
POST /api/auth/mfa/verificar/
```

Payload:

```json
{ "codigo": "123456" }
```

Aceita codigo TOTP ou backup code. Backup codes sao consumidos apos uso.

### Desativar MFA

```text
POST /api/auth/mfa/desativar/
```

Payload:

```json
{ "senha": "MinhaSenh@123" }
```

Exige confirmacao de senha atual.

### Listar backup codes (mascarados)

```text
GET /api/auth/mfa/backup-codes/
```

Retorna codigos com os 7 primeiros caracteres mascarados por `*`.

### Regenerar backup codes

```text
POST /api/auth/mfa/regenerar-backup-codes/
```

Invalida todos os backup codes anteriores e gera 8 novos.

---

## 7. Financeiro avancado

### Recorrencias financeiras

```text
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

Campos principais: `tipo` (`pagar`/`receber`), `descricao`, `valor`, `periodicidade`, `data_inicio`, `data_fim`, `dia_vencimento`, `status`.

### Periodos de fechamento financeiro

```text
GET    /api/financeiro/periodos-fechamento/
POST   /api/financeiro/periodos-fechamento/
GET    /api/financeiro/periodos-fechamento/{id}/
POST   /api/financeiro/periodos-fechamento/{id}/fechar/
POST   /api/financeiro/periodos-fechamento/{id}/reabrir/
```

`POST /reabrir/` exige `{ "justificativa": "..." }`.

### Rateios de lancamento

```text
GET    /api/financeiro/rateios/
POST   /api/financeiro/rateios/
GET    /api/financeiro/rateios/{id}/
DELETE /api/financeiro/rateios/{id}/
```

Filtros: `origem_modelo`, `centro_custo`, `plano_conta`

### Alcadas de aprovacao

```text
GET    /api/financeiro/alcadas-aprovacao/
POST   /api/financeiro/alcadas-aprovacao/
GET    /api/financeiro/alcadas-aprovacao/{id}/
PUT    /api/financeiro/alcadas-aprovacao/{id}/
DELETE /api/financeiro/alcadas-aprovacao/{id}/
```

Filtros: `ativo`

### Credenciais bancarias

```text
GET    /api/financeiro/credenciais-bancarias/
POST   /api/financeiro/credenciais-bancarias/
GET    /api/financeiro/credenciais-bancarias/{id}/
PUT    /api/financeiro/credenciais-bancarias/{id}/
DELETE /api/financeiro/credenciais-bancarias/{id}/
```

Filtros: `ativa`, `tipo_integracao`. Campo `client_secret` e somente escrita.

### Importacoes OFX

```text
GET    /api/financeiro/importacoes-ofx/
POST   /api/financeiro/importacoes-ofx/    (multipart/form-data)
GET    /api/financeiro/importacoes-ofx/{id}/
```

Filtros: `status`, `conta_bancaria`. Processamento e sincronno — cria conciliacoes pendentes.

### Regras de conciliacao

```text
GET    /api/financeiro/regras-conciliacao/
POST   /api/financeiro/regras-conciliacao/
GET    /api/financeiro/regras-conciliacao/{id}/
PUT    /api/financeiro/regras-conciliacao/{id}/
DELETE /api/financeiro/regras-conciliacao/{id}/
```

Filtros: `ativa`

### Cobrancas financeiras (boleto/PIX)

```text
GET    /api/financeiro/cobrancas/
POST   /api/financeiro/cobrancas/
GET    /api/financeiro/cobrancas/{id}/
PUT    /api/financeiro/cobrancas/{id}/
DELETE /api/financeiro/cobrancas/{id}/
POST   /api/financeiro/cobrancas/{id}/gerar_pix/
```

Filtros: `tipo`, `status`

`POST /gerar_pix/` — gera codigo PIX EMV e salva no campo `codigo_pix`.

### Regras de cobranca (regua)

```text
GET    /api/financeiro/regras-cobranca/
POST   /api/financeiro/regras-cobranca/
GET    /api/financeiro/regras-cobranca/{id}/
PUT    /api/financeiro/regras-cobranca/{id}/
DELETE /api/financeiro/regras-cobranca/{id}/
```

Filtros: `ativo`, `gatilho`, `canal`

### Historico de cobranca

```text
GET /api/financeiro/historico-cobranca/
GET /api/financeiro/historico-cobranca/{id}/
```

Somente leitura. Filtros: `canal`, `status_envio`

### Transferencias internas

```text
GET    /api/financeiro/transferencias-internas/
POST   /api/financeiro/transferencias-internas/
GET    /api/financeiro/transferencias-internas/{id}/
DELETE /api/financeiro/transferencias-internas/{id}/
```

Filtros: `conta_origem`, `conta_destino`

Ao criar, gera automaticamente duas `MovimentacaoFinanceira` (saida e entrada).

### Contratos financeiros (emprestimos)

```text
GET    /api/financeiro/contratos-financeiros/
POST   /api/financeiro/contratos-financeiros/
GET    /api/financeiro/contratos-financeiros/{id}/
PUT    /api/financeiro/contratos-financeiros/{id}/
DELETE /api/financeiro/contratos-financeiros/{id}/
POST   /api/financeiro/contratos-financeiros/{id}/gerar_parcelas/
```

Filtros: `tipo`, `status`

`POST /gerar_parcelas/` — gera o cronograma de parcelas calculando juros mensais.

### Aplicacoes financeiras

```text
GET    /api/financeiro/aplicacoes-financeiras/
POST   /api/financeiro/aplicacoes-financeiras/
GET    /api/financeiro/aplicacoes-financeiras/{id}/
PUT    /api/financeiro/aplicacoes-financeiras/{id}/
DELETE /api/financeiro/aplicacoes-financeiras/{id}/
POST   /api/financeiro/aplicacoes-financeiras/{id}/resgatar/
```

Filtros: `tipo`, `status`

`POST /resgatar/` — payload: `{ "valor_resgatado": "10500.00", "valor_imposto": "75.00", "data_resgate": "2026-06-01" }`

---

## 8. Contabil

Base URL: `/api/contabil/`

### Contas contabeis

```text
GET    /api/contabil/contas-contabeis/
POST   /api/contabil/contas-contabeis/
GET    /api/contabil/contas-contabeis/{id}/
PUT    /api/contabil/contas-contabeis/{id}/
DELETE /api/contabil/contas-contabeis/{id}/
GET    /api/contabil/contas-contabeis/arvore/
```

Filtros: `natureza`, `ativo`, `aceita_lancamento`, `pai`

`GET /arvore/` — retorna hierarquia completa com filhos aninhados.

### Centros de resultado contabil

```text
GET    /api/contabil/centros-resultado/
POST   /api/contabil/centros-resultado/
GET    /api/contabil/centros-resultado/{id}/
PUT    /api/contabil/centros-resultado/{id}/
DELETE /api/contabil/centros-resultado/{id}/
```

### Historicos padrao

```text
GET    /api/contabil/historicos-padrao/
POST   /api/contabil/historicos-padrao/
GET    /api/contabil/historicos-padrao/{id}/
PUT    /api/contabil/historicos-padrao/{id}/
DELETE /api/contabil/historicos-padrao/{id}/
```

### Competencias contabeis

```text
GET    /api/contabil/competencias/
POST   /api/contabil/competencias/
GET    /api/contabil/competencias/{id}/
POST   /api/contabil/competencias/{id}/fechar/
POST   /api/contabil/competencias/{id}/reabrir/
```

`POST /reabrir/` exige `{ "justificativa": "..." }`.

### Lancamentos contabeis

```text
GET    /api/contabil/lancamentos/
POST   /api/contabil/lancamentos/
GET    /api/contabil/lancamentos/{id}/
PUT    /api/contabil/lancamentos/{id}/
DELETE /api/contabil/lancamentos/{id}/
POST   /api/contabil/lancamentos/{id}/estornar/
```

Filtros: `tipo`, `estornado`, `excluido_logicamente`
Query params adicionais: `data_ini`, `data_fim`, `conta`

`POST /estornar/` — payload: `{ "motivo": "...", "data_estorno": "2026-06-01" }`

### Relatorios contabeis

```text
GET /api/contabil/relatorios/diario/?data_ini=...&data_fim=...
GET /api/contabil/relatorios/razao/?conta={id}&data_ini=...&data_fim=...
GET /api/contabil/relatorios/balancete/?ano=2026&mes=6
GET /api/contabil/relatorios/balanco-patrimonial/?data_ini=...&data_fim=...
GET /api/contabil/relatorios/dre/?data_ini=...&data_fim=...
```

---

## 9. Fiscal

Base URL: `/api/fiscal/`

### Configuracao fiscal

```text
GET    /api/fiscal/configuracao-fiscal/
POST   /api/fiscal/configuracao-fiscal/
GET    /api/fiscal/configuracao-fiscal/{id}/
PUT    /api/fiscal/configuracao-fiscal/{id}/
```

### Notas fiscais

```text
GET    /api/fiscal/notas-fiscais/
POST   /api/fiscal/notas-fiscais/
GET    /api/fiscal/notas-fiscais/{id}/
PUT    /api/fiscal/notas-fiscais/{id}/
POST   /api/fiscal/notas-fiscais/{id}/cancelar/
POST   /api/fiscal/notas-fiscais/{id}/calcular_impostos/
```

Filtros: `status`, `tipo`, `cliente`, `fornecedor`
Query params: `data_ini`, `data_fim`

`POST /cancelar/` — payload: `{ "justificativa": "..." }` (minimo 15 caracteres)

`POST /calcular_impostos/` — retorna ISS, PIS, COFINS e INSS calculados.

### Eventos fiscais

```text
GET /api/fiscal/eventos-fiscais/
GET /api/fiscal/eventos-fiscais/{id}/
```

Somente leitura.

### Impostos apurados

```text
GET    /api/fiscal/impostos-apurados/
POST   /api/fiscal/impostos-apurados/
GET    /api/fiscal/impostos-apurados/{id}/
PUT    /api/fiscal/impostos-apurados/{id}/
DELETE /api/fiscal/impostos-apurados/{id}/
```

Filtros: `ano`, `mes`, `tipo_imposto`

### Obrigacoes fiscais

```text
GET    /api/fiscal/obrigacoes-fiscais/
POST   /api/fiscal/obrigacoes-fiscais/
GET    /api/fiscal/obrigacoes-fiscais/{id}/
PUT    /api/fiscal/obrigacoes-fiscais/{id}/
DELETE /api/fiscal/obrigacoes-fiscais/{id}/
```

### Configuracao de imposto por servico

```text
GET    /api/fiscal/config-imposto-servico/
POST   /api/fiscal/config-imposto-servico/
GET    /api/fiscal/config-imposto-servico/{id}/
PUT    /api/fiscal/config-imposto-servico/{id}/
DELETE /api/fiscal/config-imposto-servico/{id}/
```

---

## 10. Permissoes esperadas por recurso

Padrao:

```text
<modulo>.<tela>.visualizar
<modulo>.<tela>.editar
<modulo>.<tela>.excluir
```

Acoes especiais:

```text
financeiro.contas_pagar.baixar
financeiro.contas_pagar.aprovar
financeiro.contas_receber.receber
financeiro.conciliacoes.importar
financeiro.conciliacoes.conciliar
financeiro.relatorios.exportar
inteligencia.anomalias.gerar
inteligencia.previsoes.editar
```
