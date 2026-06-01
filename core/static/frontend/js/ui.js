export const $ = (selector, root = document) => root.querySelector(selector);
export const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));

export function icon(name) {
    return `<svg class="icon"><use href="#i-${name}"></use></svg>`;
}

export function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

export function setBusy(element, busy = true) {
    if (!element) {
        return;
    }
    element.classList.toggle("is-busy", busy);
    element.disabled = busy;
}

export function toast(message, tone = "neutral") {
    const region = $("#toast-region");
    if (!region) {
        return;
    }
    const node = document.createElement("div");
    node.className = `toast toast-${tone}`;
    node.textContent = message;
    region.appendChild(node);
    window.setTimeout(() => {
        node.classList.add("is-leaving");
        window.setTimeout(() => node.remove(), 220);
    }, 3600);
}

export function badge(value, tone = "neutral") {
    return `<span class="status-badge ${toneClass(tone)}">${escapeHtml(value)}</span>`;
}

export function riskTone(value) {
    return {
        baixo: "good",
        medio: "warn",
        alto: "danger",
        critico: "critical",
    }[value] || "neutral";
}

export function statusTone(value) {
    if (["pago", "recebido", "aprovado", "conciliada", "enviada", "resolvido"].includes(value)) {
        return "good";
    }
    if (["vencido", "cancelado", "reprovado", "falhou", "critico", "protestado", "judicial"].includes(value)) {
        return "danger";
    }
    if (["em_aprovacao", "pendente", "em_cobranca", "sugerida", "em_analise", "a_vencer"].includes(value)) {
        return "warn";
    }
    return "neutral";
}

export function toneClass(tone) {
    return {
        good: "tone-good",
        warn: "tone-warn",
        danger: "tone-danger",
        critical: "tone-critical",
        neutral: "tone-neutral",
    }[tone] || "tone-neutral";
}

export function emptyState(title, body = "") {
    return `
        <div class="empty-state">
            ${icon("database")}
            <strong>${escapeHtml(title)}</strong>
            ${body ? `<span>${escapeHtml(body)}</span>` : ""}
        </div>
    `;
}

export function renderTable({ columns, rows, emptyTitle = "Sem registros", compact = false }) {
    if (!rows || rows.length === 0) {
        return emptyState(emptyTitle);
    }
    const tableClass = compact ? "data-table compact" : "data-table";
    return `
        <div class="${tableClass}">
            <table>
                <thead>
                    <tr>${columns.map((column) => `<th>${escapeHtml(column.label)}</th>`).join("")}</tr>
                </thead>
                <tbody>
                    ${rows
                        .map((row) => `
                            <tr>
                                ${columns
                                    .map((column) => {
                                        const value = typeof column.render === "function" ? column.render(row) : row[column.key];
                                        const align = column.align ? ` class="align-${column.align}"` : "";
                                        return `<td${align}>${value ?? ""}</td>`;
                                    })
                                    .join("")}
                            </tr>
                        `)
                        .join("")}
                </tbody>
            </table>
        </div>
    `;
}

export function openModal({ title, subtitle = "", body, actions = "" }) {
    const root = $("#modal-root");
    root.hidden = false;
    root.innerHTML = `
        <div class="modal-backdrop" data-close-modal></div>
        <section class="modal-panel" role="dialog" aria-modal="true" aria-label="${escapeHtml(title)}">
            <header class="modal-header">
                <div>
                    <p class="eyebrow">${escapeHtml(subtitle)}</p>
                    <h3>${escapeHtml(title)}</h3>
                </div>
                <button class="icon-button" type="button" data-close-modal title="Fechar">
                    ${icon("x")}
                </button>
            </header>
            <div class="modal-body">${body}</div>
            ${actions ? `<footer class="modal-actions">${actions}</footer>` : ""}
        </section>
    `;
    $$("[data-close-modal]", root).forEach((item) => item.addEventListener("click", closeModal));
    const first = root.querySelector("input, select, textarea, button");
    if (first) {
        first.focus();
    }
}

export function closeModal() {
    const root = $("#modal-root");
    root.hidden = true;
    root.innerHTML = "";
}

export function serializeForm(form) {
    const data = new FormData(form);
    return Array.from(data.entries()).reduce((payload, [key, value]) => {
        if (value !== "") {
            payload[key] = value;
        }
        return payload;
    }, {});
}

export function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename || "relatorio";
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);
}

export function drawCashflowChart(canvas, series) {
    if (!canvas) {
        return;
    }
    const context = canvas.getContext("2d");
    const rect = canvas.getBoundingClientRect();
    const ratio = window.devicePixelRatio || 1;
    canvas.width = Math.max(640, Math.floor(rect.width * ratio));
    canvas.height = Math.floor(320 * ratio);
    context.scale(ratio, ratio);

    const width = canvas.width / ratio;
    const height = canvas.height / ratio;
    context.clearRect(0, 0, width, height);
    context.fillStyle = "#ffffff";
    context.fillRect(0, 0, width, height);

    const padding = { top: 24, right: 22, bottom: 36, left: 54 };
    const plotWidth = width - padding.left - padding.right;
    const plotHeight = height - padding.top - padding.bottom;
    const points = series.length ? series : [{ label: "Sem dados", entrada: 0, saida: 0, saldo: 0 }];
    const values = points.flatMap((point) => [point.entrada, point.saida, point.saldo]);
    const max = Math.max(...values, 1);
    const min = Math.min(...values, 0);
    const range = max - min || 1;

    context.strokeStyle = "#e8e3d9";
    context.lineWidth = 1;
    context.font = "12px Inter, system-ui, sans-serif";
    context.fillStyle = "#6f6a61";
    for (let i = 0; i <= 4; i += 1) {
        const y = padding.top + (plotHeight / 4) * i;
        context.beginPath();
        context.moveTo(padding.left, y);
        context.lineTo(width - padding.right, y);
        context.stroke();
        const value = max - (range / 4) * i;
        context.fillText(shortCurrency(value), 8, y + 4);
    }

    drawLine(context, points, "entrada", "#118b69", padding, plotWidth, plotHeight, min, range);
    drawLine(context, points, "saida", "#b2523c", padding, plotWidth, plotHeight, min, range);
    drawLine(context, points, "saldo", "#b08a37", padding, plotWidth, plotHeight, min, range, true);

    context.fillStyle = "#4d4840";
    const step = points.length > 1 ? plotWidth / (points.length - 1) : plotWidth;
    points.forEach((point, index) => {
        if (index % Math.ceil(points.length / 6) === 0 || points.length <= 6) {
            const x = padding.left + step * index;
            context.fillText(point.label, Math.max(6, x - 16), height - 12);
        }
    });

    drawLegend(context, width, [
        ["Entradas", "#118b69"],
        ["Saidas", "#b2523c"],
        ["Saldo", "#b08a37"],
    ]);
}

function drawLine(context, points, key, color, padding, plotWidth, plotHeight, min, range, fill = false) {
    const step = points.length > 1 ? plotWidth / (points.length - 1) : plotWidth;
    context.beginPath();
    points.forEach((point, index) => {
        const x = padding.left + step * index;
        const y = padding.top + plotHeight - ((point[key] - min) / range) * plotHeight;
        if (index === 0) {
            context.moveTo(x, y);
        } else {
            context.lineTo(x, y);
        }
    });
    context.strokeStyle = color;
    context.lineWidth = fill ? 3 : 2;
    context.stroke();
    if (fill) {
        const gradient = context.createLinearGradient(0, padding.top, 0, padding.top + plotHeight);
        gradient.addColorStop(0, "rgba(176, 138, 55, .20)");
        gradient.addColorStop(1, "rgba(176, 138, 55, 0)");
        context.lineTo(padding.left + step * (points.length - 1), padding.top + plotHeight);
        context.lineTo(padding.left, padding.top + plotHeight);
        context.closePath();
        context.fillStyle = gradient;
        context.fill();
    }
}

function drawLegend(context, width, items) {
    let x = width - 250;
    context.font = "12px Inter, system-ui, sans-serif";
    items.forEach(([label, color]) => {
        context.fillStyle = color;
        context.fillRect(x, 18, 10, 10);
        context.fillStyle = "#4d4840";
        context.fillText(label, x + 16, 28);
        x += 82;
    });
}

function shortCurrency(value) {
    const abs = Math.abs(Number(value) || 0);
    if (abs >= 1000000) {
        return `R$ ${(value / 1000000).toFixed(1)}m`;
    }
    if (abs >= 1000) {
        return `R$ ${(value / 1000).toFixed(0)}k`;
    }
    return `R$ ${Math.round(value)}`;
}
