from __future__ import annotations


DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Industrial Equipment Health Platform</title>
  <style>
    :root { color-scheme: light; --ink:#17202a; --muted:#5f6b76; --line:#d7dde3; --panel:#f6f8fa; --green:#147d64; --amber:#a45c00; --red:#b42318; }
    * { box-sizing: border-box; }
    body { margin:0; color:var(--ink); background:#fff; font:15px/1.5 Inter, ui-sans-serif, system-ui, sans-serif; }
    header { border-bottom:1px solid var(--line); background:#111820; color:#fff; }
    .topbar, main { width:min(1180px, calc(100% - 32px)); margin:auto; }
    .topbar { min-height:76px; display:flex; align-items:center; justify-content:space-between; gap:24px; }
    h1 { margin:0; font-size:22px; font-weight:700; letter-spacing:0; }
    .live { display:flex; align-items:center; gap:8px; font-size:13px; }
    .dot { width:9px; height:9px; border-radius:50%; background:#9aa4ad; }
    .dot.ready { background:#25b58a; }
    main { padding:28px 0 48px; }
    .summary { display:grid; grid-template-columns:repeat(4, minmax(0, 1fr)); border:1px solid var(--line); border-radius:6px; overflow:hidden; }
    .metric { padding:18px; min-height:92px; border-right:1px solid var(--line); background:#fff; }
    .metric:last-child { border-right:0; }
    .label { display:block; color:var(--muted); font-size:12px; font-weight:650; text-transform:uppercase; }
    .value { display:block; margin-top:8px; font-size:18px; font-weight:700; overflow-wrap:anywhere; }
    .workspace { display:grid; grid-template-columns:minmax(0, 1.25fr) minmax(300px, .75fr); gap:24px; margin-top:24px; }
    section { border-top:2px solid var(--ink); padding-top:16px; }
    h2 { margin:0 0 16px; font-size:16px; }
    .equipment { display:grid; grid-template-columns:1fr 120px; gap:12px; }
    label { display:block; color:var(--muted); font-size:12px; font-weight:650; margin-bottom:6px; }
    input { width:100%; height:42px; border:1px solid var(--line); border-radius:4px; padding:0 11px; background:#fff; color:var(--ink); }
    button { height:42px; border:0; border-radius:4px; padding:0 18px; background:var(--ink); color:#fff; font-weight:700; cursor:pointer; }
    button:disabled { opacity:.55; cursor:wait; }
    .action { display:flex; align-items:end; margin-top:16px; }
    .result { margin-top:22px; background:var(--panel); border-left:4px solid var(--green); padding:20px; min-height:132px; }
    .result.warn { border-color:var(--amber); }
    .result.danger { border-color:var(--red); }
    .rul { font-size:42px; line-height:1; font-weight:750; }
    .rul small { font-size:14px; color:var(--muted); font-weight:600; }
    .result-meta { display:flex; gap:22px; margin-top:16px; color:var(--muted); font-size:13px; }
    table { width:100%; border-collapse:collapse; font-size:13px; }
    th, td { padding:10px 8px; border-bottom:1px solid var(--line); text-align:left; }
    th { color:var(--muted); font-size:11px; text-transform:uppercase; }
    .risk { font-weight:700; }
    .risk.high { color:var(--red); } .risk.medium { color:var(--amber); } .risk.low { color:var(--green); }
    .error { color:var(--red); margin-top:12px; min-height:22px; }
    @media (max-width:820px) { .summary { grid-template-columns:1fr 1fr; } .metric:nth-child(2) { border-right:0; } .metric:nth-child(-n+2) { border-bottom:1px solid var(--line); } .workspace { grid-template-columns:1fr; } }
    @media (max-width:520px) { .topbar { align-items:flex-start; flex-direction:column; justify-content:center; padding:16px 0; } .summary { grid-template-columns:1fr; } .metric { border-right:0; border-bottom:1px solid var(--line); } .equipment { grid-template-columns:1fr; } }
  </style>
</head>
<body>
  <header><div class="topbar"><h1>Industrial Equipment Health Platform</h1><div class="live"><span id="status-dot" class="dot"></span><span id="status">Connecting</span></div></div></header>
  <main>
    <div class="summary">
      <div class="metric"><span class="label">Model</span><span id="model" class="value">-</span></div>
      <div class="metric"><span class="label">Version</span><span id="version" class="value">-</span></div>
      <div class="metric"><span class="label">Source</span><span id="source" class="value">-</span></div>
      <div class="metric"><span class="label">Features</span><span id="features" class="value">-</span></div>
    </div>
    <div class="workspace">
      <section>
        <h2>Equipment prediction</h2>
        <div class="equipment">
          <div><label for="engine">Equipment ID</label><input id="engine" readonly></div>
          <div><label for="cycle">Cycle</label><input id="cycle" type="number" readonly></div>
        </div>
        <div class="action"><button id="predict" type="button">Run prediction</button></div>
        <div id="result" class="result">
          <div class="rul"><span id="rul">-</span> <small>cycles RUL</small></div>
          <div class="result-meta"><span>Risk: <strong id="risk">-</strong></span><span>Latency: <strong id="latency">-</strong></span></div>
        </div>
        <div id="error" class="error" role="alert"></div>
      </section>
      <section>
        <h2>Recent predictions</h2>
        <table><thead><tr><th>Equipment</th><th>RUL</th><th>Risk</th></tr></thead><tbody id="history"><tr><td colspan="3">No predictions</td></tr></tbody></table>
      </section>
    </div>
  </main>
  <script>
    let demoPayload;
    const $ = (id) => document.getElementById(id);
    const text = (id, value) => { $(id).textContent = value; };
    async function json(url, options) { const response = await fetch(url, options); if (!response.ok) throw new Error((await response.text()) || response.statusText); return response.json(); }
    async function refreshHistory() {
      const rows = await json('/predictions/recent');
      $('history').innerHTML = rows.length ? rows.slice().reverse().map(row => `<tr><td>${row.engine_id}</td><td>${Number(row.remaining_useful_life).toFixed(2)}</td><td class="risk ${row.risk_level}">${row.risk_level}</td></tr>`).join('') : '<tr><td colspan="3">No predictions</td></tr>';
    }
    async function boot() {
      try {
        const [health, payload] = await Promise.all([json('/health'), json('/demo-payload')]);
        demoPayload = payload;
        text('status', health.status); $('status-dot').classList.toggle('ready', health.status === 'ready');
        text('model', health.model_name); text('version', health.model_version); text('source', health.model_source); text('features', health.feature_count);
        $('engine').value = payload.engine_id; $('cycle').value = payload.cycle;
        await refreshHistory();
      } catch (error) { text('status', 'Unavailable'); text('error', error.message); }
    }
    $('predict').addEventListener('click', async () => {
      $('predict').disabled = true; text('error', '');
      try {
        const result = await json('/predict', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(demoPayload)});
        text('rul', Number(result.remaining_useful_life).toFixed(2)); text('risk', result.risk_level); text('latency', `${Number(result.latency_ms).toFixed(2)} ms`);
        $('result').className = `result ${result.risk_level === 'high' ? 'danger' : result.risk_level === 'medium' ? 'warn' : ''}`;
        await refreshHistory();
      } catch (error) { text('error', error.message); } finally { $('predict').disabled = false; }
    });
    boot();
  </script>
</body>
</html>
"""
