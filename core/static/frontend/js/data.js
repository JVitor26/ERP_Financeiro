export const ENDPOINTS = {
    token: "/api/auth/token/",
    refresh: "/api/auth/token/refresh/",
    me: "/api/auth/me/",
    empresas: "/api/core/empresas/",
    modulos: "/api/core/modulos/",
    empresaModulos: "/api/core/empresa-modulos/",
    eventos: "/api/core/eventos/",
    notificacoes: "/api/core/notificacoes/",
    centrosCusto: "/api/financeiro/centros-custo/",
    planoContas: "/api/financeiro/plano-contas/",
    contasBancarias: "/api/financeiro/contas-bancarias/",
    clientes: "/api/financeiro/clientes/",
    fornecedores: "/api/financeiro/fornecedores/",
    servicos: "/api/financeiro/servicos/",
    contasPagar: "/api/financeiro/contas-pagar/",
    contasReceber: "/api/financeiro/contas-receber/",
    movimentacoes: "/api/financeiro/movimentacoes/",
    conciliacoes: "/api/financeiro/conciliacoes/",
    aprovacoes: "/api/financeiro/aprovacoes-pagamento/",
    fluxo: "/api/financeiro/fluxo-caixa/",
    dashboard: "/api/financeiro/fluxo-caixa/dashboard/",
    dre: "/api/financeiro/fluxo-caixa/dre/",
    relatorios: "/api/financeiro/relatorios/",
    alertas: "/api/inteligencia/alertas/",
    anomalias: "/api/inteligencia/anomalias/",
    previsoes: "/api/inteligencia/previsoes/",
    // Contábil
    contasContabeis: "/api/contabil/contas-contabeis/",
    competenciasContabeis: "/api/contabil/competencias/",
    lancamentosContabeis: "/api/contabil/lancamentos/",
    relatoriosContabeis: "/api/contabil/relatorios/",
    // Fiscal
    configuracaoFiscal: "/api/fiscal/configuracao-fiscal/",
    notasFiscais: "/api/fiscal/notas-fiscais/",
    impostosApurados: "/api/fiscal/impostos-apurados/",
    obrigacoesFiscais: "/api/fiscal/obrigacoes-fiscais/",
    relatoriosFiscais: "/api/fiscal/relatorios/",
    // Financeiro avançado
    recorrencias: "/api/financeiro/recorrencias/",
    periodosFechamento: "/api/financeiro/periodos-fechamento/",
    alcadasAprovacao: "/api/financeiro/alcadas-aprovacao/",
    importacoesOFX: "/api/financeiro/importacoes-ofx/",
    cobrancas: "/api/financeiro/cobrancas/",
    regrasconciliacao: "/api/financeiro/regras-conciliacao/",
    transferenciasInternas: "/api/financeiro/transferencias-internas/",
    contratosFinanceiros: "/api/financeiro/contratos-financeiros/",
    aplicacoesFinanceiras: "/api/financeiro/aplicacoes-financeiras/",
};

export const STATUS_LABELS = {
    aberto: "Aberto",
    a_vencer: "A vencer",
    vencido: "Vencido",
    pago: "Pago",
    pago_parcial: "Pago parcial",
    recebido: "Recebido",
    recebido_parcial: "Recebido parcial",
    cancelado: "Cancelado",
    renegociado: "Renegociado",
    em_cobranca: "Em cobranca",
    judicial: "Judicial",
    protestado: "Protestado",
    em_aprovacao: "Em aprovacao",
    reprovado: "Reprovado",
    agendado: "Agendado",
    pendente: "Pendente",
    aprovado: "Aprovado",
    enviada: "Enviada",
    falhou: "Falhou",
    lida: "Lida",
    confirmado: "Confirmado",
    descartado: "Descartado",
    resolvido: "Resolvido",
    em_analise: "Em analise",
    sugerida: "Sugerida",
    conciliada: "Conciliada",
    divergente: "Divergente",
    duplicada: "Duplicada",
    receita: "Receita",
    despesa: "Despesa",
    custo: "Custo",
    investimento: "Investimento",
    imposto: "Imposto",
    taxa: "Taxa",
    comissao: "Comissao",
    repasse: "Repasse",
    financiamento: "Financiamento",
    emprestimo: "Emprestimo",
};

export const RISK_LABELS = {
    baixo: "Baixo",
    medio: "Medio",
    alto: "Alto",
    critico: "Critico",
};

export const EVENT_LABELS = {
    criacao: "Criacao",
    alteracao: "Alteracao",
    exclusao_logica: "Exclusao logica",
    baixa: "Baixa",
    aprovacao: "Aprovacao",
    reprovacao: "Reprovacao",
    exportacao: "Exportacao",
    acesso_sensivel: "Acesso sensivel",
    alerta_sistema: "Alerta sistema",
    alerta_ia: "Alerta IA",
    integracao: "Integracao",
};

export const FIELD_LABELS = {
    banco: "Banco",
    numero: "Numero",
    descricao: "Descricao",
    nome: "Nome",
    documento: "Documento",
    email: "E-mail",
    telefone: "Telefone",
    codigo: "Codigo",
    tipo: "Tipo",
    ativo: "Ativo",
    ativa: "Ativa",
    valor_original: "Valor",
    valor_total: "Total",
    saldo_pendente: "Saldo",
    data_vencimento: "Vencimento",
    status: "Status",
};

export const MONTH_NAMES = [
    "Jan",
    "Fev",
    "Mar",
    "Abr",
    "Mai",
    "Jun",
    "Jul",
    "Ago",
    "Set",
    "Out",
    "Nov",
    "Dez",
];

export function monthRange(date = new Date()) {
    const start = new Date(date.getFullYear(), date.getMonth(), 1);
    const end = new Date(date.getFullYear(), date.getMonth() + 1, 0);
    return {
        start: toISODate(start),
        end: toISODate(end),
    };
}

export function toISODate(date) {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, "0");
    const day = String(date.getDate()).padStart(2, "0");
    return `${year}-${month}-${day}`;
}

export function formatCurrency(value) {
    const number = toNumber(value);
    return new Intl.NumberFormat("pt-BR", {
        style: "currency",
        currency: "BRL",
        maximumFractionDigits: 2,
    }).format(number);
}

export function formatNumber(value) {
    return new Intl.NumberFormat("pt-BR", {
        maximumFractionDigits: 0,
    }).format(toNumber(value));
}

export function formatPercent(value) {
    return new Intl.NumberFormat("pt-BR", {
        style: "percent",
        maximumFractionDigits: 1,
    }).format(toNumber(value));
}

export function formatDate(value) {
    if (!value) {
        return "-";
    }
    const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
    if (Number.isNaN(date.getTime())) {
        return String(value);
    }
    return new Intl.DateTimeFormat("pt-BR", {
        day: "2-digit",
        month: "short",
        year: "numeric",
    }).format(date);
}

export function formatShortDate(value) {
    if (!value) {
        return "-";
    }
    const date = new Date(`${String(value).slice(0, 10)}T00:00:00`);
    if (Number.isNaN(date.getTime())) {
        return String(value);
    }
    return `${String(date.getDate()).padStart(2, "0")} ${MONTH_NAMES[date.getMonth()]}`;
}

export function toNumber(value) {
    if (value === null || value === undefined || value === "") {
        return 0;
    }
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
}

export function labelStatus(value) {
    return STATUS_LABELS[value] || value || "-";
}

export function labelRisk(value) {
    return RISK_LABELS[value] || value || "-";
}

export function labelEvent(value) {
    return EVENT_LABELS[value] || value || "-";
}

export function sumBy(items, selector) {
    return items.reduce((total, item) => total + toNumber(selector(item)), 0);
}

export function makeLookup(items, labelField = "nome") {
    return items.reduce((map, item) => {
        map[item.id] = item[labelField] || item.nome_fantasia || item.razao_social || item.descricao || `#${item.id}`;
        return map;
    }, {});
}

export function normalizeList(payload) {
    if (!payload) {
        return [];
    }
    if (Array.isArray(payload)) {
        return payload;
    }
    if (Array.isArray(payload.results)) {
        return payload.results;
    }
    return [];
}

export function buildQuery(params) {
    const search = new URLSearchParams();
    Object.entries(params || {}).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== "") {
            search.set(key, value);
        }
    });
    const query = search.toString();
    return query ? `?${query}` : "";
}

export function todayISO() {
    return toISODate(new Date());
}

export function daysUntil(value) {
    if (!value) {
        return 0;
    }
    const today = new Date(`${todayISO()}T00:00:00`);
    const due = new Date(`${String(value).slice(0, 10)}T00:00:00`);
    return Math.round((due - today) / 86400000);
}
