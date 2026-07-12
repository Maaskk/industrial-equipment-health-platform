import * as THREE from "/static/vendor/three.module.min.js";

const state = {
  page: "fleet",
  fleet: [],
  engines: [],
  replayEngine: "",
  cycle: 5,
  latestCycle: 5,
  mode: "operations",
  timer: null,
  lastRisk: null,
  batchCsv: "",
};
const $ = (id) => document.getElementById(id);
const qsa = (selector) => [...document.querySelectorAll(selector)];
const text = (id, value) => { $(id).textContent = value ?? "-"; };

async function api(url, options = {}) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = await response.text();
    try { detail = JSON.parse(detail).detail || detail; } catch {}
    throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
  }
  return response.json();
}

function toast(message) {
  text("toast", message);
  $("toast").classList.add("show");
  window.setTimeout(() => $("toast").classList.remove("show"), 2400);
}

function navigate() {
  const page = location.hash.slice(1) || "fleet";
  state.page = ["fleet", "replay", "lab", "platform", "docs"].includes(page) ? page : "fleet";
  qsa(".page").forEach((item) => item.classList.toggle("active", item.id === state.page));
  qsa("[data-nav]").forEach((item) => item.classList.toggle("active", item.dataset.nav === state.page));
  if (state.page === "fleet") loadFleet();
  if (state.page === "replay") initialiseReplay();
  if (state.page === "lab") initialiseLab();
  if (state.page === "platform") loadPlatform();
}
window.addEventListener("hashchange", navigate);

async function boot() {
  try {
    const health = await api("/health");
    $("api-dot").parentElement.classList.toggle("ready", health.status === "ready");
    text("api-label", health.status === "ready" ? "API ready" : "API degraded");
  } catch (error) {
    text("api-label", "API unavailable");
    toast(error.message);
  }
  navigate();
}

function riskClass(risk) {
  return ["low", "medium", "high"].includes(risk) ? risk : "";
}

async function loadFleet(force = false) {
  if (state.fleet.length && !force) return renderFleet();
  try {
    const [summary, rows] = await Promise.all([
      api("/api/fleet/summary"),
      api("/api/fleet/engines?sort=rul"),
    ]);
    state.fleet = rows;
    text("metric-total", summary.total_engines);
    text("metric-low", summary.risk_counts.low);
    text("metric-medium", summary.risk_counts.medium);
    text("metric-high", summary.risk_counts.high);
    text("metric-rul", summary.median_predicted_rul === null ? "No observations" : `${summary.median_predicted_rul} cycles`);
    text("metric-pipeline", summary.pipeline_health);
    renderFleet();
  } catch (error) {
    $("fleet-rows").innerHTML = `<tr><td colspan="7" class="empty">${escapeHtml(error.message)}</td></tr>`;
  }
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (character) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#039;",
  })[character]);
}

function filteredFleet() {
  const search = $("fleet-search").value.trim().toUpperCase();
  const subset = $("fleet-subset").value;
  const risk = $("fleet-risk").value;
  const sort = $("fleet-sort").value;
  const rows = state.fleet.filter((row) =>
    (!search || row.engine_id.includes(search))
    && (!subset || row.subset === subset)
    && (!risk || row.risk_level === risk)
  );
  return rows.sort((a, b) => {
    if (sort === "engine") return a.engine_id.localeCompare(b.engine_id);
    if (sort === "cycle") return a.latest_cycle - b.latest_cycle;
    return a.remaining_useful_life - b.remaining_useful_life;
  });
}

function renderFleet() {
  const rows = filteredFleet().slice(0, 200);
  $("fleet-rows").innerHTML = rows.length ? rows.map((row) => `
    <tr>
      <td><strong>${escapeHtml(row.engine_id)}</strong></td>
      <td>${row.subset}</td><td>${row.latest_cycle}</td>
      <td>${Number(row.remaining_useful_life).toFixed(1)}</td>
      <td><span class="risk-pill ${riskClass(row.risk_level)}">${row.risk_level}</span></td>
      <td>${escapeHtml(row.recommendation)}</td>
      <td><button class="link-button open-engine" data-engine="${row.engine_id}" type="button">Open</button></td>
    </tr>`).join("") : '<tr><td colspan="7" class="empty">No engines match these filters.</td></tr>';
  qsa(".open-engine").forEach((button) => button.addEventListener("click", () => {
    state.replayEngine = button.dataset.engine;
    location.hash = "replay";
  }));
}
["fleet-search", "fleet-subset", "fleet-risk", "fleet-sort"].forEach((id) => {
  $(id).addEventListener(id === "fleet-search" ? "input" : "change", renderFleet);
});
$("fleet-export").addEventListener("click", () => {
  const headers = ["engine_id", "subset", "latest_cycle", "remaining_useful_life", "risk_level", "recommendation"];
  const csv = [headers.join(","), ...filteredFleet().map((row) => headers.map((key) => JSON.stringify(row[key] ?? "")).join(","))].join("\n");
  download("fleet-health.csv", csv);
});

async function loadEngineOptions(subset, target, preferred = "") {
  const engines = await api(`/api/engines?subset=${subset}`);
  state.engines = engines;
  target.replaceChildren(...engines.map((engine) => {
    const option = document.createElement("option");
    option.value = engine.engine_id;
    option.textContent = `${engine.engine_id} (${engine.latest_cycle} cycles)`;
    return option;
  }));
  const available = engines.some((engine) => engine.engine_id === preferred);
  target.value = available ? preferred : (engines[0]?.engine_id || "");
  return engines;
}

let replayInitialised = false;
async function initialiseReplay() {
  if (!viewer.initialised && !viewer.unavailable) {
    try {
      viewer.init();
    } catch (error) {
      viewer.unavailable = true;
      $("engine-viewer").innerHTML = '<div class="viewer-fallback"><strong>Conceptual engine view unavailable</strong><span>The sensor replay and model prediction remain fully operational.</span></div>';
    }
  }
  if (replayInitialised && !state.replayEngine) return;
  replayInitialised = true;
  try {
    const preferred = state.replayEngine || "FD004_204";
    const subset = preferred.split("_")[0] || $("replay-subset").value;
    $("replay-subset").value = subset;
    await loadEngineOptions(subset, $("replay-engine"), preferred);
    state.replayEngine = $("replay-engine").value;
    await loadCycles(true);
  } catch (error) {
    text("replay-error", error.message);
  }
}

async function loadCycles(startAtEnd = false) {
  const data = await api(`/api/engines/${state.replayEngine}/cycles`);
  state.latestCycle = data.latest_cycle;
  $("cycle-slider").max = data.latest_cycle;
  state.cycle = startAtEnd ? Math.max(5, data.latest_cycle) : Math.min(Math.max(5, state.cycle), data.latest_cycle);
  $("cycle-slider").value = state.cycle;
  $("lab-cycle").max = data.latest_cycle;
  $("lab-cycle").value = state.cycle;
  await updateReplay();
}

function selectedSensors() {
  return qsa('input[name="sensor"]:checked').map((item) => item.value).slice(0, 3);
}

async function updateReplay() {
  if (!state.replayEngine) return;
  text("replay-error", "");
  text("replay-cycle-label", `${state.cycle} / ${state.latestCycle}`);
  try {
    const sensors = selectedSensors();
    const normalized = $("chart-display").value === "normalized";
    const [history, prediction] = await Promise.all([
      api(`/api/engines/${state.replayEngine}/cycle/${state.cycle}?sensors=${sensors.join(",")}&normalized=${normalized}`),
      api(`/api/engines/${state.replayEngine}/cycle/${state.cycle}/predict`, {
        method: "POST", headers: {"Content-Type": "application/json"},
        body: JSON.stringify({mode: state.mode}),
      }),
    ]);
    drawSensorChart(history);
    text("replay-rul", `${Number(prediction.remaining_useful_life).toFixed(1)} cycles`);
    text("replay-risk", prediction.risk_level.toUpperCase());
    $("replay-risk").className = riskClass(prediction.risk_level);
    text("replay-recommendation", prediction.recommendation);
    text("replay-latency", `${Number(prediction.latency_ms).toFixed(2)} ms`);
    $("truth-panel").hidden = state.mode !== "evaluation";
    if (state.mode === "evaluation") text("replay-truth", `${prediction.actual_rul} / ${prediction.prediction_error > 0 ? "+" : ""}${prediction.prediction_error}`);
    if (viewer.initialised) {
      viewer.setRisk(prediction.risk_level);
      viewer.setSensorValues(prediction.sensor_profile || {});
    }
    text("hotspot-s2", prediction.sensor_profile?.sensor_2 ?? "-");
    text("hotspot-s3", prediction.sensor_profile?.sensor_3 ?? "-");
    text("hotspot-s11", prediction.sensor_profile?.sensor_11 ?? "-");
    if ($("pause-risk").checked && state.lastRisk && state.lastRisk !== prediction.risk_level) stopReplay();
    state.lastRisk = prediction.risk_level;
  } catch (error) {
    text("replay-error", error.message);
    if (state.cycle < 5) text("replay-error", "At least five cycles are required for rolling features.");
  }
}

function drawSensorChart(data) {
  const canvas = $("sensor-chart");
  const ratio = window.devicePixelRatio || 1;
  const width = canvas.clientWidth || 800;
  const height = canvas.clientHeight || 330;
  canvas.width = width * ratio; canvas.height = height * ratio;
  const context = canvas.getContext("2d"); context.scale(ratio, ratio);
  context.clearRect(0, 0, width, height);
  const pad = {left: 48, right: 18, top: 20, bottom: 34};
  context.strokeStyle = "#d8d8d4"; context.lineWidth = 1;
  for (let index = 0; index < 5; index += 1) {
    const y = pad.top + index * (height - pad.top - pad.bottom) / 4;
    context.beginPath(); context.moveTo(pad.left, y); context.lineTo(width - pad.right, y); context.stroke();
  }
  const palette = ["#e23b2e", "#11243a", "#15805c"];
  const allValues = Object.values(data.series).flat();
  const min = Math.min(...allValues), max = Math.max(...allValues), span = max - min || 1;
  Object.entries(data.series).forEach(([name, values], seriesIndex) => {
    context.strokeStyle = palette[seriesIndex]; context.lineWidth = 2; context.beginPath();
    values.forEach((value, index) => {
      const x = pad.left + index * (width - pad.left - pad.right) / Math.max(1, values.length - 1);
      const y = height - pad.bottom - ((value - min) / span) * (height - pad.top - pad.bottom);
      index ? context.lineTo(x, y) : context.moveTo(x, y);
    });
    context.stroke();
    context.fillStyle = palette[seriesIndex]; context.fillText(name.replace("sensor_", "S"), pad.left + seriesIndex * 48, 13);
  });
  const markerX = width - pad.right;
  context.strokeStyle = "#e23b2e"; context.setLineDash([4, 4]); context.beginPath();
  context.moveTo(markerX, pad.top); context.lineTo(markerX, height - pad.bottom); context.stroke(); context.setLineDash([]);
  context.fillStyle = "#626262"; context.fillText("cycle", width - 48, height - 10); context.fillText(String(data.cycles[0]), pad.left - 6, height - 10); context.fillText(String(data.cycle), markerX - 12, height - 10);
}

$("replay-subset").addEventListener("change", async () => {
  await loadEngineOptions($("replay-subset").value, $("replay-engine"));
  state.replayEngine = $("replay-engine").value; await loadCycles(true);
});
$("replay-engine").addEventListener("change", async () => { state.replayEngine = $("replay-engine").value; await loadCycles(true); });
$("cycle-slider").addEventListener("input", () => { state.cycle = Number($("cycle-slider").value); text("replay-cycle-label", `${state.cycle} / ${state.latestCycle}`); });
$("cycle-slider").addEventListener("change", updateReplay);
$("previous-cycle").addEventListener("click", async () => { state.cycle = Math.max(5, state.cycle - 1); $("cycle-slider").value = state.cycle; await updateReplay(); });
$("next-cycle").addEventListener("click", async () => { state.cycle = Math.min(state.latestCycle, state.cycle + 1); $("cycle-slider").value = state.cycle; await updateReplay(); });
qsa('input[name="sensor"]').forEach((item) => item.addEventListener("change", () => {
  const checked = selectedSensors();
  if (!checked.length) { item.checked = true; return; }
  if (checked.length > 3) { item.checked = false; toast("Select at most three sensors."); }
  updateReplay();
}));
$("chart-display").addEventListener("change", () => { text("chart-mode-label", $("chart-display").value === "normalized" ? "Normalized profile" : "Raw values"); updateReplay(); });
qsa("[data-mode]").forEach((button) => button.addEventListener("click", () => {
  state.mode = button.dataset.mode;
  qsa("[data-mode]").forEach((item) => item.classList.toggle("active", item === button));
  text("mode-note", state.mode === "operations" ? "Future truth is hidden." : "Offline truth is visible for evaluation only.");
  updateReplay();
}));

function startReplay() {
  if (state.timer) return stopReplay();
  text("play-replay", "Pause"); viewer.setPlaying(true);
  state.timer = window.setInterval(async () => {
    if (state.cycle >= state.latestCycle) return stopReplay();
    state.cycle += 1; $("cycle-slider").value = state.cycle; await updateReplay();
  }, Number($("replay-speed").value));
}
function stopReplay() { window.clearInterval(state.timer); state.timer = null; text("play-replay", "Play"); viewer.setPlaying(false); }
$("play-replay").addEventListener("click", startReplay);
$("replay-speed").addEventListener("change", () => { if (state.timer) { stopReplay(); startReplay(); } });

let labInitialised = false;
async function initialiseLab() {
  if (labInitialised) return;
  labInitialised = true;
  const engines = await api("/api/engines?subset=FD004");
  $("lab-engine").replaceChildren(...engines.map((engine) => {
    const option = document.createElement("option"); option.value = engine.engine_id; option.textContent = engine.engine_id; option.dataset.latest = engine.latest_cycle; return option;
  }));
  $("lab-engine").value = engines.find((engine) => engine.engine_id === "FD004_204")?.engine_id || engines[0]?.engine_id;
  syncLabCycle();
}
function syncLabCycle() { $("lab-cycle").value = $("lab-engine").selectedOptions[0]?.dataset.latest || 5; }
$("lab-engine").addEventListener("change", syncLabCycle);
$("lab-predict").addEventListener("click", async () => {
  try {
    const result = await api(`/api/engines/${$("lab-engine").value}/cycle/${$("lab-cycle").value}/predict`, {method:"POST", headers:{"Content-Type":"application/json"}, body:'{"mode":"operations"}'});
    $("lab-result").className = "result-block";
    $("lab-result").innerHTML = `<strong>${result.remaining_useful_life} cycles RUL</strong><br><span class="${riskClass(result.risk_level)}">${result.risk_level.toUpperCase()}</span><br>${escapeHtml(result.recommendation)}`;
  } catch (error) { $("lab-result").textContent = error.message; }
});
$("csv-file").addEventListener("change", async () => { state.batchCsv = await $("csv-file").files[0]?.text() || ""; text("batch-result", state.batchCsv ? "File ready for validation." : "No file selected."); });
$("batch-score").addEventListener("click", async () => {
  try {
    const result = await api("/api/predict/batch", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({csv_text: state.batchCsv})});
    state.batchResult = result.csv; $("batch-download").disabled = !result.rows.length;
    $("batch-result").className = "result-block"; $("batch-result").innerHTML = `<strong>${result.rows.length} engines scored</strong><br>${result.rows.map((row) => `${row.engine_id}: ${row.remaining_useful_life} cycles (${row.risk_level})`).join("<br>")}`;
  } catch (error) { $("batch-result").textContent = error.message; }
});
$("batch-download").addEventListener("click", () => download("batch-predictions.csv", state.batchResult));
$("plan-service").addEventListener("click", async () => {
  try {
    const result = await api("/api/maintenance/plan", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({predicted_rul:Number($("plan-rul").value),average_cycles_per_day:Number($("plan-rate").value),safety_margin_cycles:Number($("plan-margin").value)})});
    $("plan-result").className = "result-block"; $("plan-result").innerHTML = `<strong>${result.maximum_cycles_before_service} cycles / about ${result.estimated_operating_days} operating days</strong><br>Priority: ${result.priority}<br>${result.recommendation}<br><small>Assumption: ${result.utilization_assumption} cycles/day</small>`;
  } catch (error) { $("plan-result").textContent = error.message; }
});

let platformLoaded = false;
async function loadPlatform() {
  if (platformLoaded) return;
  platformLoaded = true;
  try {
    const result = await api("/api/platform/status");
    $("pipeline-steps").replaceChildren(...result.pipeline.map((step) => detail(step.name, step.evidence, step.status)));
    $("model-info").replaceChildren(...Object.entries(result.model).map(([key, value]) => detail(key, Array.isArray(value) ? value.join(", ") : value)));
    const monitor = result.monitoring;
    const monitorValues = {
      "Total predictions": monitor.total_predictions,
      "Successful predictions": monitor.successful_predictions,
      "Median latency": monitor.median_latency_ms === null ? "No observations available" : `${monitor.median_latency_ms} ms`,
      "P95 latency": monitor.p95_latency_ms === null ? "No observations available" : `${monitor.p95_latency_ms} ms`,
      "Risk distribution": Object.entries(monitor.risk_counts).map(([key,value]) => `${key}: ${value}`).join(" / "),
      "Drift status": typeof monitor.drift === "string" ? monitor.drift : (monitor.drift.drift_detected ? "Mean shift detected" : "No threshold breach"),
    };
    $("monitoring-info").replaceChildren(...Object.entries(monitorValues).map(([key,value]) => detail(key,value)));
    renderMonitoringLog(monitor.recent);
  } catch (error) { $("pipeline-steps").innerHTML = `<p class="empty">${escapeHtml(error.message)}</p>`; }
}
function detail(label, value, status = "") {
  const article = document.createElement("article");
  article.innerHTML = `<span class="${status ? "status" : ""}">${escapeHtml(status || label)}</span><strong>${escapeHtml(value)}</strong>${status ? `<span>${escapeHtml(label)}</span>` : ""}`;
  return article;
}
function renderMonitoringLog(rows) {
  if (!rows.length) return $("monitoring-log").innerHTML = '<p class="empty">No observations available</p>';
  $("monitoring-log").innerHTML = `<table><thead><tr><th>Timestamp</th><th>Engine</th><th>Cycle</th><th>RUL</th><th>Change</th><th>Risk</th><th>Model</th></tr></thead><tbody>${rows.map((row) => `<tr><td>${escapeHtml(row.timestamp_utc || "-")}</td><td>${escapeHtml(row.engine_id)}</td><td>${row.cycle ?? "-"}</td><td>${row.remaining_useful_life}</td><td>${row.change_from_previous == null ? "-" : `${row.change_from_previous > 0 ? "+" : ""}${row.change_from_previous}`}</td><td class="${riskClass(row.risk_level)}">${row.risk_level}</td><td>${row.model_version}</td></tr>`).join("")}</tbody></table>`;
}
qsa("[data-tab]").forEach((button) => button.addEventListener("click", () => {
  qsa("[data-tab]").forEach((item) => item.classList.toggle("active", item === button));
  qsa(".tab-panel").forEach((panel) => panel.classList.toggle("active", panel.id === `${button.dataset.tab}-tab`));
}));

function download(filename, content) {
  const url = URL.createObjectURL(new Blob([content], {type:"text/csv"}));
  const link = document.createElement("a"); link.href = url; link.download = filename; link.click(); URL.revokeObjectURL(url);
}

const viewer = {
  initialised: false, unavailable: false, exploded: false, playing: false, angle: 0,
  init() {
    const container = $("engine-viewer");
    this.scene = new THREE.Scene(); this.scene.background = new THREE.Color(0xf0f1ef);
    this.camera = new THREE.PerspectiveCamera(36, container.clientWidth / container.clientHeight, .1, 100);
    this.camera.position.set(7, 4, 8);
    this.renderer = new THREE.WebGLRenderer({antialias:true});
    this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio)); this.renderer.setSize(container.clientWidth, container.clientHeight); container.appendChild(this.renderer.domElement);
    this.group = new THREE.Group(); this.scene.add(this.group);
    const metal = new THREE.MeshStandardMaterial({color:0xbac0c3, roughness:.45, metalness:.65});
    const dark = new THREE.MeshStandardMaterial({color:0x233646, roughness:.35, metalness:.7});
    const red = new THREE.MeshStandardMaterial({color:0xe23b2e, roughness:.5});
    const cylinders = [[2.8,1.2,metal,-1.2],[2.4,.92,dark,.8],[1.6,.64,metal,2.6]];
    this.parts = cylinders.map(([length,radius,material,x]) => {
      const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radius,radius*.88,length,48,1,true),material);
      mesh.rotation.z = Math.PI/2; mesh.position.x=x; this.group.add(mesh); return mesh;
    });
    const intake = new THREE.Mesh(new THREE.TorusGeometry(1.22,.12,16,64), red); intake.rotation.y=Math.PI/2; intake.position.x=-2.65; this.group.add(intake);
    this.rotor = new THREE.Group(); this.rotor.position.x=-2.55; this.group.add(this.rotor);
    for(let index=0;index<12;index+=1){const blade=new THREE.Mesh(new THREE.BoxGeometry(.08,.95,.18),dark);blade.position.y=.48;blade.rotation.x=index*Math.PI/6;this.rotor.add(blade);}
    this.hotspots = []; [[-1.5,.95,0],[.5,.76,0],[2.2,.52,0]].forEach((position,index)=>{const dot=new THREE.Mesh(new THREE.SphereGeometry(.11,16,16),red.clone());dot.position.set(...position);dot.userData.sensor=`sensor_${[2,3,11][index]}`;this.group.add(dot);this.hotspots.push(dot);});
    this.scene.add(new THREE.HemisphereLight(0xffffff,0x445566,2.2)); const key=new THREE.DirectionalLight(0xffffff,3);key.position.set(4,7,5);this.scene.add(key);
    this.drag={active:false,x:0,y:0}; container.addEventListener("pointerdown",(event)=>{this.drag={active:true,x:event.clientX,y:event.clientY};}); window.addEventListener("pointerup",()=>{this.drag.active=false;}); window.addEventListener("pointermove",(event)=>{if(!this.drag.active)return;this.group.rotation.y+=(event.clientX-this.drag.x)*.008;this.group.rotation.x+=(event.clientY-this.drag.y)*.006;this.drag.x=event.clientX;this.drag.y=event.clientY;}); container.addEventListener("wheel",(event)=>{event.preventDefault();this.camera.position.z=Math.max(5,Math.min(14,this.camera.position.z+event.deltaY*.008));},{passive:false});
    new ResizeObserver(()=>{const width=container.clientWidth,height=container.clientHeight;this.camera.aspect=width/height;this.camera.updateProjectionMatrix();this.renderer.setSize(width,height);}).observe(container);
    this.initialised=true; this.animate();
  },
  animate(){requestAnimationFrame(()=>this.animate());if(this.playing)this.rotor.rotation.x+=.025;this.renderer.render(this.scene,this.camera);},
  reset(){this.camera.position.set(7,4,8);this.group.rotation.set(0,0,0);},
  explode(){this.exploded=!this.exploded;this.parts.forEach((part,index)=>{part.position.x+=this.exploded?index*.55:-index*.55;});},
  setPlaying(value){this.playing=value;},
  setRisk(risk){const color={low:0x15805c,medium:0xc77a00,high:0xc92020}[risk]||0x626262;this.hotspots.forEach((dot)=>dot.material.color.setHex(color));},
  setSensorValues(values){this.hotspots.forEach((dot)=>{dot.userData.value=values[dot.userData.sensor];});},
};
$("camera-reset").addEventListener("click",()=>viewer.reset());
$("explode-toggle").addEventListener("click",()=>viewer.explode());

boot();
