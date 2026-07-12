from __future__ import annotations


DASHBOARD_HTML = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Industrial Equipment Health Platform</title>
  <style>
    :root { color-scheme:dark; --space:#071018; --panel:#0d1821; --panel2:#111f2a; --line:#28404e; --text:#edf4f7; --muted:#8fa4af; --cyan:#43c7d9; --green:#4bd49b; --amber:#ffb648; --red:#ff625c; }
    * { box-sizing:border-box; }
    body { margin:0; min-width:320px; background:var(--space); color:var(--text); font:14px/1.45 Inter, ui-sans-serif, system-ui, sans-serif; }
    button, input { font:inherit; }
    header { height:72px; border-bottom:1px solid var(--line); background:#09131b; }
    .topbar { width:min(1440px, calc(100% - 32px)); height:100%; margin:auto; display:flex; align-items:center; justify-content:space-between; gap:24px; }
    .brand { display:flex; align-items:center; gap:14px; min-width:0; }
    .mark { width:34px; height:34px; border:2px solid var(--cyan); border-radius:50%; position:relative; flex:0 0 auto; }
    .mark::before { content:""; position:absolute; width:42px; height:1px; left:-6px; top:15px; background:var(--amber); transform:rotate(-24deg); }
    h1 { margin:0; font-size:18px; letter-spacing:0; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
    .mission { color:var(--muted); font-size:11px; text-transform:uppercase; }
    .live { display:flex; align-items:center; gap:8px; font-size:12px; text-transform:uppercase; white-space:nowrap; }
    .dot { width:8px; height:8px; border-radius:50%; background:var(--amber); box-shadow:0 0 14px currentColor; }
    .dot.ready { color:var(--green); background:var(--green); }
    main { width:min(1440px, calc(100% - 32px)); margin:auto; padding:22px 0 40px; }
    .strip { display:grid; grid-template-columns:repeat(4,minmax(0,1fr)); border:1px solid var(--line); background:var(--panel); }
    .strip-item { min-height:76px; padding:14px 18px; border-right:1px solid var(--line); }
    .strip-item:last-child { border-right:0; }
    .eyebrow { display:block; color:var(--muted); font-size:10px; font-weight:700; text-transform:uppercase; }
    .strip-value { display:block; margin-top:6px; font-size:17px; font-weight:750; }
    .ok { color:var(--green); } .low { color:var(--green); } .medium { color:var(--amber); } .high { color:var(--red); }
    .grid { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(320px,.75fr); gap:18px; margin-top:18px; }
    .panel { border:1px solid var(--line); background:var(--panel); min-width:0; }
    .panel-head { height:48px; display:flex; align-items:center; justify-content:space-between; padding:0 16px; border-bottom:1px solid var(--line); }
    h2 { margin:0; font-size:12px; text-transform:uppercase; }
    .panel-code { color:var(--cyan); font:11px ui-monospace, SFMono-Regular, Menlo, monospace; }
    .telemetry { padding:16px; }
    .telemetry-meta { display:flex; gap:24px; margin-bottom:12px; color:var(--muted); font-size:12px; }
    .telemetry-meta strong { color:var(--text); }
    canvas { display:block; width:100%; height:270px; border:1px solid var(--line); background:#08131b; }
    .sensor-grid { display:grid; grid-template-columns:repeat(7,minmax(0,1fr)); gap:8px; margin-top:12px; }
    .sensor { min-width:0; padding:9px; background:var(--panel2); border-bottom:2px solid var(--cyan); }
    .sensor span { display:block; color:var(--muted); font-size:9px; text-transform:uppercase; }
    .sensor strong { display:block; margin-top:4px; font:12px ui-monospace, SFMono-Regular, Menlo, monospace; overflow:hidden; text-overflow:ellipsis; }
    .assessment { display:grid; grid-template-columns:190px 1fr; gap:18px; padding:18px; }
    .gauge { width:176px; height:176px; border-radius:50%; display:grid; place-items:center; background:conic-gradient(var(--green) var(--gauge),#20313c 0); position:relative; }
    .gauge::before { content:""; position:absolute; inset:13px; border-radius:50%; background:var(--panel); border:1px solid var(--line); }
    .gauge-value { position:relative; text-align:center; }
    .gauge-value strong { display:block; font-size:46px; line-height:1; }
    .gauge-value span { color:var(--muted); font-size:11px; text-transform:uppercase; }
    .assessment-copy { display:flex; flex-direction:column; justify-content:center; min-width:0; }
    .risk-title { color:var(--muted); font-size:11px; text-transform:uppercase; }
    .risk-value { margin-top:5px; font-size:26px; font-weight:800; text-transform:uppercase; }
    .scan-meta { display:grid; grid-template-columns:1fr 1fr; gap:1px; margin:16px 0; background:var(--line); border:1px solid var(--line); }
    .scan-meta div { padding:10px; background:var(--panel2); }
    .scan-meta span { display:block; color:var(--muted); font-size:9px; text-transform:uppercase; }
    .scan-meta strong { display:block; margin-top:3px; font-size:12px; }
    button { height:42px; border:1px solid var(--cyan); border-radius:3px; padding:0 16px; background:var(--cyan); color:#041016; font-weight:800; cursor:pointer; text-transform:uppercase; }
    button:disabled { opacity:.5; cursor:wait; }
    .event-list { max-height:328px; overflow:auto; }
    .event { display:grid; grid-template-columns:78px 1fr 58px; gap:8px; align-items:center; min-height:54px; padding:8px 14px; border-bottom:1px solid var(--line); }
    .event:last-child { border-bottom:0; }
    .event-id { font:11px ui-monospace, SFMono-Regular, Menlo, monospace; }
    .event-rul { color:var(--muted); font-size:11px; }
    .event-risk { text-align:right; font-size:10px; font-weight:800; text-transform:uppercase; }
    .empty { padding:18px; color:var(--muted); }
    .error { min-height:20px; padding-top:9px; color:var(--red); font-size:12px; }
    @media (max-width:960px) { .grid { grid-template-columns:1fr; } .sensor-grid { grid-template-columns:repeat(4,1fr); } }
    @media (max-width:680px) { header { height:auto; } .topbar { min-height:76px; padding:12px 0; } .mission { display:none; } .strip { grid-template-columns:1fr 1fr; } .strip-item:nth-child(2) { border-right:0; } .strip-item:nth-child(-n+2) { border-bottom:1px solid var(--line); } .assessment { grid-template-columns:1fr; } .gauge { margin:auto; } .sensor-grid { grid-template-columns:repeat(3,1fr); } }
  </style>
</head>
<body>
  <header><div class="topbar"><div class="brand"><div class="mark" aria-hidden="true"></div><div><h1>Industrial Equipment Health Platform</h1><div class="mission">Fleet operations / mission control</div></div></div><div class="live"><span id="status-dot" class="dot"></span><span id="status">Connecting</span></div></div></header>
  <main>
    <div class="strip">
      <div class="strip-item"><span class="eyebrow">System</span><span id="system" class="strip-value">Initialising</span></div>
      <div class="strip-item"><span class="eyebrow">Tracked unit</span><span id="engine" class="strip-value">-</span></div>
      <div class="strip-item"><span class="eyebrow">Operating cycle</span><span id="cycle" class="strip-value">-</span></div>
      <div class="strip-item"><span class="eyebrow">Current condition</span><span id="condition" class="strip-value">Awaiting scan</span></div>
    </div>
    <div class="grid">
      <div>
        <section class="panel">
          <div class="panel-head"><h2>Live sensor telemetry</h2><span class="panel-code">CMAPSS / 21 CHANNELS</span></div>
          <div class="telemetry"><div class="telemetry-meta"><span>Unit <strong id="telemetry-unit">-</strong></span><span>Cycle <strong id="telemetry-cycle">-</strong></span></div><canvas id="chart" width="980" height="270" aria-label="Sensor telemetry chart"></canvas><div id="sensors" class="sensor-grid"></div></div>
        </section>
        <section class="panel" style="margin-top:18px">
          <div class="panel-head"><h2>Health assessment</h2><span class="panel-code">PREDICTIVE MAINTENANCE</span></div>
          <div class="assessment">
            <div id="gauge" class="gauge" style="--gauge:0%"><div class="gauge-value"><strong id="rul">-</strong><span>cycles remaining</span></div></div>
            <div class="assessment-copy"><span class="risk-title">Operational risk</span><span id="risk" class="risk-value">Not scanned</span><div class="scan-meta"><div><span>Scan response</span><strong id="latency">-</strong></div><div><span>Disposition</span><strong id="disposition">Stand by</strong></div></div><button id="predict" type="button">Run health scan</button><div id="error" class="error" role="alert"></div></div>
          </div>
        </section>
      </div>
      <section class="panel">
        <div class="panel-head"><h2>Assessment log</h2><span class="panel-code">LATEST 12</span></div>
        <div id="history" class="event-list"><div class="empty">No assessments recorded</div></div>
      </section>
    </div>
  </main>
  <script>
    let demoPayload;
    const $ = (id) => document.getElementById(id);
    const text = (id,value) => { $(id).textContent=value; };
    async function json(url,options) { const response=await fetch(url,options); if(!response.ok) throw new Error((await response.text())||response.statusText); return response.json(); }
    function drawTelemetry(features) {
      const values=Object.entries(features).filter(([key])=>/^sensor_/.test(key)).sort((a,b)=>Number(a[0].split('_')[1])-Number(b[0].split('_')[1]));
      const canvas=$('chart'), ctx=canvas.getContext('2d'), w=canvas.width, h=canvas.height, pad=28;
      ctx.clearRect(0,0,w,h); ctx.strokeStyle='#203744'; ctx.lineWidth=1;
      for(let i=0;i<6;i++){const y=pad+i*(h-pad*2)/5;ctx.beginPath();ctx.moveTo(pad,y);ctx.lineTo(w-pad,y);ctx.stroke();}
      const raw=values.map(([,v])=>Number(v)), min=Math.min(...raw), max=Math.max(...raw), span=max-min||1;
      ctx.strokeStyle='#43c7d9'; ctx.lineWidth=3; ctx.beginPath();
      raw.forEach((v,i)=>{const x=pad+i*(w-pad*2)/(raw.length-1), y=h-pad-((v-min)/span)*(h-pad*2); i?ctx.lineTo(x,y):ctx.moveTo(x,y);}); ctx.stroke();
      ctx.fillStyle='#ffb648'; raw.forEach((v,i)=>{const x=pad+i*(w-pad*2)/(raw.length-1), y=h-pad-((v-min)/span)*(h-pad*2);ctx.beginPath();ctx.arc(x,y,3.4,0,Math.PI*2);ctx.fill();});
      $('sensors').replaceChildren(...values.slice(0,14).map(([key,value])=>{const el=document.createElement('div');el.className='sensor';const name=document.createElement('span');name.textContent=key.replace('_',' ');const reading=document.createElement('strong');reading.textContent=Number(value).toFixed(3);el.append(name,reading);return el;}));
    }
    function renderHistory(rows) {
      if(!rows.length){$('history').innerHTML='<div class="empty">No assessments recorded</div>';return;}
      $('history').replaceChildren(...rows.slice().reverse().map(row=>{const el=document.createElement('div');el.className='event';const id=document.createElement('span');id.className='event-id';id.textContent=row.engine_id;const rul=document.createElement('span');rul.className='event-rul';rul.textContent=Number(row.remaining_useful_life).toFixed(1)+' cycles';const risk=document.createElement('span');risk.className='event-risk '+row.risk_level;risk.textContent=row.risk_level;el.append(id,rul,risk);return el;}));
    }
    async function refreshHistory(){renderHistory(await json('/predictions/recent'));}
    async function boot(){
      try { const [health,payload]=await Promise.all([json('/health'),json('/demo-payload')]);demoPayload=payload;text('status',health.status);$('status-dot').classList.toggle('ready',health.status==='ready');text('system',health.status==='ready'?'All systems nominal':'Degraded');$('system').className='strip-value '+(health.status==='ready'?'ok':'medium');text('engine',payload.engine_id);text('cycle',payload.cycle);text('telemetry-unit',payload.engine_id);text('telemetry-cycle',payload.cycle);drawTelemetry(payload.features);await refreshHistory(); } catch(error){text('status','Unavailable');text('error',error.message);}
    }
    $('predict').addEventListener('click',async()=>{$('predict').disabled=true;text('error','');try{const result=await json('/predict',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(demoPayload)});const rul=Number(result.remaining_useful_life);text('rul',rul.toFixed(0));text('risk',result.risk_level);$('risk').className='risk-value '+result.risk_level;text('latency',Number(result.latency_ms).toFixed(0)+' ms');text('condition',result.risk_level==='low'?'Flight ready':result.risk_level==='medium'?'Inspection due':'Maintenance hold');$('condition').className='strip-value '+result.risk_level;text('disposition',result.risk_level==='low'?'Continue operation':result.risk_level==='medium'?'Schedule inspection':'Remove from service');$('gauge').style.setProperty('--gauge',Math.min(100,Math.max(4,rul/1.5))+'%');await refreshHistory();}catch(error){text('error',error.message);}finally{$('predict').disabled=false;}});
    boot();
  </script>
</body>
</html>
"""
