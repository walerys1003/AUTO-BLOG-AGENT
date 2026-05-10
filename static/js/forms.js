/*  =============================================================
 *  forms.js — Walidacja i stan zapisu formularzy
 *  -------------------------------------------------------------
 *  - Validator: walidacja na blur + submit, komunikaty po polsku
 *  - SaveState: śledzenie dirty/saving/saved + beforeunload guard
 *  - Loading: setLoading(button, isLoading) — spinner w przycisku
 *  ============================================================= */
(function (global) {
    'use strict';

    /* ───────────────────────── KOMUNIKATY ────────────────────── */
    const MSG = {
        required:   'To pole jest wymagane.',
        email:      'Wpisz poprawny adres e-mail.',
        url:        'Wpisz poprawny adres URL (z http:// lub https://).',
        minLength:  (n) => `Wpisz co najmniej ${n} znaków.`,
        maxLength:  (n) => `Maksymalnie ${n} znaków.`,
        min:        (n) => `Wartość nie może być mniejsza niż ${n}.`,
        max:        (n) => `Wartość nie może być większa niż ${n}.`,
        pattern:    'Wartość ma nieprawidłowy format.',
        passwordMatch: 'Hasła nie są identyczne.',
        number:     'Wpisz poprawną liczbę.'
    };

    /* ───────────────────────── WALIDATOR ────────────────────── */
    function validateField(field) {
        const value = (field.value || '').trim();
        const type = field.type;
        const required = field.hasAttribute('required');
        const min = field.getAttribute('minlength');
        const max = field.getAttribute('maxlength');
        const minVal = field.getAttribute('min');
        const maxVal = field.getAttribute('max');
        const pattern = field.getAttribute('pattern');
        const matchSelector = field.getAttribute('data-match');

        if (required && !value) return MSG.required;
        if (!value) return null; // puste, nie wymagane - OK

        if (type === 'email' && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) return MSG.email;
        if (type === 'url'   && !/^https?:\/\/\S+/.test(value)) return MSG.url;
        if (type === 'number') {
            const n = parseFloat(value);
            if (isNaN(n)) return MSG.number;
            if (minVal !== null && minVal !== undefined && n < parseFloat(minVal)) return MSG.min(minVal);
            if (maxVal !== null && maxVal !== undefined && n > parseFloat(maxVal)) return MSG.max(maxVal);
        }
        if (min && value.length < parseInt(min, 10)) return MSG.minLength(min);
        if (max && value.length > parseInt(max, 10)) return MSG.maxLength(max);
        if (pattern && !new RegExp('^(?:' + pattern + ')$').test(value)) return MSG.pattern;
        if (matchSelector) {
            const other = document.querySelector(matchSelector);
            if (other && other.value !== value) return MSG.passwordMatch;
        }
        return null;
    }

    function setFieldError(field, message) {
        const group = field.closest('.form-group') || field.parentElement;
        let hint = group ? group.querySelector('.form-error') : null;

        if (message) {
            field.classList.add('is-invalid');
            field.classList.remove('is-valid');
            field.setAttribute('aria-invalid', 'true');
            if (!hint && group) {
                hint = document.createElement('div');
                hint.className = 'form-error';
                group.appendChild(hint);
            }
            if (hint) hint.textContent = message;
        } else {
            field.classList.remove('is-invalid');
            if ((field.value || '').trim()) field.classList.add('is-valid');
            field.removeAttribute('aria-invalid');
            if (hint) hint.textContent = '';
        }
    }

    function validateForm(form) {
        const fields = form.querySelectorAll('input, textarea, select');
        let firstError = null;
        fields.forEach((f) => {
            if (f.disabled || f.type === 'hidden' || f.type === 'submit' || f.type === 'button') return;
            const err = validateField(f);
            setFieldError(f, err);
            if (err && !firstError) firstError = f;
        });
        if (firstError) {
            firstError.focus();
            if (firstError.scrollIntoView) firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
        return !firstError;
    }

    function attachValidator(form) {
        if (!form || form.__validatorAttached) return;
        form.__validatorAttached = true;

        // blur per field
        form.addEventListener('blur', (e) => {
            const f = e.target;
            if (f.matches && f.matches('input, textarea, select')) {
                setFieldError(f, validateField(f));
            }
        }, true);

        // input - czyść błąd gdy użytkownik poprawia
        form.addEventListener('input', (e) => {
            const f = e.target;
            if (f.matches && f.matches('input, textarea, select') && f.classList.contains('is-invalid')) {
                setFieldError(f, validateField(f));
            }
        });

        // submit
        form.addEventListener('submit', (e) => {
            if (!validateForm(form)) {
                e.preventDefault();
                if (global.Toast) global.Toast.warning('Popraw zaznaczone pola formularza.');
            }
        });
    }

    function initValidators() {
        document.querySelectorAll('form[data-validate]').forEach(attachValidator);
    }

    /* ───────────────────────── CONFIRM (data-confirm) ───────── */
    /*  Wzorzec: <form data-confirm="Czy na pewno chcesz usunąć?">
     *  Zastępuje legacy onsubmit="return confirm(...)" — używa
     *  natywnego Modal.confirm (UX > natywny confirm() + spójny styl)
     *  Delegated event-listener — działa dla form dodanych dynamicznie.
     */
    function initConfirms() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (!form || !form.matches || !form.matches('form[data-confirm]')) return;
            if (form.__confirmApproved) {
                form.__confirmApproved = false;
                return; // już potwierdzone, puszczamy submit
            }
            e.preventDefault();
            const msg = form.getAttribute('data-confirm') || 'Czy na pewno chcesz kontynuować?';
            const title = form.getAttribute('data-confirm-title') || 'Potwierdź operację';
            const isDanger = /usun|delete|skasuj|trwale|cofn/i.test(msg);

            const proceed = () => {
                form.__confirmApproved = true;
                // jeśli formularz ma submitter (np. button[name=action]), spróbuj go użyć
                if (typeof form.requestSubmit === 'function') {
                    form.requestSubmit();
                } else {
                    form.submit();
                }
            };

            if (global.Modal && typeof global.Modal.confirm === 'function') {
                global.Modal.confirm({
                    title, message: msg,
                    confirmLabel: isDanger ? 'Usuń' : 'Potwierdź',
                    cancelLabel: 'Anuluj',
                    danger: isDanger
                }).then((ok) => { if (ok) proceed(); });
            } else if (window.confirm(msg)) {
                proceed();
            }
        }, true); // capture phase aby uniknąć wcześniejszych handlerów
    }

    /* ───────────────────────── SAVE STATE ───────────────────── */
    const SaveState = (function () {
        const states = new WeakMap();

        function init(form, indicatorEl) {
            if (!form) return null;
            const s = { form, indicator: indicatorEl, dirty: false, saving: false };
            states.set(form, s);

            // śledzenie zmian
            form.addEventListener('input', () => mark(form, 'dirty'));
            form.addEventListener('change', () => mark(form, 'dirty'));

            // beforeunload guard
            window.addEventListener('beforeunload', (e) => {
                const cur = states.get(form);
                if (cur && cur.dirty && !cur.saving) {
                    e.preventDefault();
                    e.returnValue = '';
                    return '';
                }
            });
            return s;
        }

        function mark(form, state) {
            const s = states.get(form);
            if (!s) return;
            s.dirty  = (state === 'dirty');
            s.saving = (state === 'saving');
            render(s);
        }

        function render(s) {
            if (!s.indicator) return;
            let label, cls;
            if (s.saving)      { label = 'Zapisuję…';     cls = 'saving'; }
            else if (s.dirty)  { label = 'Niezapisane zmiany'; cls = 'dirty'; }
            else               { label = 'Wszystko zapisane'; cls = 'saved'; }
            s.indicator.className = 'save-indicator ' + cls;
            s.indicator.innerHTML = `<span class="save-dot"></span><span class="save-label">${label}</span>`;
        }

        return {
            init,
            markDirty:  (form) => mark(form, 'dirty'),
            markSaving: (form) => mark(form, 'saving'),
            markSaved:  (form) => mark(form, 'saved')
        };
    })();

    /* ───────────────────────── LOADING (przyciski) ─────────── */
    function setLoading(btn, isLoading) {
        if (!btn) return;
        if (isLoading) {
            if (!btn.dataset.originalHtml) btn.dataset.originalHtml = btn.innerHTML;
            btn.disabled = true;
            btn.classList.add('is-loading');
            btn.innerHTML = '<span class="spinner spinner-sm"></span> <span>Pracuję…</span>';
        } else {
            btn.disabled = false;
            btn.classList.remove('is-loading');
            if (btn.dataset.originalHtml) {
                btn.innerHTML = btn.dataset.originalHtml;
                delete btn.dataset.originalHtml;
            }
        }
    }

    /* ───────────────────────── BOOTSTRAP ─────────────────────── */
    document.addEventListener('DOMContentLoaded', () => {
        initValidators();
        initConfirms();
    });

    global.Forms = {
        validate: validateForm,
        attach: attachValidator,
        SaveState,
        setLoading,
        MSG
    };

})(window);
