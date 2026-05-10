/*  =============================================================
 *  charts.js — Konfiguracja Chart.js dla MasterContentAI
 *  -------------------------------------------------------------
 *  Centralne ustawienia spójne z design-systemem:
 *  - paleta (navy / indigo / cyan + status)
 *  - typografia (Inter)
 *  - polskie etykiety (PL locale)
 *  - tooltipy w stylu Linear/Vercel
 *  ============================================================= */
(function (global) {
    'use strict';

    if (typeof global.Chart === 'undefined') return;

    /* ───────────────────────── PALETA ────────────────────────── */
    const Palette = {
        navy:    '#0F172A',
        indigo:  '#4F46E5',
        cyan:    '#06B6D4',
        violet:  '#7C3AED',
        rose:    '#E11D48',
        amber:   '#F59E0B',
        emerald: '#10B981',
        slate:   '#64748B',
        slate100:'#F1F5F9',
        slate200:'#E2E8F0',
        slate400:'#94A3B8',
        slate700:'#334155'
    };

    const Series = [
        Palette.indigo, Palette.cyan, Palette.violet, Palette.emerald,
        Palette.amber, Palette.rose, Palette.navy, Palette.slate
    ];

    /* ───────────────────────── DEFAULTS ──────────────────────── */
    Chart.defaults.font.family = "'Inter', system-ui, -apple-system, sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = Palette.slate700;
    Chart.defaults.borderColor = Palette.slate200;

    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 16;
    Chart.defaults.plugins.legend.labels.boxWidth = 8;
    Chart.defaults.plugins.legend.labels.boxHeight = 8;

    Chart.defaults.plugins.tooltip.backgroundColor = '#0F172A';
    Chart.defaults.plugins.tooltip.titleColor = '#FFFFFF';
    Chart.defaults.plugins.tooltip.bodyColor = '#E2E8F0';
    Chart.defaults.plugins.tooltip.borderColor = 'rgba(255,255,255,0.08)';
    Chart.defaults.plugins.tooltip.borderWidth = 1;
    Chart.defaults.plugins.tooltip.padding = 10;
    Chart.defaults.plugins.tooltip.cornerRadius = 8;
    Chart.defaults.plugins.tooltip.titleFont = { weight: '600', size: 12 };
    Chart.defaults.plugins.tooltip.bodyFont = { size: 12 };
    Chart.defaults.plugins.tooltip.displayColors = true;
    Chart.defaults.plugins.tooltip.boxPadding = 6;

    Chart.defaults.maintainAspectRatio = false;
    Chart.defaults.responsive = true;

    /* ───────────────────────── HELPERS ───────────────────────── */
    function gradient(ctx, colorHex, alphaTop, alphaBottom) {
        const area = ctx.chart.chartArea;
        if (!area) return colorHex;
        const g = ctx.chart.ctx.createLinearGradient(0, area.top, 0, area.bottom);
        const rgb = hexToRgb(colorHex);
        g.addColorStop(0, `rgba(${rgb.r},${rgb.g},${rgb.b},${alphaTop || 0.25})`);
        g.addColorStop(1, `rgba(${rgb.r},${rgb.g},${rgb.b},${alphaBottom || 0})`);
        return g;
    }

    function hexToRgb(hex) {
        const m = hex.replace('#', '').match(/.{1,2}/g);
        return { r: parseInt(m[0], 16), g: parseInt(m[1], 16), b: parseInt(m[2], 16) };
    }

    function gridX(showGrid) {
        return {
            grid: { display: false, drawBorder: false },
            ticks: { color: Palette.slate, font: { size: 11 } }
        };
    }

    function gridY(showGrid) {
        return {
            grid: { color: Palette.slate200, drawBorder: false, drawTicks: false },
            ticks: { color: Palette.slate, font: { size: 11 }, padding: 8 },
            beginAtZero: true
        };
    }

    /* ───────────────────────── FABRYKI ───────────────────────── */
    function line(canvas, labels, datasets, options) {
        const ctx = canvas.getContext ? canvas.getContext('2d') : canvas;
        return new Chart(ctx, {
            type: 'line',
            data: {
                labels,
                datasets: datasets.map((d, i) => Object.assign({
                    tension: 0.35,
                    borderWidth: 2.5,
                    pointRadius: 0,
                    pointHoverRadius: 5,
                    pointBackgroundColor: '#FFFFFF',
                    pointBorderColor: d.borderColor || Series[i % Series.length],
                    pointBorderWidth: 2,
                    borderColor: Series[i % Series.length],
                    backgroundColor: (c) => gradient(c, d.color || Series[i % Series.length], 0.22, 0),
                    fill: true
                }, d))
            },
            options: Object.assign({
                interaction: { intersect: false, mode: 'index' },
                plugins: { legend: { display: datasets.length > 1, position: 'top', align: 'end' } },
                scales: { x: gridX(false), y: gridY(true) }
            }, options || {})
        });
    }

    function doughnut(canvas, labels, values, options) {
        const ctx = canvas.getContext ? canvas.getContext('2d') : canvas;
        return new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels,
                datasets: [{
                    data: values,
                    backgroundColor: labels.map((_, i) => Series[i % Series.length]),
                    borderWidth: 0,
                    hoverOffset: 8
                }]
            },
            options: Object.assign({
                cutout: '68%',
                plugins: {
                    legend: { position: 'right', align: 'center' },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => {
                                const total = ctx.dataset.data.reduce((a, b) => a + b, 0) || 1;
                                const pct = ((ctx.parsed / total) * 100).toFixed(1);
                                return ` ${ctx.label}: ${ctx.parsed} (${pct}%)`;
                            }
                        }
                    }
                }
            }, options || {})
        });
    }

    function bar(canvas, labels, datasets, options) {
        const ctx = canvas.getContext ? canvas.getContext('2d') : canvas;
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels,
                datasets: datasets.map((d, i) => Object.assign({
                    backgroundColor: Series[i % Series.length],
                    borderRadius: 6,
                    borderSkipped: false,
                    maxBarThickness: 36
                }, d))
            },
            options: Object.assign({
                plugins: { legend: { display: datasets.length > 1, position: 'top', align: 'end' } },
                scales: { x: gridX(false), y: gridY(true) }
            }, options || {})
        });
    }

    /* ───────────────────────── EKSPORT ───────────────────────── */
    global.Charts = { line, doughnut, bar, Palette, Series, gradient };

})(window);
