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

let selectedFile = null;
let categories = [];

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

    overlay.src = `data:image/png;base64,${data.overlay_png_base64}`;
    overlay.style.display = "block";
    resultState.className = `result-state ${data.severity}`;
    resultState.textContent = data.decision;
    score.textContent = Number(data.score).toFixed(4);
    threshold.textContent = Number(data.threshold).toFixed(4);
    latency.textContent = `${Number(data.latency_ms).toFixed(1)} ms`;
    guidance.textContent = data.guidance;
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
