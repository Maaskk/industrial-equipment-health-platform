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
    text("stage-engine", prediction.engine_id);
    text("scene-cycle", `CYCLE ${prediction.cycle} / ${state.latestCycle}`);
    text("stage-risk", prediction.risk_level.toUpperCase());
    text("stage-rul", `${Number(prediction.remaining_useful_life).toFixed(1)} CYCLES RUL`);
    text("visual-condition", `${prediction.risk_level.toUpperCase()} · ${prediction.recommendation}`);
    text("rail-recommendation", prediction.recommendation);
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
      "Drift status": monitor.drift.status === "insufficient_data"
        ? `Insufficient observations (${monitor.drift.sample_count} samples, ${monitor.drift.unique_observations} unique)`
        : (monitor.drift.drift_detected ? "Mean shift detected" : "No threshold breach"),
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
  initialised: false, unavailable: false, exploded: false, playing: false, airflowVisible: true,
  init() {
    const container = $("engine-viewer");
    if (!window.WebGLRenderingContext) throw new Error("WebGL is unavailable");
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0x030912);
    this.scene.fog = new THREE.FogExp2(0x030912, .035);
    this.camera = new THREE.PerspectiveCamera(34, container.clientWidth / container.clientHeight, .1, 100);
    this.camera.position.set(8.5, 3.4, 10.5);
    this.camera.lookAt(0, 0, 0);
    this.renderer = new THREE.WebGLRenderer({antialias:true, powerPreference:"high-performance"});
    this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio));
    this.renderer.setSize(container.clientWidth, container.clientHeight);
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.25;
    container.replaceChildren(this.renderer.domElement);

    this.group = new THREE.Group();
    this.group.rotation.set(.05, -.2, 0);
    this.scene.add(this.group);
    this.componentGroups = {};
    this.explodable = [];
    this.rotors = [];

    const metal = new THREE.MeshStandardMaterial({color:0x9eabb7, roughness:.28, metalness:.88});
    const titanium = new THREE.MeshStandardMaterial({color:0x526577, roughness:.34, metalness:.82});
    const dark = new THREE.MeshStandardMaterial({color:0x17293c, roughness:.25, metalness:.78});
    const edge = new THREE.MeshStandardMaterial({color:0xd9e5ef, roughness:.2, metalness:.9});
    const copper = new THREE.MeshStandardMaterial({color:0xd4853b, roughness:.3, metalness:.65, emissive:0x4b1600});
    const hot = new THREE.MeshStandardMaterial({color:0xff4b36, roughness:.35, metalness:.35, emissive:0x7a1008, emissiveIntensity:.9});
    const shell = new THREE.MeshPhysicalMaterial({color:0x6c8193, roughness:.2, metalness:.75, transparent:true, opacity:.22, side:THREE.DoubleSide, depthWrite:false});
    this.riskMaterial = new THREE.MeshStandardMaterial({color:0x55d6a0, emissive:0x0b5e43, emissiveIntensity:1.2, roughness:.3});

    const cylinder = (length, radiusA, radiusB, material, x, open = false) => {
      const mesh = new THREE.Mesh(new THREE.CylinderGeometry(radiusA, radiusB, length, 64, 1, open), material);
      mesh.rotation.z = Math.PI / 2; mesh.position.x = x; return mesh;
    };
    const ring = (radius, tube, material, x) => {
      const mesh = new THREE.Mesh(new THREE.TorusGeometry(radius, tube, 14, 72), material);
      mesh.rotation.y = Math.PI / 2; mesh.position.x = x; return mesh;
    };
    const stage = (name, x, radius, bladeCount, material) => {
      const group = new THREE.Group(); group.position.x = x; group.userData.homeX = x;
      group.add(ring(radius, .035, edge, 0));
      const hub = cylinder(.16, .22, .22, dark, 0); group.add(hub);
      for (let index=0; index<bladeCount; index+=1) {
        const blade = new THREE.Mesh(new THREE.BoxGeometry(.07, radius*.72, .11), material);
        blade.position.y = radius*.48; blade.rotation.x = index * Math.PI * 2 / bladeCount;
        group.add(blade);
      }
      this.group.add(group); this.rotors.push(group); this.explodable.push(group); this.componentGroups[name] = group;
      return group;
    };

    const shaft = cylinder(7.2, .075, .075, edge, 0); this.group.add(shaft);
    const fanGroup = new THREE.Group(); fanGroup.position.x=-3.2; fanGroup.userData.homeX=-3.2;
    fanGroup.add(cylinder(.5,.32,.22,titanium,0));
    for(let index=0;index<22;index+=1){
      const blade=new THREE.Mesh(new THREE.BoxGeometry(.11,1.15,.15),metal);
      blade.position.y=.68; blade.rotation.x=index*Math.PI*2/22; blade.rotation.z=-.12; fanGroup.add(blade);
    }
    fanGroup.add(ring(1.22,.07,edge,-.2)); this.group.add(fanGroup); this.rotors.push(fanGroup); this.explodable.push(fanGroup); this.componentGroups.fan=fanGroup;

    const intakeGroup=new THREE.Group(); intakeGroup.position.x=-3.85; intakeGroup.userData.homeX=-3.85;
    intakeGroup.add(ring(1.42,.14,edge,0)); intakeGroup.add(cylinder(1.2,1.42,1.28,shell,.5,true));
    this.group.add(intakeGroup); this.explodable.push(intakeGroup);

    const compressorGroup=new THREE.Group(); compressorGroup.userData.homeX=0;
    [-2.35,-1.9,-1.45,-1.02,-.62].forEach((x,index)=>compressorGroup.add(stage(`compressor-${index}`,x,.94-index*.07,18,titanium)));
    compressorGroup.add(cylinder(2.25,1.05,.73,shell,-1.48,true)); this.group.add(compressorGroup); this.componentGroups.compressor=compressorGroup;

    const combustorGroup=new THREE.Group(); combustorGroup.position.x=.05; combustorGroup.userData.homeX=.05;
    combustorGroup.add(cylinder(1.15,.72,.72,shell,0,true));
    for(let index=0;index<10;index+=1){const can=cylinder(.72,.1,.1,copper,0);const angle=index*Math.PI*2/10;can.position.y=Math.cos(angle)*.53;can.position.z=Math.sin(angle)*.53;combustorGroup.add(can);}
    combustorGroup.add(ring(.73,.05,hot,-.48)); combustorGroup.add(ring(.73,.05,hot,.48));
    this.group.add(combustorGroup); this.explodable.push(combustorGroup); this.componentGroups.combustor=combustorGroup;

    const turbineGroup=new THREE.Group(); turbineGroup.userData.homeX=0;
    [1.0,1.42,1.82].forEach((x,index)=>turbineGroup.add(stage(`turbine-${index}`,x,.67-index*.08,16,index===0?hot:titanium)));
    turbineGroup.add(cylinder(1.45,.75,.57,shell,1.4,true)); this.group.add(turbineGroup); this.componentGroups.turbine=turbineGroup;

    const exhaustGroup=new THREE.Group(); exhaustGroup.position.x=2.75; exhaustGroup.userData.homeX=2.75;
    exhaustGroup.add(cylinder(1.65,.58,.9,titanium,0,true)); exhaustGroup.add(ring(.88,.07,edge,.8));
    exhaustGroup.add(cylinder(1.3,.18,.5,dark,.25)); this.group.add(exhaustGroup); this.explodable.push(exhaustGroup); this.componentGroups.exhaust=exhaustGroup;

    const pylons=[-.35,.35]; pylons.forEach(z=>{const p=new THREE.Mesh(new THREE.BoxGeometry(2.4,.13,.12),dark);p.position.set(-1.2,1.12,z);this.group.add(p);});
    this.outerShell=cylinder(5.9,1.31,.9,shell,-.7,true); this.outerShell.rotation.z=Math.PI/2; this.group.add(this.outerShell);

    this.hotspots=[];
    [[-3.35,1.45,.15,"sensor_2",0x64b5ff],[-.2,1.03,.2,"sensor_3",0xffb44c],[2.55,.9,.15,"sensor_11",0xff5f55]].forEach(([x,y,z,sensor,color])=>{
      const holder=new THREE.Group();holder.position.set(x,y,z);
      const dot=new THREE.Mesh(new THREE.SphereGeometry(.095,20,20),new THREE.MeshStandardMaterial({color,emissive:color,emissiveIntensity:1.7}));
      const halo=ring(.18,.015,new THREE.MeshBasicMaterial({color,transparent:true,opacity:.75}),0);halo.rotation.set(0,0,0);
      holder.add(dot);holder.add(halo);holder.userData={sensor,dot,halo,value:null};this.group.add(holder);this.hotspots.push(holder);
    });

    const airflowCount=260; const positions=new Float32Array(airflowCount*3);
    for(let index=0;index<airflowCount;index+=1){positions[index*3]=-5+Math.random()*10;const angle=Math.random()*Math.PI*2;const radius=.15+Math.random()*.78;positions[index*3+1]=Math.cos(angle)*radius;positions[index*3+2]=Math.sin(angle)*radius;}
    const airflowGeometry=new THREE.BufferGeometry();airflowGeometry.setAttribute("position",new THREE.BufferAttribute(positions,3));
    this.airflow=new THREE.Points(airflowGeometry,new THREE.PointsMaterial({color:0x65bfff,size:.035,transparent:true,opacity:.78,depthWrite:false,blending:THREE.AdditiveBlending}));this.group.add(this.airflow);

    const stars=new Float32Array(900);for(let index=0;index<300;index+=1){stars[index*3]=(Math.random()-.5)*24;stars[index*3+1]=(Math.random()-.5)*12;stars[index*3+2]=-4-Math.random()*10;}
    const starsGeometry=new THREE.BufferGeometry();starsGeometry.setAttribute("position",new THREE.BufferAttribute(stars,3));this.scene.add(new THREE.Points(starsGeometry,new THREE.PointsMaterial({color:0x527ca3,size:.018,transparent:true,opacity:.55})));
    const grid=new THREE.GridHelper(22,44,0x24415e,0x13273c);grid.position.y=-1.55;this.scene.add(grid);
    this.scene.add(new THREE.HemisphereLight(0xbad9ff,0x07101c,2.4));
    const key=new THREE.DirectionalLight(0xffffff,5);key.position.set(-4,7,8);this.scene.add(key);
    const rim=new THREE.PointLight(0x4ca7ff,26,18);rim.position.set(-3,1,4);this.scene.add(rim);
    this.riskLight=new THREE.PointLight(0x55d6a0,20,12);this.riskLight.position.set(2,0,3);this.scene.add(this.riskLight);

    this.drag={active:false,x:0,y:0};
    container.addEventListener("pointerdown",event=>{this.drag={active:true,x:event.clientX,y:event.clientY};container.setPointerCapture?.(event.pointerId);});
    window.addEventListener("pointerup",()=>{this.drag.active=false;});
    window.addEventListener("pointermove",event=>{if(!this.drag.active)return;this.group.rotation.y+=(event.clientX-this.drag.x)*.006;this.group.rotation.x=Math.max(-.6,Math.min(.6,this.group.rotation.x+(event.clientY-this.drag.y)*.004));this.drag.x=event.clientX;this.drag.y=event.clientY;});
    container.addEventListener("wheel",event=>{event.preventDefault();const direction=this.camera.position.clone().normalize();this.camera.position.addScaledVector(direction,event.deltaY*.008);const distance=this.camera.position.length();if(distance<6)this.camera.position.setLength(6);if(distance>18)this.camera.position.setLength(18);this.camera.lookAt(this.focusTarget||new THREE.Vector3());},{passive:false});
    new ResizeObserver(()=>{const width=container.clientWidth,height=container.clientHeight;this.camera.aspect=width/height;this.camera.updateProjectionMatrix();this.renderer.setSize(width,height);}).observe(container);
    this.focusTarget=new THREE.Vector3(0,0,0); this.initialised=true; this.animate();
  },
  animate(){
    requestAnimationFrame(()=>this.animate());
    const speed=this.playing?.045:.006;this.rotors.forEach((rotor,index)=>{rotor.rotation.x+=speed*(1+index*.08);});
    if(this.airflowVisible){const positions=this.airflow.geometry.attributes.position.array;for(let index=0;index<positions.length;index+=3){positions[index]+=(this.playing?.075:.018);if(positions[index]>5)positions[index]=-5;}this.airflow.geometry.attributes.position.needsUpdate=true;}
    const pulse=1+Math.sin(Date.now()*.004)*.12;this.hotspots.forEach(marker=>marker.userData.halo.scale.setScalar(pulse));
    this.renderer.render(this.scene,this.camera);
  },
  reset(){this.focusTarget.set(0,0,0);this.camera.position.set(8.5,3.4,10.5);this.camera.lookAt(this.focusTarget);this.group.rotation.set(.05,-.2,0);qsa("[data-component]").forEach(button=>button.classList.toggle("active",button.dataset.component==="overview"));},
  focus(name){const targets={overview:[0,0,0,8.5,3.4,10.5],fan:[-3.15,0,0,2.5,1.2,6],compressor:[-1.45,0,0,4.6,2.2,7],combustor:[.05,0,0,5.8,2.1,6.4],turbine:[1.4,0,0,6.5,2,6],exhaust:[2.8,0,0,7.5,1.8,5.4]};const values=targets[name]||targets.overview;this.focusTarget.set(values[0],values[1],values[2]);this.camera.position.set(values[3],values[4],values[5]);this.camera.lookAt(this.focusTarget);},
  explode(){this.exploded=!this.exploded;this.explodable.forEach((part,index)=>{const direction=index-(this.explodable.length-1)/2;part.position.x=part.userData.homeX+(this.exploded?direction*.28:0);});text("explode-toggle",this.exploded?"Assembled view":"Exploded view");},
  toggleAirflow(){this.airflowVisible=!this.airflowVisible;this.airflow.visible=this.airflowVisible;$("airflow-toggle").classList.toggle("active",this.airflowVisible);},
  setPlaying(value){this.playing=value;text("scene-status",value?"REPLAY RUNNING":"DATASET LINKED");},
  setRisk(risk){const color={low:0x55d6a0,medium:0xffb44c,high:0xff4b42}[risk]||0x668099;this.riskLight.color.setHex(color);this.riskMaterial.color.setHex(color);this.hotspots.forEach(marker=>{marker.userData.dot.material.color.setHex(color);marker.userData.dot.material.emissive.setHex(color);});},
  setSensorValues(values){this.hotspots.forEach(marker=>{const value=Number(values[marker.userData.sensor]);marker.userData.value=value;const scale=1+Math.min(.65,Math.log10(Math.abs(value)+1)*.12);marker.userData.dot.scale.setScalar(scale);});},
};
$("camera-reset").addEventListener("click",()=>viewer.reset());
$("explode-toggle").addEventListener("click",()=>viewer.explode());
$("airflow-toggle").addEventListener("click",()=>viewer.toggleAirflow());
qsa("[data-component]").forEach(button=>button.addEventListener("click",()=>{qsa("[data-component]").forEach(item=>item.classList.toggle("active",item===button));viewer.focus(button.dataset.component);}));

boot();
