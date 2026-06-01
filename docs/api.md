# API Inicial

Base URL em desenvolvimento:

```text
http://127.0.0.1:8000/api/
```

## Autenticacao

- `POST /api/auth/token/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/token/verify/`
- `GET /api/auth/me/`
- `GET /api/schema/`
- `GET /api/docs/`

Exemplo de login JWT:

```json
{
  "username": "admin",
  "password": "Admin@123"
}
```

## Core

- `GET /api/core/empresas/`
- `GET /api/core/modulos/`
- `GET /api/core/empresa-modulos/`
- `GET /api/core/usuarios/`
- `GET /api/core/perfis/`
- `GET /api/core/permissoes/`
- `GET /api/core/eventos/`
- `GET /api/core/notificacoes/`

## Financeiro

- `GET /api/financeiro/centros-custo/`
- `GET /api/financeiro/plano-contas/`
- `GET /api/financeiro/contas-bancarias/`
- `GET /api/financeiro/clientes/`
- `GET /api/financeiro/fornecedores/`
- `GET /api/financeiro/contas-pagar/`
- `POST /api/financeiro/contas-pagar/{id}/baixar/`
- `POST /api/financeiro/contas-pagar/{id}/solicitar_aprovacao/`
- `POST /api/financeiro/contas-pagar/{id}/cancelar/`
- `POST /api/financeiro/contas-pagar/{id}/anexar/`
- `GET /api/financeiro/contas-receber/`
- `POST /api/financeiro/contas-receber/{id}/receber/`
- `POST /api/financeiro/contas-receber/{id}/renegociar/`
- `POST /api/financeiro/contas-receber/{id}/cancelar/`
- `POST /api/financeiro/contas-receber/{id}/anexar/`
- `GET /api/financeiro/movimentacoes/`
- `GET /api/financeiro/conciliacoes/`
- `POST /api/financeiro/conciliacoes/importar_csv/`
- `POST /api/financeiro/conciliacoes/sugerir/`
- `POST /api/financeiro/conciliacoes/{id}/conciliar/`
- `GET /api/financeiro/orcamentos/`
- `POST /api/financeiro/aprovacoes-pagamento/{id}/aprovar/`
- `POST /api/financeiro/aprovacoes-pagamento/{id}/reprovar/`
- `GET /api/financeiro/fluxo-caixa/?data_inicio=2026-05-01&data_fim=2026-05-31`
- `GET /api/financeiro/fluxo-caixa/dashboard/?data_inicio=2026-05-01&data_fim=2026-05-31`
- `GET /api/financeiro/fluxo-caixa/dre/?data_inicio=2026-05-01&data_fim=2026-05-31`
- `POST /api/financeiro/relatorios/`

Relatorios aceitam:

```json
{
  "tipo": "contas_pagar",
  "formato": "xlsx",
  "data_inicio": "2026-05-01",
  "data_fim": "2026-05-31"
}
```

## Inteligencia

- `GET /api/inteligencia/alertas/`
- `GET /api/inteligencia/anomalias/`
- `POST /api/inteligencia/anomalias/detectar_duplicidades/`
- `POST /api/inteligencia/anomalias/varredura/`
- `POST /api/inteligencia/anomalias/{id}/feedback/`
- `GET /api/inteligencia/previsoes/`
- `POST /api/inteligencia/previsoes/gerar_baseline_caixa/`

## Observacoes

- Autenticacao inicial usa sessao/admin do Django.
- Os endpoints filtram dados pela empresa do usuario, exceto superusuarios.
- O log de eventos e somente leitura pela API.
- Escrita em cadastros administrativos do core exige usuario `is_staff`.
- `DELETE` em contas a pagar/receber executa exclusao logica e registra evento.
- Contas a pagar/receber ja consultam permissoes por perfil para visualizar, editar, excluir, baixar e receber.
- Login por JWT registra sucesso/falha e bloqueia excesso de tentativas.
- Relatorios exportados geram evento de auditoria.
