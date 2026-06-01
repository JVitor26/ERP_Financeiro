# MFA — Autenticacao de Dois Fatores

## Visao geral

O MFA (Multi-Factor Authentication) usa TOTP (Time-based One-Time Password) compativel com aplicativos autenticadores como Google Authenticator, Microsoft Authenticator e Authy.

O fluxo e dividido em: configurar → ativar → usar no login. O desligamento exige confirmacao de senha.

Dependencias: `pyotp`, `qrcode`

---

## Endpoints

Todos exigem autenticacao JWT (`Authorization: Bearer <access_token>`).

| Metodo | Rota | Descricao |
|---|---|---|
| `POST` | `/api/auth/mfa/setup/` | Gera secret e QR code (sem ativar) |
| `POST` | `/api/auth/mfa/ativar/` | Valida TOTP e ativa MFA |
| `POST` | `/api/auth/mfa/verificar/` | Verifica codigo TOTP ou backup code |
| `POST` | `/api/auth/mfa/desativar/` | Desativa MFA com confirmacao de senha |
| `GET`  | `/api/auth/mfa/backup-codes/` | Lista backup codes mascarados |
| `POST` | `/api/auth/mfa/regenerar-backup-codes/` | Regenera backup codes |

---

## Fluxo de ativacao

### 1. Iniciar configuracao

```
POST /api/auth/mfa/setup/
```

Nao requer payload. Gera um novo secret TOTP e salva em `MFASecret` com `ativado_em=None` (inativo).

Resposta:
```json
{
  "secret": "JBSWY3DPEHPK3PXP",
  "qr_code_base64": "<png em base64>",
  "otpauth_uri": "otpauth://totp/ERP%20Financeiro:admin?secret=...&issuer=ERP%20Financeiro"
}
```

O `qr_code_base64` pode ser exibido diretamente em `<img src="data:image/png;base64,...">`.

### 2. Escanear QR code

O usuario abre o aplicativo autenticador e escaneia o QR code ou insere o secret manualmente.

### 3. Confirmar ativacao

```
POST /api/auth/mfa/ativar/
```

Payload:
```json
{ "codigo": "123456" }
```

Valida o TOTP com `valid_window=1` (aceita codigo do minuto anterior e seguinte para compensar desvios de relogio). Se valido:
- Salva `ativado_em` no `MFASecret`.
- Marca `mfa_habilitado=True` no usuario.
- Retorna 8 backup codes de 10 caracteres alfanumericos.

Resposta:
```json
{
  "detail": "MFA ativado com sucesso.",
  "backup_codes": ["ABCD1234EF", "GH5678IJKL", ...]
}
```

Os backup codes sao exibidos apenas neste momento. Guarde-os com segurança.

---

## Uso no login

O endpoint de token (`POST /api/auth/token/`) aceita `mfa_code` quando `mfa_habilitado=True`:

```json
{
  "username": "admin",
  "password": "Admin@123",
  "mfa_code": "123456"
}
```

Para verificar um codigo isoladamente (ex: etapa separada no frontend):

```
POST /api/auth/mfa/verificar/
```

Payload:
```json
{ "codigo": "123456" }
```

Aceita codigo TOTP valido **ou** um backup code. Backup codes sao consumidos (uso unico).

Resposta com TOTP valido:
```json
{ "detail": "Codigo TOTP valido.", "valido": true }
```

Resposta com backup code valido:
```json
{
  "detail": "Backup code valido. Codigo consumido.",
  "valido": true,
  "backup_codes_restantes": 7
}
```

---

## Backup codes

### Listar (mascarados)

```
GET /api/auth/mfa/backup-codes/
```

Retorna os codigos com os 7 primeiros caracteres substituidos por `*`:

```json
{
  "backup_codes_mascarados": ["*******EF", "*******KL", ...],
  "total": 8
}
```

### Regenerar

```
POST /api/auth/mfa/regenerar-backup-codes/
```

Invalida todos os backup codes anteriores e retorna 8 novos:

```json
{
  "detail": "Backup codes regenerados com sucesso.",
  "backup_codes": ["ABCD1234EF", ...]
}
```

---

## Desativar MFA

```
POST /api/auth/mfa/desativar/
```

Payload:
```json
{ "senha": "MinhaSenh@123" }
```

Confirma a senha atual do usuario. Se correta:
- Remove o registro `MFASecret`.
- Define `mfa_habilitado=False` no usuario.

---

## Auditoria

Todos os eventos MFA sao registrados no sistema de auditoria (`registrar_evento`):

| Acao | Nivel de risco |
|---|---|
| `mfa_setup_iniciado` | Medio |
| `mfa_ativado` | Alto |
| `mfa_verificado_totp` | Baixo |
| `mfa_verificado_backup_code` | Alto |
| `mfa_codigo_invalido` | Alto |
| `mfa_desativado` | Critico |
| `mfa_backup_codes_regenerados` | Alto |

---

## Modelo MFASecret

Criado pela migracao `core/migrations/0003_historicosenha_mfasecret.py`.

| Campo | Descricao |
|---|---|
| `usuario` | OneToOne para o usuario |
| `secret` | Secret TOTP em base32 |
| `ativado_em` | `None` enquanto nao confirmado |
| `backup_codes` | JSONField com lista de codigos em texto puro |

---

## Modelo HistoricoSenha

Criado na mesma migracao. Armazena hashes de senhas anteriores para impedir reutilizacao.

| Campo | Descricao |
|---|---|
| `usuario` | FK para o usuario |
| `senha_hash` | Hash bcrypt da senha anterior |
| `criado_em` | Timestamp do registro |
