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

let selectedFile = null;
let categories = [];
let currentInspectionId = null;

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
    option.textContent = item.ready ? item.name : `${item.name} — not ready`;
    option.dataset.ready = item.ready;
    categorySelect.appendChild(option);
  });
  validateSelectedCategory();
}

function validateSelectedCategory() {
  const current = categories.find(item => item.name === categorySelect.value);
  if (current && !current.ready) {
    setWarning("This category is documented but not demo-ready yet. Check the model file and calibrated threshold.");
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

    if (!response.ok) {
      throw new Error(data.detail || "Inspection failed.");
    }

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

resetResult();
loadCategories().catch(() => setWarning("Could not load model configuration."));


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
        <strong>${row.category}</strong>
        <span class="mini-badge ${badgeClass(row.model_decision)}">${row.model_decision}</span>
        <span class="mono">${Number(row.anomaly_score).toFixed(4)}</span>
        <span class="mini-badge ${badgeClass(human)}">${human}</span>
      </div>
    `;
  }).join("");
}

document.querySelectorAll(".review-button").forEach(button => {
  button.addEventListener("click", () => submitReview(button.dataset.action));
});
refreshHistory.addEventListener("click", refreshOperations);
refreshOperations().catch(() => {});
