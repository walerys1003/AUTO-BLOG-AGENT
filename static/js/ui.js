/*  =============================================================
 *  ui.js — Komponenty interakcji UI dla MasterContentAI
 *  -------------------------------------------------------------
 *  - Toast.success/error/info/warning(message, opts)
 *  - Modal.open(id), Modal.close(id), Modal.confirm({...})
 *  - Drawer.open(id), Drawer.close(id)
 *  - Tabs (auto-init dla [data-tabs])
 *  - Copy-to-clipboard (auto-init dla [data-copy])
 *  - Sidebar collapse (auto-init dla [data-sidebar-toggle])
 *  ============================================================= */
(function (global) {
    'use strict';

    /* ───────────────────────── TOAST ───────────────────────── */
    const Toast = (function () {
        let container = null;

        function ensureContainer() {
            if (container) return container;
            container = document.querySelector('.toast-container');
            if (!container) {
                container = document.createElement('div');
                container.className = 'toast-container';
                document.body.appendChild(container);
            }
            return container;
        }

        const ICONS = {
            success: 'fa-check-circle',
            error: 'fa-circle-xmark',
            warning: 'fa-triangle-exclamation',
            info: 'fa-circle-info'
        };

        function show(type, message, opts) {
            opts = opts || {};
            const duration = opts.duration || (type === 'error' ? 6000 : 4000);
            const root = ensureContainer();
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <div class="toast-icon"><i class="fas ${ICONS[type] || ICONS.info}"></i></div>
                <div class="toast-body">${message}</div>
                <button type="button" class="toast-close" aria-label="Zamknij">&times;</button>
            `;
            root.appendChild(toast);
            requestAnimationFrame(() => toast.classList.add('is-visible'));

            const remove = () => {
                toast.classList.remove('is-visible');
                setTimeout(() => toast.remove(), 250);
            };
            toast.querySelector('.toast-close').addEventListener('click', remove);
            if (duration > 0) setTimeout(remove, duration);
            return toast;
        }

        return {
            show: show,
            success: (m, o) => show('success', m, o),
            error:   (m, o) => show('error', m, o),
            warning: (m, o) => show('warning', m, o),
            info:    (m, o) => show('info', m, o)
        };
    })();

    /* ───────────────────────── MODAL ───────────────────────── */
    const Modal = (function () {
        function open(id) {
            const el = typeof id === 'string' ? document.getElementById(id) : id;
            if (!el) return;
            el.classList.add('is-open');
            document.body.classList.add('modal-open');
            // focus pierwszy input
            const input = el.querySelector('input,textarea,select,button');
            if (input) setTimeout(() => input.focus(), 50);
        }

        function close(id) {
            const el = typeof id === 'string' ? document.getElementById(id) : id;
            if (!el) return;
            el.classList.remove('is-open');
            // jeśli żaden inny modal nie otwarty, zdejmij blokadę body
            if (!document.querySelector('.modal.is-open')) {
                document.body.classList.remove('modal-open');
            }
        }

        function confirm(opts) {
            opts = opts || {};
            return new Promise((resolve) => {
                const id = 'modal-confirm-' + Date.now();
                const el = document.createElement('div');
                el.className = 'modal';
                el.id = id;
                el.innerHTML = `
                    <div class="modal-backdrop" data-close></div>
                    <div class="modal-dialog modal-sm">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h3 class="modal-title">${opts.title || 'Potwierdź'}</h3>
                                <button type="button" class="modal-close" data-close aria-label="Zamknij">&times;</button>
                            </div>
                            <div class="modal-body">${opts.message || 'Czy na pewno chcesz kontynuować?'}</div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-ghost" data-close>${opts.cancelLabel || 'Anuluj'}</button>
                                <button type="button" class="btn btn-${opts.danger ? 'danger' : 'primary'}" data-ok>${opts.confirmLabel || 'Potwierdź'}</button>
                            </div>
                        </div>
                    </div>`;
                document.body.appendChild(el);
                open(el);

                const cleanup = (result) => {
                    close(el);
                    setTimeout(() => el.remove(), 300);
                    resolve(result);
                };
                el.querySelectorAll('[data-close]').forEach(b => b.addEventListener('click', () => cleanup(false)));
                el.querySelector('[data-ok]').addEventListener('click', () => cleanup(true));
            });
        }

        // Auto-bind data-modal-open / data-modal-close
        function init() {
            document.addEventListener('click', (e) => {
                const opener = e.target.closest('[data-modal-open]');
                if (opener) {
                    e.preventDefault();
                    open(opener.getAttribute('data-modal-open'));
                    return;
                }
                const closer = e.target.closest('[data-modal-close]');
                if (closer) {
                    e.preventDefault();
                    const modal = closer.closest('.modal');
                    if (modal) close(modal);
                    return;
                }
                // klik w backdrop zamyka
                if (e.target.classList.contains('modal-backdrop')) {
                    const modal = e.target.closest('.modal');
                    if (modal) close(modal);
                }
            });
            // ESC zamyka
            document.addEventListener('keydown', (e) => {
                if (e.key === 'Escape') {
                    const opened = document.querySelector('.modal.is-open');
                    if (opened) close(opened);
                }
            });
        }

        return { open, close, confirm, init };
    })();

    /* ───────────────────────── DRAWER (mobile sidebar) ───────────────────── */
    const Drawer = (function () {
        function open(id) {
            const el = typeof id === 'string' ? document.getElementById(id) : id;
            if (el) el.classList.add('is-open');
            document.body.classList.add('drawer-open');
        }
        function close(id) {
            const el = typeof id === 'string' ? document.getElementById(id) : id;
            if (el) el.classList.remove('is-open');
            document.body.classList.remove('drawer-open');
        }
        function toggle(id) {
            const el = typeof id === 'string' ? document.getElementById(id) : id;
            if (!el) return;
            if (el.classList.contains('is-open')) close(el); else open(el);
        }
        return { open, close, toggle };
    })();

    /* ───────────────────────── COPY-TO-CLIPBOARD ─────────────────────────── */
    function initCopyButtons() {
        document.addEventListener('click', async (e) => {
            const btn = e.target.closest('[data-copy]');
            if (!btn) return;
            e.preventDefault();
            const value = btn.getAttribute('data-copy');
            try {
                await navigator.clipboard.writeText(value);
                Toast.success('Skopiowano do schowka');
            } catch (err) {
                Toast.error('Nie udało się skopiować');
            }
        });
    }

    /* ───────────────────────── TABS ──────────────────────────────────────── */
    function initTabs() {
        document.querySelectorAll('[data-tabs]').forEach((root) => {
            const buttons = root.querySelectorAll('[data-tab]');
            const panels = root.querySelectorAll('[data-tab-panel]');
            buttons.forEach((btn) => {
                btn.addEventListener('click', (e) => {
                    e.preventDefault();
                    const target = btn.getAttribute('data-tab');
                    buttons.forEach(b => b.classList.toggle('is-active', b === btn));
                    panels.forEach(p => p.classList.toggle('is-active', p.getAttribute('data-tab-panel') === target));
                });
            });
        });
    }

    /* ───────────────────────── SIDEBAR collapse ──────────────────────────── */
    function initSidebar() {
        // Kompatybilność: klucz historycznie używany w base.html
        const KEY = 'mc-sidebar-collapsed';
        const sidebar = document.querySelector('.app-sidebar, .sidebar');
        const backdrop = document.querySelector('.sidebar-backdrop');
        if (!sidebar) return;

        const isMobile = () => window.matchMedia('(max-width: 1024px)').matches;

        // restore stan
        try {
            if (!isMobile() && localStorage.getItem(KEY) === '1') {
                sidebar.classList.add('is-collapsed');
            }
        } catch (_) { /* ignore storage errors */ }

        document.addEventListener('click', (e) => {
            const toggle = e.target.closest('[data-sidebar-toggle]');
            if (toggle) {
                e.preventDefault();
                if (isMobile()) {
                    sidebar.classList.toggle('is-open');
                    if (backdrop) backdrop.classList.toggle('is-visible');
                } else {
                    sidebar.classList.toggle('is-collapsed');
                    try { localStorage.setItem(KEY, sidebar.classList.contains('is-collapsed') ? '1' : '0'); } catch (_) {}
                }
                return;
            }
            // backdrop / data-drawer-close zamykają drawer
            if (e.target.classList && e.target.classList.contains('sidebar-backdrop')) {
                sidebar.classList.remove('is-open');
                if (backdrop) backdrop.classList.remove('is-visible');
            }
            if (e.target.closest('[data-drawer-close]')) {
                sidebar.classList.remove('is-open');
                if (backdrop) backdrop.classList.remove('is-visible');
            }
        });

        // Zamknij mobile drawer przy zmianie do desktop
        window.addEventListener('resize', () => {
            if (!isMobile()) {
                sidebar.classList.remove('is-open');
                if (backdrop) backdrop.classList.remove('is-visible');
            }
        });
    }

    /* ───────────────────────── Auto-flash → Toast ───────────────────────── */
    function initFlashToasts() {
        document.querySelectorAll('[data-flash]').forEach((el) => {
            const type = el.getAttribute('data-flash') || 'info';
            const msg = el.textContent.trim();
            if (msg) Toast.show(type, msg);
            el.remove();
        });
    }

    /* ───────────────────────── BOOTSTRAP ──────────────────────────────────── */
    document.addEventListener('DOMContentLoaded', () => {
        Modal.init();
        initCopyButtons();
        initTabs();
        initSidebar();
        initFlashToasts();
    });

    global.Toast = Toast;
    global.Modal = Modal;
    global.Drawer = Drawer;

})(window);
