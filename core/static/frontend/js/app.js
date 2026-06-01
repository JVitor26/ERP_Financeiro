import { ApiClient } from "./api.js";
import {
    ENDPOINTS,
    buildQuery,
    daysUntil,
    formatCurrency,
    formatDate,
    formatNumber,
    formatPercent,
    formatShortDate,
    labelEvent,
    labelRisk,
    labelStatus,
    makeLookup,
    monthRange,
    normalizeList,
    sumBy,
    toNumber,
} from "./data.js";
import {
    $,
    $$,
    badge,
    closeModal,
    downloadBlob,
    drawCashflowChart,
    emptyState,
    escapeHtml,
    icon,
    openModal,
    renderTable,
    riskTone,
    serializeForm,
    setBusy,
    statusTone,
    toast,
} from "./ui.js";

const api = new ApiClient();
const initialPeriod = monthRange();
const VALUES_HIDDEN_KEY = "erp_financeiro_values_hidden";

const state = {
    activeView: "dashboard",
    ledger: "receber",
    period: initialPeriod,
    search: "",
    valuesHidden: localStorage.getItem(VALUES_HIDDEN_KEY) === "1",
    dreCollapsed: new Set(),
    user: null,
    empresa: null,
    data: blankData(),
    lookups: {},
};

api.onUnauthorized = () => {
    showAuth();
    toast("Sessao expirada. Entre novamente.", "warn");
};

document.addEventListener("DOMContentLoaded", init);
window.addEventListener("resize", debounce(() => drawCashflowChart($("#cashflow-chart"), buildChartSeries()), 120));

function init() {
    bindShellEvents();
    $("#period-start").value = state.period.start;
    $("#period-end").value = state.period.end;
    updateValuePrivacyButton();

    if (api.hasSession()) {
        bootSession().catch((error) => {
            console.error(error);
            showAuth();
        });
    } else {
        showAuth();
    }
}

function bindShellEvents() {
    $("#login-form").addEventListener("submit", handleLogin);
    $("#logout-button").addEventListener("click", () => {
        api.clearTokens();
        showAuth();
    });
    $$(".nav-item").forEach((item) => {
        item.addEventListener("click", () => showView(item.dataset.view));
    });
    $$(".segment").forEach((item) => {
        item.addEventListener("click", () => {
            state.ledger = item.dataset.ledger;
            $$(".segment").forEach((segment) => segment.classList.toggle("is-active", segment === item));
            renderLedger();
        });
    });
    $("#apply-period").addEventListener("click", async () => {
        state.period = {
            start: $("#period-start").value || initialPeriod.start,
            end: $("#period-end").value || initialPeriod.end,
        };
        await loadWorkspace();
    });
    $("#refresh-button").addEventListener("click", () => loadWorkspace());
    $("#toggle-values").addEventListener("click", () => {
        state.valuesHidden = !state.valuesHidden;
        localStorage.setItem(VALUES_HIDDEN_KEY, state.valuesHidden ? "1" : "0");
        updateValuePrivacyButton();
        renderAll();
    });
    $("#global-search").addEventListener("input", debounce((event) => {
        state.search = event.target.value.trim().toLowerCase();
        renderActiveView();
    }, 140));
    $("#new-payable").addEventListener("click", () => openEntryModal("pagar"));
    $("#new-receivable").addEventListener("click", () => openEntryModal("receber"));
    $("#run-ai-scan").addEventListener("click", runAiScan);
    $("#run-forecast").addEventListener("click", runForecast);
    $("#report-form").addEventListener("submit", downloadReport);
}

async function handleLogin(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const errorBox = $("#login-error");
    errorBox.textContent = "";
    setBusy(button, true);
    try {
        const payload = serializeForm(form);
        await api.login(ENDPOINTS.token, payload);
        await bootSession();
        form.reset();
    } catch (error) {
        errorBox.textContent = error.message || "Nao foi possivel entrar.";
    } finally {
        setBusy(button, false);
    }
}

async function bootSession() {
    showApp();
    state.user = await api.get(ENDPOINTS.me);
    await loadWorkspace();
    updateIdentity();
    renderAll();
}

async function loadWorkspace() {
    const button = $("#refresh-button");
    setBusy(button, true);
    try {
        const params = {
            data_inicio: state.period.start,
            data_fim: state.period.end,
        };
        const [
            empresas,
            modulos,
            empresaModulos,
            dashboard,
            fluxo,
            dre,
            contasPagar,
            contasReceber,
            movimentacoes,
            contasBancarias,
            clientes,
            fornecedores,
            servicos,
            centrosCusto,
            planoContas,
            conciliacoes,
            aprovacoes,
            alertas,
            anomalias,
            previsoes,
            eventos,
            notificacoes,
        ] = await Promise.all([
            safeList(ENDPOINTS.empresas, { page_size: 100 }),
            safeList(ENDPOINTS.modulos, { page_size: 100 }),
            safeList(ENDPOINTS.empresaModulos, { page_size: 100 }),
            safeGet(`${ENDPOINTS.dashboard}${buildQuery(params)}`, {}),
            safeGet(`${ENDPOINTS.fluxo}${buildQuery(params)}`, {}),
            safeGet(`${ENDPOINTS.dre}${buildQuery(params)}`, {}),
            safeList(ENDPOINTS.contasPagar, { page_size: 100, ordering: "data_vencimento" }),
            safeList(ENDPOINTS.contasReceber, { page_size: 100, ordering: "data_vencimento" }),
            safeList(ENDPOINTS.movimentacoes, { page_size: 160, ordering: "-data_movimento" }),
            safeList(ENDPOINTS.contasBancarias, { page_size: 100 }),
            safeList(ENDPOINTS.clientes, { page_size: 120 }),
            safeList(ENDPOINTS.fornecedores, { page_size: 120 }),
            safeList(ENDPOINTS.servicos, { page_size: 120 }),
            safeList(ENDPOINTS.centrosCusto, { page_size: 100 }),
            safeList(ENDPOINTS.planoContas, { page_size: 160 }),
            safeList(ENDPOINTS.conciliacoes, { page_size: 100, ordering: "-data_movimento" }),
            safeList(ENDPOINTS.aprovacoes, { page_size: 100 }),
            safeList(ENDPOINTS.alertas, { page_size: 100, ordering: "-criado_em" }),
            safeList(ENDPOINTS.anomalias, { page_size: 100, ordering: "-criado_em" }),
            safeList(ENDPOINTS.previsoes, { page_size: 100, ordering: "-data_referencia" }),
            safeList(ENDPOINTS.eventos, { page_size: 120, ordering: "-criado_em" }),
            safeList(ENDPOINTS.notificacoes, { page_size: 80 }),
        ]);

        state.data = {
            empresas,
            modulos,
            empresaModulos,
            dashboard,
            fluxo,
            dre,
            contasPagar,
            contasReceber,
            movimentacoes,
            contasBancarias,
            clientes,
            fornecedores,
            servicos,
            centrosCusto,
            planoContas,
            conciliacoes,
            aprovacoes,
            alertas,
            anomalias,
            previsoes,
            eventos,
            notificacoes,
        };
        state.empresa = empresas.find((empresa) => empresa.id === state.user?.empresa) || empresas[0] || null;
        state.lookups = buildLookups(state.data);
        updateIdentity();
        renderAll();
        toast("Painel atualizado.", "good");
    } catch (error) {
        console.error(error);
        toast(error.message || "Falha ao atualizar painel.", "danger");
    } finally {
        setBusy(button, false);
    }
}

async function safeList(path, params) {
    try {
        return await api.list(path, params);
    } catch (error) {
        console.warn(path, error);
        return [];
    }
}

async function safeGet(path, fallback) {
    try {
        return await api.request(path);
    } catch (error) {
        console.warn(path, error);
        return fallback;
    }
}

function blankData() {
    return {
        empresas: [],
        modulos: [],
        empresaModulos: [],
        dashboard: {},
        fluxo: {},
        dre: {},
        contasPagar: [],
        contasReceber: [],
        movimentacoes: [],
        contasBancarias: [],
        clientes: [],
        fornecedores: [],
        servicos: [],
        centrosCusto: [],
        planoContas: [],
        conciliacoes: [],
        aprovacoes: [],
        alertas: [],
        anomalias: [],
        previsoes: [],
        eventos: [],
        notificacoes: [],
    };
}

function buildLookups(data) {
    return {
        empresas: makeLookup(data.empresas, "nome_fantasia"),
        clientes: makeLookup(data.clientes, "nome"),
        fornecedores: makeLookup(data.fornecedores, "nome"),
        servicos: makeLookup(data.servicos, "nome"),
        contasBancarias: data.contasBancarias.reduce((map, conta) => {
            map[conta.id] = `${conta.banco} ${conta.numero}`;
            return map;
        }, {}),
        centrosCusto: makeLookup(data.centrosCusto, "nome"),
        planoContas: makeLookup(data.planoContas, "nome"),
        modulos: makeLookup(data.modulos, "nome"),
    };
}

function showAuth() {
    $("#auth-view").classList.remove("is-hidden");
    $("#app-view").classList.add("is-hidden");
}

function showApp() {
    $("#auth-view").classList.add("is-hidden");
    $("#app-view").classList.remove("is-hidden");
}

function updateIdentity() {
    const user = state.user || {};
    const companyName = state.empresa?.nome_fantasia || state.empresa?.razao_social || "Empresa";
    $("#tenant-label").textContent = companyName;
    $("#user-name").textContent = user.first_name || user.username || "Usuario";
    $("#user-role").textContent = user.is_staff ? "Administrador" : "Operacao";
    $("#user-avatar").textContent = (user.first_name || user.username || "U").slice(0, 1).toUpperCase();
}

function updateValuePrivacyButton() {
    const button = $("#toggle-values");
    if (!button) {
        return;
    }
    button.title = state.valuesHidden ? "Mostrar valores" : "Ocultar valores";
    button.setAttribute("aria-pressed", state.valuesHidden ? "true" : "false");
    button.innerHTML = icon(state.valuesHidden ? "eye" : "eye-off");
}

function showView(view) {
    state.activeView = view;
    $$(".nav-item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === view));
    $$(".screen").forEach((screen) => screen.classList.toggle("is-active", screen.id === `${view}-view`));
    const active = $(`#${view}-view`);
    $("#view-title").textContent = active.dataset.title || "Painel";
    $("#view-kicker").textContent = active.dataset.kicker || "ERP";
    renderActiveView();
}

function renderAll() {
    renderDashboard();
    renderLedger();
    renderApprovals();
    renderRegistries();
    renderIntelligence();
    renderAudit();
    renderCompanies();
    renderReports();
    showView(state.activeView);
}

function renderActiveView() {
    const renderers = {
        dashboard: renderDashboard,
        lancamentos: renderLedger,
        aprovacoes: renderApprovals,
        cadastros: renderRegistries,
        inteligencia: renderIntelligence,
        auditoria: renderAudit,
        empresas: renderCompanies,
        relatorios: renderReports,
    };
    const renderer = renderers[state.activeView];
    if (renderer) {
        renderer();
    }
}

function renderDashboard() {
    const dashboard = state.data.dashboard || {};
    const inadimplencia = toNumber(dashboard.inadimplencia);
    const totalReceber = toNumber(dashboard.total_a_receber);
    const inadimplenciaRate = totalReceber ? inadimplencia / totalReceber : 0;
    const kpis = [
        {
            label: "Saldo previsto",
            value: money(dashboard.saldo_previsto),
            note: "Recebiveis menos pagamentos",
            tone: toNumber(dashboard.saldo_previsto) >= 0 ? "good" : "danger",
        },
        {
            label: "Resultado",
            value: money(dashboard.resultado_periodo),
            note: "Entradas menos saidas realizadas",
            tone: toNumber(dashboard.resultado_periodo) >= 0 ? "good" : "danger",
        },
        {
            label: "A receber",
            value: money(dashboard.total_a_receber),
            note: `${formatNumber(dashboard.titulos_receber_abertos)} titulos abertos`,
            tone: "neutral",
        },
        {
            label: "A pagar",
            value: money(dashboard.total_a_pagar),
            note: `${formatNumber(dashboard.titulos_pagar_abertos)} titulos abertos`,
            tone: "warn",
        },
        {
            label: "Inadimplencia",
            value: money(inadimplencia),
            note: formatPercent(inadimplenciaRate),
            tone: inadimplencia > 0 ? "danger" : "good",
        },
        {
            label: "Hoje",
            value: money(toNumber(dashboard.contas_receber_hoje) - toNumber(dashboard.contas_pagar_hoje)),
            note: "Liquido do dia",
            tone: "neutral",
        },
    ];
    $("#kpi-grid").innerHTML = kpis.map(renderKpi).join("");
    $("#cashflow-badge").textContent = `${formatShortDate(state.period.start)} - ${formatShortDate(state.period.end)}`;
    drawCashflowChart($("#cashflow-chart"), buildChartSeries());
    renderRiskPanel();
    renderUpcoming();
    renderDre();
}

function renderKpi(item) {
    return `
        <article class="kpi-card ${item.tone ? `tone-${item.tone}` : ""}">
            <span>${escapeHtml(item.label)}</span>
            <strong>${escapeHtml(item.value)}</strong>
            <small>${escapeHtml(item.note)}</small>
        </article>
    `;
}

function money(value, options = {}) {
    if (state.valuesHidden) {
        return "R$ ***";
    }
    const amount = options.absolute ? Math.abs(toNumber(value)) : value;
    return formatCurrency(amount);
}

function buildChartSeries() {
    const byDate = {};
    state.data.movimentacoes.forEach((mov) => {
        const key = String(mov.data_movimento || "").slice(0, 10);
        if (!key) {
            return;
        }
        byDate[key] = byDate[key] || { entrada: 0, saida: 0 };
        if (mov.tipo === "entrada") {
            byDate[key].entrada += toNumber(mov.valor);
        } else {
            byDate[key].saida += toNumber(mov.valor);
        }
    });
    let saldo = 0;
    const rows = Object.keys(byDate)
        .sort()
        .slice(-18)
        .map((date) => {
            saldo += byDate[date].entrada - byDate[date].saida;
            return {
                label: formatShortDate(date),
                entrada: byDate[date].entrada,
                saida: byDate[date].saida,
                saldo,
            };
        });
    if (rows.length === 0) {
        const dashboard = state.data.dashboard || {};
        return [
            { label: "Prev.", entrada: toNumber(dashboard.total_a_receber), saida: toNumber(dashboard.total_a_pagar), saldo: toNumber(dashboard.saldo_previsto) },
            { label: "Real.", entrada: toNumber(dashboard.entradas_realizadas), saida: toNumber(dashboard.saidas_realizadas), saldo: toNumber(dashboard.saldo_realizado) },
        ];
    }
    return rows;
}

function renderRiskPanel() {
    const risks = ["critico", "alto", "medio", "baixo"].map((risk) => {
        const alerts = state.data.alertas.filter((item) => item.nivel_risco === risk).length;
        const anomalies = state.data.anomalias.filter((item) => item.nivel_risco === risk).length;
        return { risk, count: alerts + anomalies };
    });
    const openAnomalies = state.data.anomalias.filter((item) => !["resolvido", "descartado"].includes(item.status)).slice(0, 4);
    $("#risk-panel").innerHTML = `
        <div class="risk-stack">
            ${risks
                .map((item) => `
                    <div class="risk-row">
                        ${badge(labelRisk(item.risk), riskTone(item.risk))}
                        <strong>${formatNumber(item.count)}</strong>
                    </div>
                `)
                .join("")}
        </div>
        <div class="mini-list">
            ${
                openAnomalies.length
                    ? openAnomalies.map((item) => `<span>${escapeHtml(item.descricao)}</span>`).join("")
                    : "<span>Nenhum risco aberto no periodo.</span>"
            }
        </div>
    `;
}

function renderUpcoming() {
    const rows = [
        ...state.data.contasReceber.map((item) => ({ ...item, kind: "receber", partner: state.lookups.clientes[item.cliente] || "Cliente" })),
        ...state.data.contasPagar.map((item) => ({ ...item, kind: "pagar", partner: state.lookups.fornecedores[item.fornecedor] || "Fornecedor" })),
    ]
        .filter((item) => !["pago", "recebido", "cancelado"].includes(item.status))
        .sort((a, b) => String(a.data_vencimento).localeCompare(String(b.data_vencimento)))
        .slice(0, 8);

    $("#upcoming-list").innerHTML = rows.length
        ? rows
              .map((item) => {
                  const due = daysUntil(item.data_vencimento);
                  const dueText = due < 0 ? `${Math.abs(due)}d atraso` : due === 0 ? "Hoje" : `${due}d`;
                  return `
                    <article class="timeline-item">
                        <span class="timeline-marker ${item.kind === "receber" ? "in" : "out"}"></span>
                        <div>
                            <strong>${escapeHtml(item.partner)}</strong>
                            <small>${escapeHtml(item.descricao || "")}</small>
                        </div>
                        <div class="timeline-value">
                            <strong>${money(item.saldo_pendente || item.valor_total || item.valor_original)}</strong>
                            <small>${escapeHtml(dueText)}</small>
                        </div>
                    </article>
                `;
              })
              .join("")
        : emptyState("Agenda limpa", "Nao ha vencimentos abertos.");
}

function renderDre() {
    const dre = state.data.dre || {};
    const rows = dre.linhas || [
        ["Receita bruta", dre.receita_bruta, "+"],
        ["Receita liquida", dre.receita_liquida, "="],
        ["Margem de contribuicao", dre.margem_contribuicao, "="],
        ["Despesas operacionais", dre.despesas_operacionais, "-"],
        ["Resultado operacional", dre.resultado_operacional, "="],
        ["Lucro / prejuizo", dre.lucro_prejuizo, "="],
    ].map(([label, valor, operador]) => ({ label, valor, operador }));
    const centros = filterRows(dre.centros_custo || [], ["codigo", "nome"]);
    const planos = filterRows(dre.planos_contas || [], ["codigo", "nome", "tipo"]);

    $("#dre-table").innerHTML = `
        <div class="dre-layout">
            ${renderDreStatement(rows, planos)}
            <div class="dre-subsection">
                <div class="section-heading compact-heading">
                    <div>
                        <p class="eyebrow">Centros de custo</p>
                        <h3>Resultado por centro</h3>
                    </div>
                </div>
                ${renderTable({
                    compact: true,
                    columns: [
                        { label: "Centro", render: (row) => `<strong>${escapeHtml(row.codigo || "-")}</strong><span class="table-subtext">${escapeHtml(row.nome)}</span>` },
                        { label: "Entradas", align: "right", render: (row) => dreAmount(row.entradas, "+") },
                        { label: "Saidas", align: "right", render: (row) => dreAmount(row.saidas, "-") },
                        { label: "Resultado", align: "right", render: (row) => dreAmount(row.resultado, "=") },
                        { label: "Transacoes", align: "right", render: (row) => formatNumber(row.transacoes) },
                    ],
                    rows: centros,
                    emptyTitle: "Sem centros de custo",
                })}
            </div>
            <div class="dre-subsection">
                <div class="section-heading compact-heading">
                    <div>
                        <p class="eyebrow">Plano de contas</p>
                        <h3>Abertura contabil</h3>
                    </div>
                </div>
                ${renderTable({
                    compact: true,
                    columns: [
                        { label: "Conta", render: (row) => `<strong>${escapeHtml(row.codigo || "-")}</strong><span class="table-subtext">${escapeHtml(row.nome)}</span>` },
                        { label: "Tipo", render: (row) => badge(labelStatus(row.tipo), "neutral") },
                        { label: "Entradas", align: "right", render: (row) => dreAmount(row.entradas, "+") },
                        { label: "Saidas", align: "right", render: (row) => dreAmount(row.saidas, "-") },
                        { label: "Resultado", align: "right", render: (row) => dreAmount(row.resultado, "=") },
                    ],
                    rows: planos,
                    emptyTitle: "Sem plano de contas",
                })}
            </div>
        </div>
    `;
    bindDreToggles();
}

function renderDreStatement(rows, planos) {
    if (!rows.length) {
        return emptyState("DRE sem dados");
    }
    return `
        <div class="data-table compact dre-statement">
            <table>
                <thead>
                    <tr>
                        <th></th>
                        <th>Indicador</th>
                        <th class="align-right">Valor</th>
                    </tr>
                </thead>
                <tbody>
                    ${rows.map((row) => renderDreLine(row, planos)).join("")}
                </tbody>
            </table>
        </div>
    `;
}

function renderDreLine(row, planos) {
    const details = dreDetailsFor(row, planos);
    const key = dreGroupKey(row);
    const hasDetails = details.length > 0;
    const collapsed = hasDetails && state.dreCollapsed.has(key);
    const classes = ["dre-main-row"];
    if (hasDetails) {
        classes.push("is-toggleable");
    }
    if (collapsed) {
        classes.push("is-collapsed");
    }
    return `
        <tr class="${classes.join(" ")}" ${hasDetails ? `data-dre-toggle="${escapeHtml(key)}" title="Mostrar ou ocultar detalhes"` : ""}>
            <td>${dreOperator(row.operador, row.valor, hasDetails, collapsed)}</td>
            <td>${escapeHtml(row.label)}</td>
            <td class="align-right">${dreAmount(row.valor, row.operador)}</td>
        </tr>
        ${collapsed ? "" : details.map(renderDreDetailLine).join("")}
    `;
}

function renderDreDetailLine(row) {
    return `
        <tr class="dre-detail-row">
            <td>${dreOperator(row.operador, row.valor)}</td>
            <td>
                <span class="dre-detail-name">${escapeHtml(row.codigo || "-")} - ${escapeHtml(row.nome)}</span>
                <span class="table-subtext">${escapeHtml(row.tipoLabel)}</span>
            </td>
            <td class="align-right">${dreAmount(row.valor, row.operador)}</td>
        </tr>
    `;
}

function dreDetailsFor(row, planos) {
    const group = row.grupo || "";
    const deductionTypes = ["imposto", "taxa", "comissao", "repasse"];
    const commonOutputTypes = [...deductionTypes, "custo", "despesa", "investimento"];
    return planos
        .map((plano) => ({
            ...plano,
            entradas: toNumber(plano.entradas),
            saidas: toNumber(plano.saidas),
        }))
        .filter((plano) => {
            if (group === "receita") {
                return plano.entradas > 0;
            }
            if (group === "deducao") {
                return deductionTypes.includes(plano.tipo) && plano.saidas > 0;
            }
            if (group === "custo") {
                return plano.tipo === "custo" && plano.saidas > 0;
            }
            if (group === "despesa") {
                return plano.tipo === "despesa" && plano.saidas > 0;
            }
            if (group === "investimento") {
                return plano.saidas > 0 && (plano.tipo === "investimento" || !commonOutputTypes.includes(plano.tipo));
            }
            return false;
        })
        .map((plano) => ({
            codigo: plano.codigo,
            nome: plano.nome,
            tipoLabel: labelStatus(plano.tipo),
            operador: group === "receita" ? "+" : "-",
            valor: group === "receita" ? plano.entradas : plano.saidas,
        }));
}

function dreGroupKey(row) {
    return String(row.grupo || row.label || "")
        .toLowerCase()
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "");
}

function bindDreToggles() {
    $$("[data-dre-toggle]").forEach((row) => {
        row.addEventListener("click", () => {
            const key = row.dataset.dreToggle;
            if (state.dreCollapsed.has(key)) {
                state.dreCollapsed.delete(key);
            } else {
                state.dreCollapsed.add(key);
            }
            renderDre();
        });
    });
}

function dreOperator(operator, value, toggleable = false, collapsed = false) {
    const tone = operator === "-" ? "negative" : operator === "+" || toNumber(value) >= 0 ? "positive" : "negative";
    const title = toggleable ? (collapsed ? "Clique para abrir" : "Clique para ocultar") : "";
    return `<span class="dre-sign dre-${tone} ${toggleable ? "is-toggleable" : ""}" title="${escapeHtml(title)}">${escapeHtml(operator || "=")}</span>`;
}

function dreAmount(value, operator = "=") {
    const number = toNumber(value);
    const tone = operator === "-" ? "negative" : operator === "+" || number >= 0 ? "positive" : "negative";
    return `<strong class="dre-value dre-${tone}">${money(number, { absolute: true })}</strong>`;
}

function renderLedger() {
    const isReceivable = state.ledger === "receber";
    const rows = filterRows(isReceivable ? state.data.contasReceber : state.data.contasPagar, ["descricao", "status", "numero_documento", "contrato"]);
    const collection = isReceivable ? state.data.contasReceber : state.data.contasPagar;
    const open = collection.filter((item) => !["pago", "recebido", "cancelado"].includes(item.status));
    const totalOpen = sumBy(open, (item) => item.saldo_pendente || item.valor_total || item.valor_original);
    const overdue = open.filter((item) => daysUntil(item.data_vencimento) < 0);

    $("#ledger-summary").innerHTML = [
        {
            label: isReceivable ? "Recebiveis abertos" : "Pagamentos abertos",
            value: money(totalOpen),
            note: `${open.length} titulos`,
            tone: isReceivable ? "good" : "warn",
        },
        {
            label: "Vencidos",
            value: money(sumBy(overdue, (item) => item.saldo_pendente || item.valor_total || item.valor_original)),
            note: `${overdue.length} em atraso`,
            tone: overdue.length ? "danger" : "good",
        },
        {
            label: "Media por titulo",
            value: money(open.length ? totalOpen / open.length : 0),
            note: "Saldo medio",
            tone: "neutral",
        },
    ].map(renderKpi).join("");

    const partnerLookup = isReceivable ? state.lookups.clientes : state.lookups.fornecedores;
    const partnerKey = isReceivable ? "cliente" : "fornecedor";
    $("#ledger-table").innerHTML = renderTable({
        columns: [
            { label: "Vencimento", render: (row) => formatDate(row.data_vencimento) },
            { label: isReceivable ? "Cliente" : "Fornecedor", render: (row) => escapeHtml(partnerLookup[row[partnerKey]] || `#${row[partnerKey]}`) },
            { label: "Descricao", render: (row) => escapeHtml(row.descricao) },
            { label: "Total", align: "right", render: (row) => money(row.valor_total || row.valor_original) },
            { label: "Saldo", align: "right", render: (row) => `<strong>${money(row.saldo_pendente || 0)}</strong>` },
            { label: "Status", render: (row) => badge(labelStatus(row.status), statusTone(row.status)) },
            {
                label: "Acao",
                render: (row) => ledgerAction(row, isReceivable),
            },
        ],
        rows,
        emptyTitle: "Nenhum lancamento encontrado",
    });

    bindLedgerActions();
}

function ledgerAction(row, isReceivable) {
    const closed = isReceivable ? ["recebido", "cancelado"].includes(row.status) : ["pago", "cancelado", "reprovado"].includes(row.status);
    if (closed) {
        return `<span class="muted">Concluido</span>`;
    }
    const pendingApproval = !isReceivable && state.data.aprovacoes.some((item) => String(item.conta_pagar) === String(row.id) && item.status === "pendente");
    if (pendingApproval) {
        return `
            <div class="table-actions">
                <button class="mini-button ghost" data-go-approvals type="button">Ver aprovacao</button>
            </div>
        `;
    }
    if (!isReceivable && row.status === "agendado") {
        return `
            <div class="table-actions">
                <button class="mini-button" data-settle="${row.id}" data-kind="pagar" type="button">Baixar</button>
                <span class="muted">Aprovado</span>
            </div>
        `;
    }
    return `
        <div class="table-actions">
            <button class="mini-button" data-settle="${row.id}" data-kind="${isReceivable ? "receber" : "pagar"}" type="button">
                ${isReceivable ? "Receber" : "Baixar"}
            </button>
            ${
                isReceivable
                    ? `<button class="mini-button ghost" data-renegotiate="${row.id}" type="button">Renegociar</button>`
                    : `<button class="mini-button ghost" data-approval="${row.id}" type="button">Solicitar aprovacao</button>`
            }
        </div>
    `;
}

function bindLedgerActions() {
    $$("[data-settle]").forEach((button) => {
        button.addEventListener("click", () => openSettlementModal(button.dataset.kind, button.dataset.settle));
    });
    $$("[data-approval]").forEach((button) => {
        button.addEventListener("click", () => requestApproval(button.dataset.approval, button));
    });
    $$("[data-go-approvals]").forEach((button) => {
        button.addEventListener("click", () => showView("aprovacoes"));
    });
    $$("[data-renegotiate]").forEach((button) => {
        button.addEventListener("click", () => openRenegotiationModal(button.dataset.renegotiate));
    });
}

function renderApprovals() {
    const rows = filterApprovals(state.data.aprovacoes);
    const pending = rows.filter((item) => item.status === "pendente");
    const decided = rows.filter((item) => item.status !== "pendente");
    const pendingTotal = sumBy(pending, (item) => approvalDetails(item).valor);
    const approved = state.data.aprovacoes.filter((item) => item.status === "aprovado");
    const rejected = state.data.aprovacoes.filter((item) => item.status === "reprovado");

    $("#approval-summary").innerHTML = [
        {
            label: "Pendentes",
            value: formatNumber(pending.length),
            note: money(pendingTotal),
            tone: pending.length ? "warn" : "good",
        },
        {
            label: "Aprovados",
            value: formatNumber(approved.length),
            note: "Pagamentos liberados",
            tone: "good",
        },
        {
            label: "Reprovados",
            value: formatNumber(rejected.length),
            note: "Retornaram para revisao",
            tone: rejected.length ? "danger" : "neutral",
        },
    ].map(renderKpi).join("");

    $("#approvals-table").innerHTML = renderTable({
        rows: pending,
        emptyTitle: "Sem aprovacoes pendentes",
        columns: [
            { label: "Solicitada", render: (row) => formatDate(row.criado_em) },
            {
                label: "Pagamento",
                render: (row) => {
                    const details = approvalDetails(row);
                    return `
                        <strong>${escapeHtml(details.fornecedor)}</strong>
                        <small class="table-subtext">${escapeHtml(details.descricao || "-")}</small>
                    `;
                },
            },
            { label: "Vencimento", render: (row) => formatDate(approvalDetails(row).vencimento) },
            { label: "Valor", align: "right", render: (row) => `<strong>${money(approvalDetails(row).valor)}</strong>` },
            { label: "Solicitante", render: (row) => escapeHtml(approvalDetails(row).solicitante) },
            { label: "Status", render: (row) => badge(labelStatus(row.status), statusTone(row.status)) },
            {
                label: "Acao",
                render: (row) => `
                    <div class="table-actions">
                        <button class="mini-button" data-approve="${row.id}" type="button">Aprovar</button>
                        <button class="mini-button ghost" data-reject="${row.id}" type="button">Reprovar</button>
                    </div>
                `,
            },
        ],
    });
    bindApprovalActions();

    $("#approval-history").innerHTML = decided.length
        ? decided.slice(0, 8).map(renderApprovalHistoryItem).join("")
        : emptyState("Sem decisoes", "As aprovacoes concluidas aparecem aqui.");
}

function bindApprovalActions() {
    $$("[data-approve]").forEach((button) => {
        button.addEventListener("click", () => openApprovalDecisionModal(button.dataset.approve, true));
    });
    $$("[data-reject]").forEach((button) => {
        button.addEventListener("click", () => openApprovalDecisionModal(button.dataset.reject, false));
    });
}

function renderApprovalHistoryItem(item) {
    const details = approvalDetails(item);
    const marker = item.status === "aprovado" ? "in" : "alert";
    return `
        <article class="timeline-item">
            <span class="timeline-marker ${marker}"></span>
            <div>
                <strong>${escapeHtml(details.fornecedor)}</strong>
                <small>${escapeHtml(details.descricao || "-")}</small>
            </div>
            <div class="timeline-value">
                ${badge(labelStatus(item.status), statusTone(item.status))}
                <small>${formatDate(item.decidido_em || item.atualizado_em)} por ${escapeHtml(details.aprovador)}</small>
            </div>
        </article>
    `;
}

function filterApprovals(rows) {
    if (!state.search) {
        return rows;
    }
    return rows.filter((item) => {
        const details = approvalDetails(item);
        return [
            item.status,
            item.justificativa,
            details.fornecedor,
            details.descricao,
            details.numero,
            details.solicitante,
            details.aprovador,
        ].some((value) => String(value ?? "").toLowerCase().includes(state.search));
    });
}

function approvalDetails(item) {
    const conta = state.data.contasPagar.find((row) => String(row.id) === String(item.conta_pagar)) || {};
    const details = item.conta_pagar_detalhes || {};
    return {
        fornecedor: details.fornecedor || state.lookups.fornecedores[conta.fornecedor] || "Fornecedor",
        descricao: details.descricao || conta.descricao || "",
        numero: details.numero_documento || conta.numero_documento || "",
        valor: details.valor_total ?? conta.valor_total ?? conta.valor_original ?? 0,
        vencimento: details.data_vencimento || conta.data_vencimento || "",
        solicitante: item.solicitante_nome || (item.solicitante ? `#${item.solicitante}` : "-"),
        aprovador: item.aprovador_nome || (item.aprovador ? `#${item.aprovador}` : "-"),
    };
}

function openApprovalDecisionModal(id, approved) {
    const approval = state.data.aprovacoes.find((item) => String(item.id) === String(id));
    if (!approval) {
        toast("Aprovacao nao encontrada.", "danger");
        return;
    }
    const details = approvalDetails(approval);
    openModal({
        title: approved ? "Aprovar pagamento" : "Reprovar pagamento",
        subtitle: details.fornecedor,
        body: `
            <form id="approval-decision-form" class="modal-form">
                <div class="settlement-resume">
                    <span>${escapeHtml(details.descricao || "Pagamento")}</span>
                    <strong>${money(details.valor)}</strong>
                </div>
                <div class="form-grid">
                    <label>Vencimento<input value="${escapeHtml(formatDate(details.vencimento))}" readonly></label>
                    <label>Solicitante<input value="${escapeHtml(details.solicitante)}" readonly></label>
                    <label class="span-2">Justificativa<textarea name="justificativa" rows="3" ${approved ? "" : "required"}>${approved ? "Aprovado pelo painel web." : ""}</textarea></label>
                </div>
                <button class="btn btn-primary btn-wide" type="submit">
                    ${icon(approved ? "check" : "x")}${approved ? "Confirmar aprovacao" : "Confirmar reprovacao"}
                </button>
            </form>
        `,
    });
    $("#approval-decision-form").addEventListener("submit", (event) => submitApprovalDecision(event, id, approved));
}

async function submitApprovalDecision(event, id, approved) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const action = approved ? "aprovar" : "reprovar";
    setBusy(button, true);
    try {
        await api.post(`${ENDPOINTS.aprovacoes}${id}/${action}/`, serializeForm(form));
        closeModal();
        toast(approved ? "Pagamento aprovado." : "Pagamento reprovado.", "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Nao foi possivel decidir a aprovacao.", "danger");
    } finally {
        setBusy(button, false);
    }
}

function renderRegistries() {
    const grids = [
        {
            kind: "cliente",
            title: "Clientes",
            buttonLabel: "Novo cliente",
            kicker: `${state.data.clientes.length} clientes`,
            rows: filterRows(state.data.clientes, ["nome", "documento", "email"]),
            columns: [
                { label: "Nome", render: (row) => escapeHtml(row.nome) },
                { label: "Documento", render: (row) => escapeHtml(row.documento || "-") },
                { label: "Contato", render: (row) => escapeHtml(row.email || row.telefone || "-") },
            ],
        },
        {
            kind: "fornecedor",
            title: "Fornecedores",
            buttonLabel: "Novo fornecedor",
            kicker: `${state.data.fornecedores.length} fornecedores`,
            rows: filterRows(state.data.fornecedores, ["nome", "documento", "email"]),
            columns: [
                { label: "Nome", render: (row) => escapeHtml(row.nome) },
                { label: "Documento", render: (row) => escapeHtml(row.documento || "-") },
                { label: "Contato", render: (row) => escapeHtml(row.email || row.telefone || "-") },
            ],
        },
        {
            kind: "servico",
            title: "Servicos",
            buttonLabel: "Novo servico",
            kicker: `${state.data.servicos.length} servicos`,
            rows: filterRows(state.data.servicos, ["codigo", "nome", "descricao"]),
            columns: [
                { label: "Codigo", render: (row) => escapeHtml(row.codigo || "-") },
                { label: "Nome", render: (row) => escapeHtml(row.nome) },
                { label: "Valor", align: "right", render: (row) => money(row.valor_padrao) },
                { label: "Status", render: (row) => badge(row.ativo ? "Ativo" : "Inativo", row.ativo ? "good" : "neutral") },
            ],
        },
        {
            kind: "conta-bancaria",
            title: "Contas bancarias",
            buttonLabel: "Nova conta",
            kicker: `${state.data.contasBancarias.length} contas`,
            rows: filterRows(state.data.contasBancarias, ["banco", "numero", "descricao"]),
            columns: [
                { label: "Banco", render: (row) => escapeHtml(row.banco) },
                { label: "Numero", render: (row) => escapeHtml(row.numero) },
                { label: "Saldo inicial", align: "right", render: (row) => money(row.saldo_inicial) },
                { label: "Status", render: (row) => badge(row.ativa ? "Ativa" : "Inativa", row.ativa ? "good" : "neutral") },
            ],
        },
        {
            kind: "centro-custo",
            title: "Centros de custo",
            buttonLabel: "Novo centro",
            kicker: `${state.data.centrosCusto.length} centros`,
            rows: filterRows(state.data.centrosCusto, ["codigo", "nome"]),
            columns: [
                { label: "Codigo", render: (row) => escapeHtml(row.codigo) },
                { label: "Nome", render: (row) => escapeHtml(row.nome) },
                { label: "Pai", render: (row) => escapeHtml(state.lookups.centrosCusto[row.pai] || "-") },
                { label: "Status", render: (row) => badge(row.ativo ? "Ativo" : "Inativo", row.ativo ? "good" : "neutral") },
            ],
        },
        {
            kind: "plano-conta",
            title: "Plano de contas",
            buttonLabel: "Nova conta",
            kicker: `${state.data.planoContas.length} contas`,
            rows: filterRows(state.data.planoContas, ["codigo", "nome", "tipo"]),
            columns: [
                { label: "Codigo", render: (row) => escapeHtml(row.codigo) },
                { label: "Nome", render: (row) => escapeHtml(row.nome) },
                { label: "Tipo", render: (row) => badge(labelStatus(row.tipo), "neutral") },
            ],
        },
    ];

    $("#registry-grid").innerHTML = grids
        .map((grid) => `
            <section class="surface registry-card">
                <div class="section-heading">
                    <div>
                        <p class="eyebrow">${escapeHtml(grid.kicker)}</p>
                        <h3>${escapeHtml(grid.title)}</h3>
                    </div>
                    <button class="mini-button ghost registry-action" data-registry="${escapeHtml(grid.kind)}" type="button">
                        ${icon("plus")}${escapeHtml(grid.buttonLabel)}
                    </button>
                </div>
                ${renderTable({ columns: grid.columns, rows: grid.rows.slice(0, 8), compact: true, emptyTitle: "Sem registros" })}
            </section>
        `)
        .join("");

    $$("[data-registry]").forEach((button) => {
        button.addEventListener("click", () => openRegistryModal(button.dataset.registry));
    });
}

function openRegistryModal(kind) {
    const config = registryFormConfig(kind);
    if (!config) {
        return;
    }
    openModal({
        title: config.title,
        subtitle: "Cadastro operacional",
        body: `
            <form id="registry-form" class="modal-form">
                <div class="form-grid">
                    ${config.body}
                </div>
                <button class="btn btn-primary btn-wide" type="submit">${icon("check")}${escapeHtml(config.submitLabel)}</button>
            </form>
        `,
    });
    $("#registry-form").addEventListener("submit", (event) => submitRegistry(event, kind));
}

function registryFormConfig(kind) {
    const personFields = `
        <label class="span-2">Nome<input name="nome" required maxlength="180"></label>
        <label>Tipo<select name="tipo_pessoa" required>
            <option value="juridica">Pessoa juridica</option>
            <option value="fisica">Pessoa fisica</option>
        </select></label>
        <label>Documento<input name="documento" maxlength="18" placeholder="CPF ou CNPJ"></label>
        <label>E-mail<input name="email" type="email" maxlength="254"></label>
        <label>Telefone<input name="telefone" maxlength="30"></label>
    `;
    const planOptions = optionsFor(state.data.planoContas, (item) => `${item.codigo} - ${item.nome}`, true);
    const centerOptions = optionsFor(state.data.centrosCusto, (item) => `${item.codigo} - ${item.nome}`, true);
    const planTypeOptions = [
        ["receita", "Receita"],
        ["despesa", "Despesa"],
        ["custo", "Custo"],
        ["investimento", "Investimento"],
        ["imposto", "Imposto"],
        ["taxa", "Taxa"],
        ["comissao", "Comissao"],
        ["repasse", "Repasse"],
        ["financiamento", "Financiamento"],
        ["emprestimo", "Emprestimo"],
    ].map(([value, label]) => `<option value="${value}">${label}</option>`).join("");

    return {
        cliente: {
            title: "Novo cliente",
            submitLabel: "Salvar cliente",
            endpoint: ENDPOINTS.clientes,
            body: personFields,
        },
        fornecedor: {
            title: "Novo fornecedor",
            submitLabel: "Salvar fornecedor",
            endpoint: ENDPOINTS.fornecedores,
            body: personFields,
        },
        servico: {
            title: "Novo servico",
            submitLabel: "Salvar servico",
            endpoint: ENDPOINTS.servicos,
            body: `
                <label>Codigo<input name="codigo" maxlength="40" placeholder="SERV-001"></label>
                <label>Valor padrao<input name="valor_padrao" type="number" min="0" step="0.01" value="0"></label>
                <label class="span-2">Nome<input name="nome" required maxlength="160"></label>
                <label class="span-2">Plano de contas<select name="plano_conta">${planOptions}</select></label>
                <label class="span-2">Descricao<textarea name="descricao" rows="3"></textarea></label>
            `,
        },
        "conta-bancaria": {
            title: "Nova conta bancaria",
            submitLabel: "Salvar conta bancaria",
            endpoint: ENDPOINTS.contasBancarias,
            body: `
                <label>Banco<input name="banco" required maxlength="80"></label>
                <label>Agencia<input name="agencia" maxlength="20"></label>
                <label>Numero<input name="numero" required maxlength="40"></label>
                <label>Saldo inicial<input name="saldo_inicial" type="number" step="0.01" value="0"></label>
                <label class="span-2">Descricao<input name="descricao" maxlength="120"></label>
            `,
        },
        "centro-custo": {
            title: "Novo centro de custo",
            submitLabel: "Salvar centro de custo",
            endpoint: ENDPOINTS.centrosCusto,
            body: `
                <label>Codigo<input name="codigo" required maxlength="40"></label>
                <label>Centro pai<select name="pai">${centerOptions}</select></label>
                <label class="span-2">Nome<input name="nome" required maxlength="120"></label>
            `,
        },
        "plano-conta": {
            title: "Nova conta contabil",
            submitLabel: "Salvar plano de contas",
            endpoint: ENDPOINTS.planoContas,
            body: `
                <label>Codigo<input name="codigo" required maxlength="40"></label>
                <label>Tipo<select name="tipo" required>${planTypeOptions}</select></label>
                <label class="span-2">Nome<input name="nome" required maxlength="120"></label>
                <label class="span-2">Conta pai<select name="pai">${planOptions}</select></label>
            `,
        },
    }[kind];
}

async function submitRegistry(event, kind) {
    event.preventDefault();
    const config = registryFormConfig(kind);
    if (!config) {
        return;
    }
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const payload = serializeForm(form);
    const empresa = currentEmpresaId();
    if (!empresa) {
        toast("Selecione uma empresa antes de cadastrar.", "warn");
        return;
    }
    payload.empresa = empresa;
    setBusy(button, true);
    try {
        await api.post(config.endpoint, payload);
        closeModal();
        toast(`${config.title} cadastrado.`, "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Nao foi possivel cadastrar.", "danger");
    } finally {
        setBusy(button, false);
    }
}

function currentEmpresaId() {
    return state.user?.empresa || state.empresa?.id || "";
}

function renderIntelligence() {
    const openAlerts = state.data.alertas.filter((item) => !["resolvido", "descartado"].includes(item.status));
    const highRisk = [...state.data.alertas, ...state.data.anomalias].filter((item) => ["alto", "critico"].includes(item.nivel_risco));
    $("#ai-summary").innerHTML = [
        { label: "Alertas abertos", value: formatNumber(openAlerts.length), note: "Sinais ativos", tone: openAlerts.length ? "warn" : "good" },
        { label: "Risco alto", value: formatNumber(highRisk.length), note: "Prioridade executiva", tone: highRisk.length ? "danger" : "good" },
        { label: "Previsoes", value: formatNumber(state.data.previsoes.length), note: "Modelos baseline", tone: "neutral" },
    ].map(renderKpi).join("");

    $("#ai-grid").innerHTML = `
        <section class="surface span-2">
            <div class="section-heading"><div><p class="eyebrow">Alertas</p><h3>Fila de excecoes</h3></div></div>
            ${renderTable({
                compact: true,
                rows: filterRows(state.data.alertas, ["titulo", "mensagem", "status"]).slice(0, 10),
                columns: [
                    { label: "Titulo", render: (row) => escapeHtml(row.titulo) },
                    { label: "Risco", render: (row) => badge(labelRisk(row.nivel_risco), riskTone(row.nivel_risco)) },
                    { label: "Score", align: "right", render: (row) => row.score ? `${row.score}` : "-" },
                    { label: "Status", render: (row) => badge(labelStatus(row.status), statusTone(row.status)) },
                ],
                emptyTitle: "Sem alertas",
            })}
        </section>
        <section class="surface">
            <div class="section-heading"><div><p class="eyebrow">Anomalias</p><h3>Analises abertas</h3></div></div>
            <div class="timeline-list">
                ${renderAnomalyCards()}
            </div>
        </section>
        <section class="surface span-2">
            <div class="section-heading"><div><p class="eyebrow">Previsoes</p><h3>Caixa projetado</h3></div></div>
            ${renderTable({
                compact: true,
                rows: filterRows(state.data.previsoes, ["nome", "metrica", "modelo"]).slice(0, 10),
                columns: [
                    { label: "Nome", render: (row) => escapeHtml(row.nome) },
                    { label: "Referencia", render: (row) => formatDate(row.data_referencia) },
                    { label: "Horizonte", render: (row) => `${formatNumber(row.horizonte_dias)} dias` },
                    { label: "Valor", align: "right", render: (row) => `<strong>${money(row.valor_previsto)}</strong>` },
                    { label: "Confianca", render: (row) => row.confianca ? `${row.confianca}` : "-" },
                ],
                emptyTitle: "Sem previsoes",
            })}
        </section>
    `;
    $$("[data-feedback]").forEach((button) => {
        button.addEventListener("click", () => sendFeedback(button.dataset.feedback, button.dataset.status));
    });
}

function renderAnomalyCards() {
    const rows = filterRows(state.data.anomalias, ["descricao", "tipo", "status"]).slice(0, 6);
    if (!rows.length) {
        return emptyState("Sem anomalias", "Execute uma varredura quando necessario.");
    }
    return rows.map((item) => `
        <article class="timeline-item anomaly-item">
            <span class="timeline-marker alert"></span>
            <div>
                <strong>${escapeHtml(item.descricao)}</strong>
                <small>${badge(labelRisk(item.nivel_risco), riskTone(item.nivel_risco))} ${badge(labelStatus(item.status), statusTone(item.status))}</small>
            </div>
            <div class="table-actions">
                <button class="mini-button" data-feedback="${item.id}" data-status="confirmado" type="button">Confirmar</button>
                <button class="mini-button ghost" data-feedback="${item.id}" data-status="descartado" type="button">Descartar</button>
            </div>
        </article>
    `).join("");
}

function renderAudit() {
    $("#events-table").innerHTML = renderTable({
        compact: true,
        rows: filterRows(state.data.eventos, ["tipo_evento", "modulo", "acao", "registro_modelo"]).slice(0, 18),
        columns: [
            { label: "Data", render: (row) => formatDate(row.criado_em) },
            { label: "Evento", render: (row) => badge(labelEvent(row.tipo_evento), row.nivel_risco === "alto" ? "danger" : "neutral") },
            { label: "Modulo", render: (row) => escapeHtml(row.modulo) },
            { label: "Acao", render: (row) => escapeHtml(row.acao) },
            { label: "Risco", render: (row) => badge(labelRisk(row.nivel_risco), riskTone(row.nivel_risco)) },
            { label: "Hash", render: (row) => `<code>${escapeHtml(String(row.hash_evento || "").slice(0, 12))}</code>` },
        ],
        emptyTitle: "Sem eventos",
    });

    $("#notifications-list").innerHTML = state.data.notificacoes.length
        ? filterRows(state.data.notificacoes, ["titulo", "mensagem", "status"]).slice(0, 10).map((item) => `
            <article class="timeline-item">
                <span class="timeline-marker notify"></span>
                <div>
                    <strong>${escapeHtml(item.titulo)}</strong>
                    <small>${escapeHtml(item.mensagem)}</small>
                </div>
                <div class="timeline-value">${badge(labelStatus(item.status), statusTone(item.status))}</div>
            </article>
        `).join("")
        : emptyState("Sem notificacoes", "A fila operacional esta vazia.");
}

function renderCompanies() {
    const empresas = filterRows(state.data.empresas, ["razao_social", "nome_fantasia", "cnpj", "status"]);
    $("#company-grid").innerHTML = empresas.length
        ? empresas.map((empresa) => `
            <article class="company-card surface ${empresa.id === state.user?.empresa ? "is-current" : ""}">
                <div>
                    <p class="eyebrow">${escapeHtml(empresa.cnpj || "Sem CNPJ")}</p>
                    <h3>${escapeHtml(empresa.nome_fantasia || empresa.razao_social)}</h3>
                    <span>${escapeHtml(empresa.razao_social)}</span>
                </div>
                ${badge(labelStatus(empresa.status), statusTone(empresa.status))}
            </article>
        `).join("")
        : emptyState("Sem empresas", "Nenhuma empresa acessivel para este usuario.");

    $("#modules-table").innerHTML = renderTable({
        compact: true,
        rows: filterRows(state.data.empresaModulos, ["ativo"]).slice(0, 20),
        columns: [
            { label: "Empresa", render: (row) => escapeHtml(state.lookups.empresas[row.empresa] || `#${row.empresa}`) },
            { label: "Modulo", render: (row) => escapeHtml(state.lookups.modulos[row.modulo] || `#${row.modulo}`) },
            { label: "Status", render: (row) => badge(row.ativo ? "Ativo" : "Inativo", row.ativo ? "good" : "neutral") },
            { label: "Instalado em", render: (row) => formatDate(row.instalado_em) },
        ],
        emptyTitle: "Sem modulos instalados",
    });
}

function renderReports() {
    const reportEvents = state.data.eventos.filter((item) => item.tipo_evento === "exportacao" || String(item.acao || "").includes("exportar"));
    $("#report-events").innerHTML = renderTable({
        compact: true,
        rows: filterRows(reportEvents, ["acao", "modulo", "tela"]).slice(0, 14),
        columns: [
            { label: "Data", render: (row) => formatDate(row.criado_em) },
            { label: "Acao", render: (row) => escapeHtml(row.acao) },
            { label: "Modulo", render: (row) => escapeHtml(row.modulo) },
            { label: "Risco", render: (row) => badge(labelRisk(row.nivel_risco), riskTone(row.nivel_risco)) },
        ],
        emptyTitle: "Sem exportacoes",
    });
}

function filterRows(rows, fields) {
    const search = state.search;
    if (!search) {
        return rows;
    }
    return rows.filter((row) => fields.some((field) => String(row[field] ?? "").toLowerCase().includes(search)));
}

function openEntryModal(kind) {
    const isReceivable = kind === "receber";
    const partnerOptions = optionsFor(isReceivable ? state.data.clientes : state.data.fornecedores, "nome");
    const accountOptions = optionsFor(state.data.contasBancarias, (item) => `${item.banco} ${item.numero}`);
    const costOptions = optionsFor(state.data.centrosCusto, (item) => `${item.codigo} - ${item.nome}`, true);
    const planOptions = optionsFor(state.data.planoContas, (item) => `${item.codigo} - ${item.nome}`, true);
    openModal({
        title: isReceivable ? "Novo recebivel" : "Novo pagamento",
        subtitle: "Lancamento financeiro",
        body: `
            <form id="entry-form" class="modal-form">
                <div class="form-grid">
                    <label>${isReceivable ? "Cliente" : "Fornecedor"}<select name="${isReceivable ? "cliente" : "fornecedor"}" required>${partnerOptions}</select></label>
                    <label>Descricao<input name="descricao" required maxlength="180"></label>
                    <label>Emissao<input name="data_emissao" type="date" required value="${state.period.start}"></label>
                    <label>Vencimento<input name="data_vencimento" type="date" required value="${state.period.end}"></label>
                    <label>Valor<input name="valor_original" type="number" min="0.01" step="0.01" required></label>
                    <label>${isReceivable ? "Contrato" : "Documento"}<input name="${isReceivable ? "contrato" : "numero_documento"}" maxlength="80"></label>
                    <label>Conta bancaria<select name="conta_bancaria">${accountOptions}</select></label>
                    <label>Centro de custo<select name="centro_custo">${costOptions}</select></label>
                    <label>Plano de contas<select name="plano_conta">${planOptions}</select></label>
                    <label class="span-2">Observacao<textarea name="observacao" rows="3"></textarea></label>
                </div>
                <button class="btn btn-primary btn-wide" type="submit">${icon("check")}Salvar lancamento</button>
            </form>
        `,
    });
    $("#entry-form").addEventListener("submit", (event) => submitEntry(event, kind));
}

async function submitEntry(event, kind) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    const payload = serializeForm(form);
    payload.empresa = state.user?.empresa;
    setBusy(button, true);
    try {
        await api.post(kind === "receber" ? ENDPOINTS.contasReceber : ENDPOINTS.contasPagar, payload);
        closeModal();
        toast("Lancamento salvo.", "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Nao foi possivel salvar.", "danger");
    } finally {
        setBusy(button, false);
    }
}

function openSettlementModal(kind, id) {
    const isReceivable = kind === "receber";
    const list = isReceivable ? state.data.contasReceber : state.data.contasPagar;
    const item = list.find((row) => String(row.id) === String(id));
    const accountOptions = optionsFor(state.data.contasBancarias, (conta) => `${conta.banco} ${conta.numero}`, true);
    openModal({
        title: isReceivable ? "Registrar recebimento" : "Baixar pagamento",
        subtitle: item?.descricao || "Lancamento",
        body: `
            <form id="settlement-form" class="modal-form">
                <div class="settlement-resume">
                    <span>Saldo pendente</span>
                    <strong>${money(item?.saldo_pendente || item?.valor_total || 0)}</strong>
                </div>
                <div class="form-grid">
                    <label>Valor<input name="valor" type="number" min="0.01" step="0.01" required value="${item?.saldo_pendente || ""}"></label>
                    <label>Conta bancaria<select name="conta_bancaria">${accountOptions}</select></label>
                    <label class="span-2">${isReceivable ? "Forma de recebimento" : "Forma de pagamento"}<input name="${isReceivable ? "forma_recebimento" : "forma_pagamento"}" maxlength="80"></label>
                </div>
                <button class="btn btn-primary btn-wide" type="submit">${icon("check")}${isReceivable ? "Confirmar recebimento" : "Confirmar baixa"}</button>
            </form>
        `,
    });
    $("#settlement-form").addEventListener("submit", (event) => submitSettlement(event, kind, id));
}

async function submitSettlement(event, kind, id) {
    event.preventDefault();
    const form = event.currentTarget;
    const button = form.querySelector("button");
    setBusy(button, true);
    const payload = serializeForm(form);
    const endpoint = kind === "receber" ? `${ENDPOINTS.contasReceber}${id}/receber/` : `${ENDPOINTS.contasPagar}${id}/baixar/`;
    try {
        await api.post(endpoint, payload);
        closeModal();
        toast(kind === "receber" ? "Recebimento registrado." : "Pagamento baixado.", "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Operacao nao concluida.", "danger");
    } finally {
        setBusy(button, false);
    }
}

async function requestApproval(id, button) {
    setBusy(button, true);
    try {
        await api.post(`${ENDPOINTS.contasPagar}${id}/solicitar_aprovacao/`, { justificativa: "Solicitado pelo painel web." });
        toast("Aprovacao solicitada. A decisao fica na tela Aprovacoes.", "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Nao foi possivel solicitar aprovacao.", "danger");
    } finally {
        setBusy(button, false);
    }
}

function openRenegotiationModal(id) {
    const item = state.data.contasReceber.find((row) => String(row.id) === String(id));
    openModal({
        title: "Renegociar recebivel",
        subtitle: item?.descricao || "Conta a receber",
        body: `
            <form id="renegotiation-form" class="modal-form">
                <div class="form-grid">
                    <label>Novo vencimento<input name="nova_data_vencimento" type="date" required value="${state.period.end}"></label>
                    <label>Valor<input name="valor_original" type="number" min="0.01" step="0.01" required value="${item?.saldo_pendente || item?.valor_original || ""}"></label>
                    <label>Juros<input name="juros" type="number" min="0" step="0.01" value="0"></label>
                    <label>Multa<input name="multa" type="number" min="0" step="0.01" value="0"></label>
                    <label>Desconto<input name="desconto" type="number" min="0" step="0.01" value="0"></label>
                    <label>Honorarios<input name="honorarios" type="number" min="0" step="0.01" value="0"></label>
                    <label class="span-2">Observacao<textarea name="observacao" rows="3"></textarea></label>
                </div>
                <button class="btn btn-primary btn-wide" type="submit">${icon("check")}Salvar renegociacao</button>
            </form>
        `,
    });
    $("#renegotiation-form").addEventListener("submit", async (event) => {
        event.preventDefault();
        const button = event.currentTarget.querySelector("button");
        setBusy(button, true);
        try {
            await api.post(`${ENDPOINTS.contasReceber}${id}/renegociar/`, serializeForm(event.currentTarget));
            closeModal();
            toast("Recebivel renegociado.", "good");
            await loadWorkspace();
        } catch (error) {
            toast(error.message || "Nao foi possivel renegociar.", "danger");
        } finally {
            setBusy(button, false);
        }
    });
}

async function runAiScan(event) {
    const button = event.currentTarget;
    setBusy(button, true);
    try {
        await api.post(`${ENDPOINTS.anomalias}varredura/`, {});
        toast("Varredura concluida.", "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Varredura nao concluida.", "danger");
    } finally {
        setBusy(button, false);
    }
}

async function runForecast(event) {
    const button = event.currentTarget;
    setBusy(button, true);
    try {
        await api.post(`${ENDPOINTS.previsoes}gerar_baseline_caixa/`, { horizonte_dias: 60 });
        toast("Previsao gerada.", "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Previsao nao gerada.", "danger");
    } finally {
        setBusy(button, false);
    }
}

async function sendFeedback(id, status) {
    try {
        await api.post(`${ENDPOINTS.anomalias}${id}/feedback/`, { status });
        toast("Feedback registrado.", "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Feedback nao registrado.", "danger");
    }
}

async function downloadReport(event) {
    event.preventDefault();
    const button = event.currentTarget.querySelector("button");
    setBusy(button, true);
    try {
        const payload = {
            tipo: $("#report-type").value,
            formato: $("#report-format").value,
            data_inicio: state.period.start,
            data_fim: state.period.end,
        };
        const { blob, filename } = await api.download(ENDPOINTS.relatorios, payload);
        downloadBlob(blob, filename);
        toast("Relatorio gerado.", "good");
        await loadWorkspace();
    } catch (error) {
        toast(error.message || "Nao foi possivel gerar relatorio.", "danger");
    } finally {
        setBusy(button, false);
    }
}

function optionsFor(items, label, includeEmpty = false) {
    const rows = items.map((item) => {
        const text = typeof label === "function" ? label(item) : item[label];
        return `<option value="${item.id}">${escapeHtml(text || `#${item.id}`)}</option>`;
    });
    if (includeEmpty) {
        rows.unshift('<option value="">Nao informado</option>');
    }
    return rows.join("");
}

function debounce(callback, wait) {
    let timeout;
    return (...args) => {
        window.clearTimeout(timeout);
        timeout = window.setTimeout(() => callback(...args), wait);
    };
}
