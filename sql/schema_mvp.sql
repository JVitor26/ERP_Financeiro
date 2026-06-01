-- Esquema conceitual do MVP. As migracoes oficiais devem ser geradas pelo Django.

create table empresas (
    id bigserial primary key,
    razao_social varchar(180) not null,
    nome_fantasia varchar(180) not null default '',
    cnpj varchar(18) unique,
    status varchar(20) not null default 'ativa',
    timezone varchar(64) not null default 'America/Cuiaba',
    configuracoes jsonb not null default '{}',
    criado_em timestamptz not null,
    atualizado_em timestamptz not null
);

create table modulos (
    id bigserial primary key,
    codigo varchar(60) not null unique,
    nome varchar(120) not null,
    descricao text not null default '',
    ativo boolean not null default true,
    schema_configuracao jsonb not null default '{}',
    criado_em timestamptz not null,
    atualizado_em timestamptz not null
);

create table empresa_modulos (
    id bigserial primary key,
    empresa_id bigint not null references empresas(id),
    modulo_id bigint not null references modulos(id),
    ativo boolean not null default true,
    instalado_em timestamptz not null,
    configuracoes jsonb not null default '{}',
    criado_em timestamptz not null,
    atualizado_em timestamptz not null,
    unique (empresa_id, modulo_id)
);

create table logs_eventos (
    id bigserial primary key,
    event_id uuid not null unique,
    tipo_evento varchar(40) not null,
    usuario_id bigint null,
    empresa_id bigint null references empresas(id),
    modulo varchar(80) not null,
    tela varchar(80) not null default '',
    acao varchar(80) not null,
    registro_modelo varchar(120) not null default '',
    registro_id varchar(80) not null default '',
    valor_anterior jsonb,
    valor_novo jsonb,
    ip inet,
    dispositivo varchar(255) not null default '',
    origem varchar(80) not null default 'sistema',
    justificativa text not null default '',
    nivel_risco varchar(20) not null default 'baixo',
    metadados jsonb not null default '{}',
    criado_em timestamptz not null
);

create index idx_logs_empresa_criado_em on logs_eventos (empresa_id, criado_em);
create index idx_logs_tipo_risco on logs_eventos (tipo_evento, nivel_risco);

create table centros_custo (
    id bigserial primary key,
    empresa_id bigint not null references empresas(id),
    codigo varchar(40) not null,
    nome varchar(120) not null,
    pai_id bigint references centros_custo(id),
    ativo boolean not null default true,
    criado_em timestamptz not null,
    atualizado_em timestamptz not null,
    unique (empresa_id, codigo)
);

create table plano_contas (
    id bigserial primary key,
    empresa_id bigint not null references empresas(id),
    codigo varchar(40) not null,
    nome varchar(120) not null,
    tipo varchar(30) not null,
    pai_id bigint references plano_contas(id),
    vincula_dre boolean not null default true,
    vincula_fluxo_caixa boolean not null default true,
    ativo boolean not null default true,
    criado_em timestamptz not null,
    atualizado_em timestamptz not null,
    unique (empresa_id, codigo)
);

create table contas_bancarias (
    id bigserial primary key,
    empresa_id bigint not null references empresas(id),
    banco varchar(80) not null,
    agencia varchar(20) not null default '',
    numero varchar(40) not null,
    descricao varchar(120) not null default '',
    saldo_inicial numeric(14, 2) not null default 0,
    ativa boolean not null default true,
    criado_em timestamptz not null,
    atualizado_em timestamptz not null
);

create table clientes (
    id bigserial primary key,
    empresa_id bigint not null references empresas(id),
    nome varchar(180) not null,
    tipo_pessoa varchar(20) not null,
    documento varchar(18) not null default '',
    email varchar(254) not null default '',
    telefone varchar(30) not null default '',
    ativo boolean not null default true,
    metadados jsonb not null default '{}',
    criado_em timestamptz not null,
    atualizado_em timestamptz not null
);

create table fornecedores (
    id bigserial primary key,
    empresa_id bigint not null references empresas(id),
    nome varchar(180) not null,
    tipo_pessoa varchar(20) not null,
    documento varchar(18) not null default '',
    email varchar(254) not null default '',
    telefone varchar(30) not null default '',
    ativo boolean not null default true,
    metadados jsonb not null default '{}',
    criado_em timestamptz not null,
    atualizado_em timestamptz not null
);

create table contas_pagar (
    id bigserial primary key,
    empresa_id bigint not null references empresas(id),
    fornecedor_id bigint not null references fornecedores(id),
    descricao varchar(180) not null,
    numero_documento varchar(80) not null default '',
    nota_fiscal varchar(80) not null default '',
    data_emissao date not null,
    data_vencimento date not null,
    valor_original numeric(14, 2) not null,
    valor_pago numeric(14, 2) not null default 0,
    desconto numeric(14, 2) not null default 0,
    juros numeric(14, 2) not null default 0,
    multa numeric(14, 2) not null default 0,
    acrescimo numeric(14, 2) not null default 0,
    centro_custo_id bigint references centros_custo(id),
    plano_conta_id bigint references plano_contas(id),
    conta_bancaria_id bigint references contas_bancarias(id),
    forma_pagamento varchar(80) not null default '',
    status varchar(30) not null default 'aberto',
    observacao text not null default '',
    excluido_logicamente boolean not null default false,
    criado_em timestamptz not null,
    atualizado_em timestamptz not null
);

create table contas_receber (
    id bigserial primary key,
    empresa_id bigint not null references empresas(id),
    cliente_id bigint not null references clientes(id),
    contrato varchar(80) not null default '',
    parcela integer,
    descricao varchar(180) not null,
    data_emissao date not null,
    data_vencimento date not null,
    valor_original numeric(14, 2) not null,
    valor_recebido numeric(14, 2) not null default 0,
    desconto numeric(14, 2) not null default 0,
    juros numeric(14, 2) not null default 0,
    multa numeric(14, 2) not null default 0,
    acrescimo numeric(14, 2) not null default 0,
    honorarios numeric(14, 2) not null default 0,
    centro_custo_id bigint references centros_custo(id),
    plano_conta_id bigint references plano_contas(id),
    conta_bancaria_id bigint references contas_bancarias(id),
    forma_recebimento varchar(80) not null default '',
    status varchar(30) not null default 'aberto',
    observacao text not null default '',
    excluido_logicamente boolean not null default false,
    criado_em timestamptz not null,
    atualizado_em timestamptz not null
);
