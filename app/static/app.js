// ─── Configuration ─────────────────────────────────────────────────
const API_URL        = '/metrics';
const POLL_INTERVAL  = 3000;        // 3s live refresh (lab spec: 15-30s, faster for demo)
const SLO_P95_MS     = 2000;        // From slo.yaml
const SLO_ERROR_PCT  = 2.0;
const SLO_QUALITY    = 0.80;
const MAX_POINTS     = 30;

// ─── State ─────────────────────────────────────────────────────────
let prevTraffic = 0;
let labels        = [];
let latencyP50    = [], latencyP95 = [], latencyP99 = [];
let trafficData   = [];
let errorRateData  = [];
let costData       = [];
let tokensInData   = [], tokensOutData = [];

// ─── Chart Instances ───────────────────────────────────────────────
let charts = {};

// ─── Helper: push bounded time-series ──────────────────────────────
function push(arr, val) {
    arr.push(val);
    if (arr.length > MAX_POINTS) arr.shift();
}

function now() {
    return new Date().toLocaleTimeString('en-US', { hour12: false });
}

// ─── Chart factory helpers ─────────────────────────────────────────
const GRID_COLOR  = 'rgba(0,0,0,0.05)';
const FONT_FAMILY = "'Inter', sans-serif";

function baseScales(yMin = null, suggestedMax = null) {
    const y = {
        border: { display: false },
        grid:   { color: GRID_COLOR },
        ticks:  { font: { family: FONT_FAMILY, size: 10 }, color: '#9CA3AF' },
    };
    if (yMin !== null)      y.min = yMin;
    if (suggestedMax !== null) y.suggestedMax = suggestedMax;
    return {
        x: { display: false },
        y
    };
}

// ─── Initialise Charts ─────────────────────────────────────────────
function initCharts() {
    Chart.defaults.font.family = FONT_FAMILY;

    // 1. Latency Line Chart
    charts.latency = new Chart(document.getElementById('latencyChart'), {
        type: 'line',
        data: {
            labels,
            datasets: [
                {
                    label: 'P50', data: latencyP50,
                    borderColor: '#1D70B8', backgroundColor: 'rgba(29,112,184,0.06)',
                    borderWidth: 2, pointRadius: 0, fill: false, tension: 0.4
                },
                {
                    label: 'P95', data: latencyP95,
                    borderColor: '#1C2C5B', backgroundColor: 'rgba(28,44,91,0.06)',
                    borderWidth: 2.5, pointRadius: 2, pointBackgroundColor: '#1C2C5B',
                    fill: false, tension: 0.4
                },
                {
                    label: 'P99', data: latencyP99,
                    borderColor: '#F04438', backgroundColor: 'rgba(240,68,56,0.06)',
                    borderWidth: 1.5, pointRadius: 0, fill: false, tension: 0.4,
                    borderDash: [4, 3]
                },
                {
                    label: 'SLO 2000ms', data: Array(MAX_POINTS).fill(SLO_P95_MS),
                    borderColor: '#F04438', borderWidth: 1.5,
                    pointRadius: 0, fill: false, borderDash: [6, 4],
                    backgroundColor: 'transparent', tension: 0
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
            plugins: {
                legend: {
                    display: true, position: 'bottom', align: 'end',
                    labels: { boxWidth: 10, padding: 14, font: { size: 11 }, usePointStyle: true }
                },
                tooltip: { mode: 'index', intersect: false }
            },
            scales: baseScales(0)
        }
    });

    // 2. Traffic Area Chart
    charts.traffic = new Chart(document.getElementById('trafficChart'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Requests', data: trafficData,
                borderColor: '#0EA5E9', backgroundColor: 'rgba(14,165,233,0.1)',
                borderWidth: 2, pointRadius: 0, fill: true, tension: 0.4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
            plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
            scales: baseScales(0)
        }
    });

    // 3. Error Rate Chart
    charts.error = new Chart(document.getElementById('errorChart'), {
        type: 'bar',
        data: {
            labels,
            datasets: [{
                label: 'Error %', data: errorRateData,
                backgroundColor: errorRateData.map(v => v > SLO_ERROR_PCT ? 'rgba(240,68,56,0.7)' : 'rgba(240,68,56,0.25)'),
                borderRadius: 4, borderSkipped: false
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
            plugins: { legend: { display: false } },
            scales: baseScales(0, 10)
        }
    });

    // 4. Cost Line Chart
    charts.cost = new Chart(document.getElementById('costChart'), {
        type: 'line',
        data: {
            labels,
            datasets: [{
                label: 'Total Cost $', data: costData,
                borderColor: '#F79009', backgroundColor: 'rgba(247,144,9,0.1)',
                borderWidth: 2, pointRadius: 2, pointBackgroundColor: '#F79009',
                fill: true, tension: 0.4
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, animation: { duration: 400 },
            plugins: { legend: { display: false }, tooltip: { mode: 'index', intersect: false } },
            scales: baseScales(0)
        }
    });

    // 5. Token Stacked Bar
    charts.tokens = new Chart(document.getElementById('tokensChart'), {
        type: 'bar',
        data: {
            labels,
            datasets: [
                {
                    label: 'Tokens In', data: tokensInData,
                    backgroundColor: 'rgba(14,165,233,0.6)', borderRadius: 3, stack: 'tokens'
                },
                {
                    label: 'Tokens Out', data: tokensOutData,
                    backgroundColor: 'rgba(18,183,106,0.6)', borderRadius: 3, stack: 'tokens'
                }
            ]
        },
        options: {
            responsive: true, maintainAspectRatio: false, animation: { duration: 300 },
            plugins: {
                legend: {
                    display: true, position: 'bottom', align: 'end',
                    labels: { boxWidth: 10, padding: 12, font: { size: 11 }, usePointStyle: true }
                }
            },
            scales: { ...baseScales(0), x: { display: false, stacked: true }, y: { ...baseScales(0).y, stacked: true } }
        }
    });

    // 6. Quality Gauge (doughnut half)
    charts.quality = new Chart(document.getElementById('qualityGauge'), {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [0, 1],
                backgroundColor: ['#E5E7EB', '#E5E7EB'],
                borderWidth: 0,
                circumference: 180,
                rotation: 270
            }]
        },
        options: {
            responsive: true, maintainAspectRatio: false, animation: { duration: 700 },
            cutout: '72%',
            plugins: { legend: { display: false }, tooltip: { enabled: false } }
        }
    });
}

// ─── Fetch & Update Loop ───────────────────────────────────────────
async function fetchMetrics() {
    try {
        const res = await fetch(API_URL);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const d = await res.json();
        update(d);
        document.getElementById('last-updated').textContent = new Date().toLocaleTimeString();
    } catch (e) {
        console.warn('Metrics fetch failed:', e.message);
    }
}

function update(d) {
    const t = now();

    // ── Push time-series ──
    if (labels.length >= MAX_POINTS) {
        labels.shift();
        [latencyP50, latencyP95, latencyP99, trafficData,
         errorRateData, costData, tokensInData, tokensOutData].forEach(a => a.shift());
    }

    const totalErrors = Object.values(d.error_breakdown || {}).reduce((a, v) => a + v, 0);
    const errPct = d.traffic > 0 ? +((totalErrors / d.traffic) * 100).toFixed(2) : 0;

    labels.push(t);
    push(latencyP50,   Math.round(d.latency_p50));
    push(latencyP95,   Math.round(d.latency_p95));
    push(latencyP99,   Math.round(d.latency_p99));
    push(trafficData,  d.traffic);
    push(errorRateData, errPct);
    push(costData,     d.total_cost_usd);
    push(tokensInData,  d.tokens_in_total);
    push(tokensOutData, d.tokens_out_total);

    // ── KPI Cards ──
    const deltaTraffic = d.traffic - prevTraffic;
    prevTraffic = d.traffic;

    el('val-traffic').textContent = fmtNum(d.traffic);
    el('trend-traffic').textContent = deltaTraffic > 0 ? `+${deltaTraffic} this interval` : 'No new requests';

    el('val-p95').innerHTML = `${Math.round(d.latency_p95)}<small>ms</small>`;
    const badge = el('slo-p95-badge');
    if (d.latency_p95 > SLO_P95_MS) {
        badge.textContent = 'SLO BREACH ⚠'; badge.className = 'kpi-trend slo-err';
    } else {
        badge.textContent = 'SLO OK ✓';     badge.className = 'kpi-trend slo-ok';
    }

    el('val-error-rate').innerHTML = `${errPct.toFixed(1)}<small>%</small>`;
    el('val-error-count').textContent = `${totalErrors} error${totalErrors !== 1 ? 's' : ''}`;

    el('val-cost-total').textContent = `$${d.total_cost_usd.toFixed(4)}`;
    el('val-cost-avg').textContent   = `$${d.avg_cost_usd.toFixed(4)}`;

    const q = d.quality_avg || 0;
    el('val-quality').textContent = q.toFixed(2);

    // ── Latency Pills ──
    el('badge-p50').textContent = Math.round(d.latency_p50);
    el('badge-p95').textContent = Math.round(d.latency_p95);
    el('badge-p99').textContent = Math.round(d.latency_p99);
    const p95pill = document.querySelector('.pill.p95');
    if (d.latency_p95 > SLO_P95_MS) p95pill.classList.add('slo-breach');
    else p95pill.classList.remove('slo-breach');

    // ── Token totals ──
    el('total-tokens-in').textContent  = fmtNum(d.tokens_in_total);
    el('total-tokens-out').textContent = fmtNum(d.tokens_out_total);

    // ── Error breakdown list ──
    const breakdown = d.error_breakdown || {};
    const errKeys = Object.keys(breakdown);
    const errDiv = el('error-breakdown');
    if (errKeys.length === 0) {
        errDiv.innerHTML = '<div class="no-error-row"><span class="green-dot"></span> No errors detected</div>';
    } else {
        errDiv.innerHTML = errKeys.map(k =>
            `<div class="error-row"><span class="error-name">${k}</span><span class="error-count">${breakdown[k]}</span></div>`
        ).join('');
    }

    // ── Incident Badge ──
    const isIncident = d.latency_p95 > SLO_P95_MS || errPct > SLO_ERROR_PCT;
    const incBadge = el('incident-badge');
    incBadge.className = 'incident-badge ' + (isIncident ? 'firing' : 'normal');
    el('incident-text').textContent = isIncident ? 'Incident Detected' : 'All Systems Normal';

    // ── SLO Progress Bars ──
    const latRatio = d.traffic > 0 ? Math.min(1, d.latency_p95 / SLO_P95_MS) : 0;
    updateSloBar('slo-latency-bar', 'slo-latency-pct', latRatio, true);

    const errRatio = Math.min(1, errPct / SLO_ERROR_PCT);
    updateSloBar('slo-error-bar', 'slo-error-pct', 1 - errRatio, false, errPct);

    const qRatio = Math.min(1, q / 1.0);
    updateSloBar('slo-quality-bar', 'slo-quality-pct', qRatio, false, null, q);

    // ── Quality Gauge ──
    const gaugeScore = Math.min(q, 1);
    const gaugeColor = q >= SLO_QUALITY ? '#12B76A' : q >= 0.6 ? '#F79009' : '#F04438';
    charts.quality.data.datasets[0].data = [gaugeScore, 1 - gaugeScore];
    charts.quality.data.datasets[0].backgroundColor = [gaugeColor, '#F3F4F6'];
    charts.quality.update('none');
    el('gauge-score').textContent = q.toFixed(2);
    el('gauge-score').style.color = gaugeColor;

    // ── Update Chart Data ──
    charts.latency.data.labels = [...labels];
    charts.latency.data.datasets[0].data = [...latencyP50];
    charts.latency.data.datasets[1].data = [...latencyP95];
    charts.latency.data.datasets[2].data = [...latencyP99];
    charts.latency.data.datasets[3].data = Array(labels.length).fill(SLO_P95_MS);
    charts.latency.update();

    charts.traffic.data.labels = [...labels];
    charts.traffic.data.datasets[0].data = [...trafficData];
    charts.traffic.update();

    charts.error.data.labels = [...labels];
    charts.error.data.datasets[0].data = [...errorRateData];
    charts.error.data.datasets[0].backgroundColor = errorRateData.map(v =>
        v > SLO_ERROR_PCT ? 'rgba(240,68,56,0.75)' : 'rgba(240,68,56,0.25)'
    );
    charts.error.update();

    charts.cost.data.labels = [...labels];
    charts.cost.data.datasets[0].data = [...costData];
    charts.cost.update();

    charts.tokens.data.labels = [...labels];
    charts.tokens.data.datasets[0].data = [...tokensInData];
    charts.tokens.data.datasets[1].data = [...tokensOutData];
    charts.tokens.update();
}

function updateSloBar(barId, pctId, ratio, higherIsBad = false, rawPct = null, rawScore = null) {
    const bar = el(barId);
    const pctEl = el(pctId);
    const pct = Math.round(ratio * 100);
    bar.style.width = pct + '%';

    const isBad = higherIsBad ? ratio > 0.8 : ratio < SLO_QUALITY;
    bar.className = 'slo-progress-fill ' + (ratio >= 1.0 && higherIsBad ? 'danger' : ratio > 0.8 && higherIsBad ? 'warning' : '');

    if (rawPct !== null)   pctEl.textContent = rawPct.toFixed(1) + '%';
    else if (rawScore !== null) pctEl.textContent = rawScore.toFixed(2);
    else pctEl.textContent = pct + '%';
}

// ─── Utility ───────────────────────────────────────────────────────
const el = id => document.getElementById(id);

function fmtNum(n) {
    if (n >= 1e6) return (n / 1e6).toFixed(1) + 'M';
    if (n >= 1e3) return (n / 1e3).toFixed(1) + 'K';
    return String(n);
}

// ─── Boot ───────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    initCharts();
    fetchMetrics();
    setInterval(fetchMetrics, POLL_INTERVAL);
});
