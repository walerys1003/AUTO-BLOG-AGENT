/*  =============================================================
 *  api.js — Centralny klient HTTP dla MasterContentAI
 *  -------------------------------------------------------------
 *  Zapewnia jednolite wywołania HTTP:
 *    - apiFetch(url, options)   -> Response (low-level)
 *    - apiJSON(url, options)    -> parsuje JSON, rzuca błąd przy non-2xx
 *    - apiForm(url, FormData)   -> POST formularza wieloczęściowego
 *    - apiPost(url, dataObj)    -> POST JSON
 *    - apiGet(url, paramsObj)   -> GET z query-string
 *  Wszystkie błędy są normalizowane do obiektu { message, status, body }.
 *  Globalnie podpina toast przy błędzie sieci/serwera.
 *  ============================================================= */
(function (global) {
    'use strict';

    /* ------- Pomocnicze --------------------------------------- */

    function buildQuery(params) {
        if (!params) return '';
        const q = new URLSearchParams();
        Object.keys(params).forEach((k) => {
            const v = params[k];
            if (v === undefined || v === null) return;
            q.append(k, v);
        });
        const s = q.toString();
        return s ? '?' + s : '';
    }

    function getCsrfToken() {
        const meta = document.querySelector('meta[name="csrf-token"]');
        return meta ? meta.getAttribute('content') : null;
    }

    function defaultHeaders(extra) {
        const h = {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        };
        const csrf = getCsrfToken();
        if (csrf) h['X-CSRFToken'] = csrf;
        return Object.assign(h, extra || {});
    }

    async function parseBody(response) {
        const ct = response.headers.get('content-type') || '';
        if (ct.includes('application/json')) {
            try { return await response.json(); } catch (e) { return null; }
        }
        try { return await response.text(); } catch (e) { return null; }
    }

    function showErrorToast(message) {
        if (global.Toast && typeof global.Toast.error === 'function') {
            global.Toast.error(message);
        } else {
            // fallback - cicho do konsoli
            console.error('[API]', message);
        }
    }

    /* ------- Public API --------------------------------------- */

    async function apiFetch(url, options) {
        options = options || {};
        options.headers = defaultHeaders(options.headers);
        options.credentials = options.credentials || 'same-origin';
        try {
            return await fetch(url, options);
        } catch (err) {
            const msg = 'Brak połączenia z serwerem. Sprawdź sieć i spróbuj ponownie.';
            showErrorToast(msg);
            const e = new Error(msg);
            e.network = true;
            throw e;
        }
    }

    async function apiJSON(url, options) {
        const res = await apiFetch(url, options);
        const body = await parseBody(res);
        if (!res.ok) {
            const message = (body && body.error) || (body && body.message)
                || `Błąd ${res.status} ${res.statusText}`;
            showErrorToast(message);
            const err = new Error(message);
            err.status = res.status;
            err.body = body;
            throw err;
        }
        return body;
    }

    function apiGet(url, params, options) {
        return apiJSON(url + buildQuery(params), Object.assign({ method: 'GET' }, options || {}));
    }

    function apiPost(url, data, options) {
        const opts = Object.assign({
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data || {})
        }, options || {});
        return apiJSON(url, opts);
    }

    function apiForm(url, formData, options) {
        // FormData: nie ustawiamy Content-Type, browser doda boundary
        const opts = Object.assign({
            method: 'POST',
            body: formData
        }, options || {});
        return apiJSON(url, opts);
    }

    function apiDelete(url, options) {
        return apiJSON(url, Object.assign({ method: 'DELETE' }, options || {}));
    }

    /* ------- Eksport ------------------------------------------ */
    global.API = {
        fetch: apiFetch,
        json: apiJSON,
        get: apiGet,
        post: apiPost,
        form: apiForm,
        delete: apiDelete,
        csrf: getCsrfToken
    };

})(window);
