import { buildQuery, normalizeList } from "./data.js";

const TOKEN_KEY = "erp_financeiro_access";
const REFRESH_KEY = "erp_financeiro_refresh";

export class ApiClient {
    constructor() {
        this.access = localStorage.getItem(TOKEN_KEY) || "";
        this.refresh = localStorage.getItem(REFRESH_KEY) || "";
        this.onUnauthorized = null;
    }

    hasSession() {
        return Boolean(this.access && this.refresh);
    }

    setTokens({ access, refresh }) {
        this.access = access || "";
        this.refresh = refresh || "";
        if (this.access) {
            localStorage.setItem(TOKEN_KEY, this.access);
        }
        if (this.refresh) {
            localStorage.setItem(REFRESH_KEY, this.refresh);
        }
    }

    clearTokens() {
        this.access = "";
        this.refresh = "";
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(REFRESH_KEY);
    }

    async login(endpoint, payload) {
        const data = await this.request(endpoint, {
            method: "POST",
            body: payload,
            skipAuth: true,
        });
        this.setTokens(data);
        return data;
    }

    async get(path, params) {
        return this.request(`${path}${buildQuery(params)}`);
    }

    async list(path, params) {
        return normalizeList(await this.get(path, params));
    }

    async post(path, payload = {}) {
        return this.request(path, {
            method: "POST",
            body: payload,
        });
    }

    async patch(path, payload = {}) {
        return this.request(path, {
            method: "PATCH",
            body: payload,
        });
    }

    async download(path, payload = {}) {
        return this.request(path, {
            method: "POST",
            body: payload,
            responseType: "blob",
        });
    }

    async request(path, options = {}) {
        const response = await fetch(path, this.makeOptions(options));
        if (response.status === 401 && !options.skipRefresh && this.refresh) {
            const refreshed = await this.refreshToken().catch(() => null);
            if (refreshed) {
                return this.request(path, { ...options, skipRefresh: true });
            }
            this.clearTokens();
            if (typeof this.onUnauthorized === "function") {
                this.onUnauthorized();
            }
        }
        return this.parseResponse(response, options.responseType);
    }

    makeOptions(options) {
        const headers = new Headers(options.headers || {});
        const init = {
            method: options.method || "GET",
            headers,
        };
        if (this.access && !options.skipAuth) {
            headers.set("Authorization", `Bearer ${this.access}`);
        }
        if (options.body !== undefined) {
            if (options.body instanceof FormData) {
                init.body = options.body;
            } else {
                headers.set("Content-Type", "application/json");
                init.body = JSON.stringify(options.body);
            }
        }
        return init;
    }

    async refreshToken() {
        if (!this.refresh) {
            return null;
        }
        const response = await fetch("/api/auth/token/refresh/", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ refresh: this.refresh }),
        });
        if (!response.ok) {
            return null;
        }
        const data = await response.json();
        this.setTokens({ access: data.access, refresh: data.refresh || this.refresh });
        return data;
    }

    async parseResponse(response, responseType) {
        if (responseType === "blob") {
            if (!response.ok) {
                throw await this.makeError(response);
            }
            const blob = await response.blob();
            return {
                blob,
                filename: getFilename(response.headers.get("Content-Disposition")),
            };
        }

        const contentType = response.headers.get("Content-Type") || "";
        const isJson = contentType.includes("application/json");
        const payload = isJson ? await response.json().catch(() => null) : await response.text();

        if (!response.ok) {
            throw this.toError(response.status, payload);
        }
        return payload;
    }

    async makeError(response) {
        const text = await response.text().catch(() => "");
        return this.toError(response.status, text);
    }

    toError(status, payload) {
        const error = new Error(extractMessage(payload) || `Erro ${status}`);
        error.status = status;
        error.payload = payload;
        return error;
    }
}

function extractMessage(payload) {
    if (!payload) {
        return "";
    }
    if (typeof payload === "string") {
        return payload;
    }
    if (payload.detail) {
        return payload.detail;
    }
    if (payload.non_field_errors) {
        return Array.isArray(payload.non_field_errors) ? payload.non_field_errors.join(" ") : payload.non_field_errors;
    }
    const [firstKey] = Object.keys(payload);
    if (!firstKey) {
        return "";
    }
    const value = payload[firstKey];
    if (Array.isArray(value)) {
        return `${firstKey}: ${value.join(" ")}`;
    }
    if (typeof value === "object") {
        return `${firstKey}: ${JSON.stringify(value)}`;
    }
    return `${firstKey}: ${value}`;
}

function getFilename(header) {
    if (!header) {
        return "relatorio";
    }
    const match = header.match(/filename="?([^";]+)"?/i);
    return match ? match[1] : "relatorio";
}
