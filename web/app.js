const fileInput = document.getElementById("fileInput");
const dropzone = document.getElementById("dropzone");
const preview = document.getElementById("preview");
const dropPrompt = document.getElementById("dropPrompt");
const categorySelect = document.getElementById("category");
const inspectButton = document.getElementById("inspectButton");
const overlay = document.getElementById("overlay");
const emptyResult = document.getElementById("emptyResult");
const loader = document.getElementById("loader");
const resultState = document.getElementById("resultState");
const score = document.getElementById("score");
const threshold = document.getElementById("threshold");
const latency = document.getElementById("latency");
const guidance = document.getElementById("guidance");
const warning = document.getElementById("configurationWarning");
const reviewActions = document.getElementById("reviewActions");
const historyRows = document.getElementById("historyRows");
const refreshHistory = document.getElementById("refreshHistory");
const refreshSystem = document.getElementById("refreshSystem");

let selectedFile = null;
let categories = [];
let currentInspectionId = null;

function navigate(page) {
  document.querySelectorAll("[data-page]").forEach(section => {
    section.classList.toggle("active", section.dataset.page === page);
  });
  document.querySelectorAll("[data-page-link]").forEach(item => {
    item.classList.toggle("active", item.dataset.pageLink === page);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

document.querySelectorAll("[data-page-link]").forEach(item => {
  item.addEventListener("click", event => {
    event.preventDefault();
    navigate(item.dataset.pageLink);
  });
});

function setWarning(message = "") {
  warning.textContent = message;
  warning.classList.toggle("hidden", !message);
}

function setImage(file) {
  if (!file) return;
  selectedFile = file;
  preview.src = URL.createObjectURL(file);
  preview.style.display = "block";
  dropPrompt.style.display = "none";
  inspectButton.disabled = false;
}

async function loadCategories() {
  const response = await fetch("/api/categories");
  const data = await response.json();
  categories = data.categories || [];

  categorySelect.innerHTML = "";
  if (!categories.length) {
    categorySelect.innerHTML = '<option value="bottle">bottle — configuration required</option>';
    setWarning("No calibrated category is configured yet. Build a memory bank, calibrate a threshold, then create model_config.json.");
    return;
  }

  categories.forEach(item => {
    const option = document.createElement("option");
    option.value = item.name;
    option.textContent = item.ready ? item.name.replaceAll("_", " ") : `${item.name.replaceAll("_", " ")} — not ready`;
    categorySelect.appendChild(option);
  });
  validateSelectedCategory();
}

function validateSelectedCategory() {
  const current = categories.find(item => item.name === categorySelect.value);
  if (current && !current.ready) {
    setWarning("This category is configured but not demo-ready. Check the model artifact and calibrated threshold.");
  } else {
    setWarning("");
  }
}

function resetResult() {
  overlay.style.display = "none";
  emptyResult.classList.remove("hidden");
  resultState.className = "result-state idle";
  resultState.textContent = "Awaiting result";
  score.textContent = "—";
  threshold.textContent = "—";
  latency.textContent = "—";
  currentInspectionId = null;
  reviewActions.classList.add("hidden");
}

async function runInspection() {
  if (!selectedFile) return;

  loader.classList.remove("hidden");
  emptyResult.classList.add("hidden");
  overlay.style.display = "none";
  inspectButton.disabled = true;
  resultState.className = "result-state idle";
  resultState.textContent = "Inspecting";

  const form = new FormData();
  form.append("image", selectedFile);
  form.append("category", categorySelect.value);

  try {
    const response = await fetch("/api/inspect", { method: "POST", body: form });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Inspection failed.");

    currentInspectionId = data.inspection_id;
    overlay.src = `data:image/png;base64,${data.overlay_png_base64}`;
    overlay.style.display = "block";
    resultState.className = `result-state ${data.severity}`;
    resultState.textContent = data.decision;
    score.textContent = Number(data.score).toFixed(4);
    threshold.textContent = Number(data.threshold).toFixed(4);
    latency.textContent = `${Number(data.latency_ms).toFixed(1)} ms`;
    guidance.textContent = data.guidance;
    reviewActions.classList.remove("hidden");
    await refreshOperations();
  } catch (error) {
    resetResult();
    resultState.className = "result-state error";
    resultState.textContent = "Configuration required";
    guidance.textContent = error.message;
  } finally {
    loader.classList.add("hidden");
    inspectButton.disabled = !selectedFile;
  }
}

async function submitReview(action) {
  if (!currentInspectionId) return;
  const response = await fetch(`/api/inspections/${currentInspectionId}/review`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });
  const data = await response.json();
  if (!response.ok) {
    guidance.textContent = data.detail || "Could not save the operator decision.";
    return;
  }
  guidance.textContent = `Operator decision recorded: ${data.operator_decision}. Model evidence remains unchanged.`;
  await refreshOperations();
}

function badgeClass(value) {
  if (value === "ANOMALY" || value === "REJECT") return "danger";
  if (value === "NORMAL" || value === "ACCEPT") return "success";
  if (value === "ESCALATE") return "warning-badge";
  return "";
}

async function refreshOperations() {
  const [statsResponse, historyResponse] = await Promise.all([
    fetch("/api/stats"),
    fetch("/api/inspections?limit=12"),
  ]);
  if (!statsResponse.ok || !historyResponse.ok) return;

  const stats = await statsResponse.json();
  const history = await historyResponse.json();

  document.getElementById("statTotal").textContent = stats.total_inspections ?? 0;
  document.getElementById("statAnomalies").textContent = stats.model_anomalies ?? 0;
  document.getElementById("statReviewed").textContent = stats.reviewed_by_operator ?? 0;
  document.getElementById("statLatency").textContent =
    stats.average_latency_ms == null ? "—" : `${Number(stats.average_latency_ms).toFixed(1)} ms`;

  const rows = history.inspections || [];
  if (!rows.length) {
    historyRows.innerHTML = '<div class="history-empty">No inspections recorded yet.</div>';
    return;
  }

  historyRows.innerHTML = rows.map(row => {
    const created = new Date(row.created_at).toLocaleString();
    const human = row.operator_decision || "Pending";
    return `
      <div class="history-row">
        <span>${created}</span>
        <strong>${row.category.replaceAll("_", " ")}</strong>
        <span class="mini-badge ${badgeClass(row.model_decision)}">${row.model_decision}</span>
        <span class="mono">${Number(row.anomaly_score).toFixed(4)}</span>
        <span class="mini-badge ${badgeClass(human)}">${human}</span>
      </div>
    `;
  }).join("");
}

async function loadBenchmarks() {
  const response = await fetch("/api/benchmarks");
  if (!response.ok) return;
  const data = await response.json();
  const container = document.getElementById("benchmarkCards");
  const rows = data.benchmarks || [];
  if (!rows.length) {
    container.innerHTML = '<div class="history-empty">No verified benchmark artifacts found.</div>';
    return;
  }

  container.innerHTML = rows.map(row => {
    const name = row.category.replaceAll("_", " ");
    const auroc = row.auroc == null ? "—" : Number(row.auroc).toFixed(3);
    const ap = row.average_precision == null ? "—" : Number(row.average_precision).toFixed(3);
    const acc = row.accuracy == null ? "—" : `${(Number(row.accuracy) * 100).toFixed(1)}%`;
    const f1 = row.f1 == null ? "—" : Number(row.f1).toFixed(3);
    const baseline = row.baseline_auroc == null ? "—" : Number(row.baseline_auroc).toFixed(3);
    return `
      <article class="benchmark-card">
        <div class="benchmark-top">
          <div><span class="mini-label">${row.selected_method}</span><h3>${name}</h3></div>
          <span class="baseline-chip">Baseline AUROC ${baseline}</span>
        </div>
        <div class="benchmark-values four">
          <span><small>AUROC</small><strong>${auroc}</strong></span>
          <span><small>AP</small><strong>${ap}</strong></span>
          <span><small>Accuracy</small><strong>${acc}</strong></span>
          <span><small>F1</small><strong>${f1}</strong></span>
        </div>
        <p>False positive ${row.false_positive ?? "—"} · False negative ${row.false_negative ?? "—"}</p>
      </article>
    `;
  }).join("");
}

async function refreshSystemStatus() {
  const [healthResponse, readinessResponse, categoriesResponse] = await Promise.all([
    fetch("/api/health"),
    fetch("/api/readiness"),
    fetch("/api/categories"),
  ]);

  if (!healthResponse.ok || !readinessResponse.ok || !categoriesResponse.ok) {
    document.getElementById("globalStatusText").textContent = "System unavailable";
    document.getElementById("globalStatus").classList.add("status-error");
    return;
  }

  const health = await healthResponse.json();
  const readiness = await readinessResponse.json();
  const categoryData = await categoriesResponse.json();

  const isReady = readiness.status === "ready";
  document.getElementById("globalStatusText").textContent = isReady ? "System ready" : "System degraded";
  document.getElementById("globalStatus").classList.toggle("status-error", !isReady);
  document.getElementById("systemState").textContent = isReady ? "Ready for inspection" : "Degraded";
  document.getElementById("systemVersion").textContent = `VisionGuard AI v${health.version}`;
  document.getElementById("healthApi").textContent = health.status === "ok" ? "Healthy" : "Unavailable";
  document.getElementById("healthModels").textContent = `${health.ready_categories}/${health.configured_categories} ready`;

  const container = document.getElementById("modelRegistryCards");
  const rows = categoryData.categories || [];
  container.innerHTML = rows.map(row => {
    const displayName = row.name.replaceAll("_", " ");
    return `
      <article class="registry-card">
        <div class="registry-title">
          <div><span class="mini-label">${row.engine}</span><h3>${displayName}</h3></div>
          <span class="mini-badge ${row.ready ? "success" : "danger"}">${row.ready ? "READY" : "NOT READY"}</span>
        </div>
        <dl>
          <div><dt>Threshold</dt><dd>${row.threshold_configured ? "Calibrated" : "Missing"}</dd></div>
          <div><dt>Model artifact</dt><dd>${row.model_available ? "Available" : "Missing"}</dd></div>
          <div><dt>Source</dt><dd>${row.threshold_source}</dd></div>
        </dl>
      </article>
    `;
  }).join("");
}

dropzone.addEventListener("dragover", event => {
  event.preventDefault();
  dropzone.classList.add("dragover");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", event => {
  event.preventDefault();
  dropzone.classList.remove("dragover");
  setImage(event.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => setImage(fileInput.files[0]));
categorySelect.addEventListener("change", validateSelectedCategory);
inspectButton.addEventListener("click", runInspection);

document.querySelectorAll(".review-button").forEach(button => {
  button.addEventListener("click", () => submitReview(button.dataset.action));
});
refreshHistory.addEventListener("click", refreshOperations);
refreshSystem.addEventListener("click", refreshSystemStatus);

resetResult();
loadCategories().catch(() => setWarning("Could not load model configuration."));
refreshOperations().catch(() => {});
loadBenchmarks().catch(() => {});
refreshSystemStatus().catch(() => {});
