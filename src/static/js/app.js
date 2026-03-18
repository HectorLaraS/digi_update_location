let currentExecutionId = null;
let pollingIntervalId = null;

const digiUserInput = document.getElementById("digiUser");
const digiPasswordInput = document.getElementById("digiPassword");
const executedByInput = document.getElementById("executedBy");
const csvFileInput = document.getElementById("csvFile");
const rebootEnabledInput = document.getElementById("rebootEnabled");

const validateBtn = document.getElementById("validateBtn");
const executeBtn = document.getElementById("executeBtn");
const refreshBtn = document.getElementById("refreshBtn");
const continueBtn = document.getElementById("continueBtn");
const stopBtn = document.getElementById("stopBtn");

const appStatus = document.getElementById("app-status");
const executionIdLabel = document.getElementById("executionId");
const currentPhaseLabel = document.getElementById("currentPhase");
const progressText = document.getElementById("progressText");
const messagesBox = document.getElementById("messagesBox");
const tableBody = document.getElementById("routersTableBody");

const totalRows = document.getElementById("totalRows");
const readyCount = document.getElementById("readyCount");
const notFoundCount = document.getElementById("notFoundCount");
const disconnectedCount = document.getElementById("disconnectedCount");
const updatedCount = document.getElementById("updatedCount");
const rebootedCount = document.getElementById("rebootedCount");
const failedCount = document.getElementById("failedCount");
const executionStatus = document.getElementById("executionStatus");

function setStatus(text) {
  appStatus.textContent = text;
}

function setMessage(text) {
  messagesBox.textContent = text || "No messages yet.";
}

function setPausedControls(isPaused) {
  continueBtn.disabled = !isPaused;
  stopBtn.disabled = !isPaused;
  executeBtn.disabled = isPaused || !currentExecutionId;
}

function setRunningControls(isRunning) {
  validateBtn.disabled = isRunning;
  executeBtn.disabled = isRunning || !currentExecutionId;
  continueBtn.disabled = true;
  stopBtn.disabled = !isRunning;
  refreshBtn.disabled = false;
}

function setIdleControls() {
  validateBtn.disabled = false;
  executeBtn.disabled = !currentExecutionId;
  continueBtn.disabled = true;
  stopBtn.disabled = true;
  refreshBtn.disabled = !currentExecutionId;
}

function renderSummary(execution) {
  if (!execution) {
    totalRows.textContent = "0";
    readyCount.textContent = "0";
    notFoundCount.textContent = "0";
    disconnectedCount.textContent = "0";
    updatedCount.textContent = "0";
    rebootedCount.textContent = "0";
    failedCount.textContent = "0";
    executionStatus.textContent = "-";
    setPausedControls(false);
    return;
  }

  totalRows.textContent = execution.total_rows ?? 0;
  readyCount.textContent = execution.ready_count ?? 0;
  notFoundCount.textContent = execution.not_found_count ?? 0;
  disconnectedCount.textContent = execution.disconnected_count ?? 0;
  updatedCount.textContent = execution.updated_count ?? 0;
  rebootedCount.textContent = execution.rebooted_count ?? 0;
  failedCount.textContent = execution.failed_count ?? 0;
  executionStatus.textContent = execution.execution_status ?? "-";

  if (execution.execution_status === "paused") {
    setPausedControls(true);
  }
}

function renderStatusBadge(value, kind = "status") {
  const rawValue = value ?? "-";
  const safeClassValue = String(rawValue).toLowerCase().replaceAll("_", "-");
  return `<span class="table-badge ${kind}-badge ${kind}-${safeClassValue}">${rawValue}</span>`;
}

function renderRouters(routers) {
  tableBody.innerHTML = "";

  if (!routers || routers.length === 0) {
    tableBody.innerHTML = `
      <tr>
        <td colspan="11" class="empty-row">No data available.</td>
      </tr>
    `;
    progressText.textContent = "0 / 0";
    return;
  }

  const completedCount = routers.filter(
    (router) =>
      router.system_status_after === "done" ||
      router.system_status_after === "updated_no_reboot"
  ).length;

  progressText.textContent = `${completedCount} / ${routers.length}`;

  for (const router of routers) {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td>${router.device_name ?? "-"}</td>
      <td>${router.ip_address ?? "-"}</td>
      <td>${router.old_location ?? "-"}</td>
      <td>${router.new_location ?? "-"}</td>
      <td>${router.device_type ?? "-"}</td>
      <td>${renderStatusBadge(router.connection_status_before, "connection")}</td>
      <td>${renderStatusBadge(router.system_status_before, "status")}</td>
      <td>${renderStatusBadge(router.system_status_after, "status")}</td>
      <td>${renderStatusBadge(router.update_result, "result")}</td>
      <td>${renderStatusBadge(router.reboot_result, "result")}</td>
      <td>${router.notes ?? "-"}</td>
    `;
    tableBody.appendChild(row);
  }
}

async function loadExecution(executionId) {
  const response = await fetch(`/execution/${executionId}`);
  const data = await response.json();

  renderSummary(data.execution);
  renderRouters(data.routers);

  currentExecutionId = data.execution?.execution_id || executionId;
  executionIdLabel.textContent = currentExecutionId || "-";
  refreshBtn.disabled = false;
}

function validateCredentialPair(digiUser, digiPassword) {
  if ((digiUser && !digiPassword) || (!digiUser && digiPassword)) {
    setMessage("Please provide both Digi user/email and Digi password, or leave both empty.");
    return false;
  }
  return true;
}

async function pollExecutionStatus() {
  if (!currentExecutionId) {
    stopPolling();
    return;
  }

  try {
    const [jobResponse, executionResponse] = await Promise.all([
      fetch(`/execution/${currentExecutionId}/job-status`),
      fetch(`/execution/${currentExecutionId}`),
    ]);

    const executionData = await executionResponse.json();
    renderSummary(executionData.execution);
    renderRouters(executionData.routers);

    if (!jobResponse.ok) {
      return;
    }

    const jobData = await jobResponse.json();

    if (jobData.status === "running") {
      setStatus("Running");
      currentPhaseLabel.textContent = "Execution Running";
      setRunningControls(true);
      if (jobData.message) {
        setMessage(jobData.message);
      }
      return;
    }

    if (jobData.status === "paused") {
      setStatus("Paused");
      currentPhaseLabel.textContent = "Paused";
      setPausedControls(true);
      setMessage(
        jobData.message ||
          `Execution paused. Router ${jobData.paused_router_ip || "-"} did not come back online.`
      );
      stopPolling();
      return;
    }

    if (jobData.status === "completed") {
      setStatus("Completed");
      currentPhaseLabel.textContent = "Execution Completed";
      setMessage(jobData.message || "Execution completed successfully.");
      setIdleControls();
      stopPolling();
      return;
    }

    if (jobData.status === "failed") {
      setStatus("Failed");
      currentPhaseLabel.textContent = "Execution Failed";
      setMessage(jobData.message || "Execution failed.");
      setIdleControls();
      stopPolling();
      return;
    }

    if (jobData.status === "cancelled" || jobData.status === "cancel_requested") {
      setStatus("Cancelled");
      currentPhaseLabel.textContent = "Cancelled";
      setMessage(jobData.message || "Execution was cancelled.");
      setIdleControls();
      stopPolling();
    }
  } catch (error) {
    setMessage(`Unexpected polling error: ${error}`);
    setStatus("Error");
    stopPolling();
  }
}

function startPolling() {
  stopPolling();
  pollingIntervalId = window.setInterval(pollExecutionStatus, 3000);
}

function stopPolling() {
  if (pollingIntervalId !== null) {
    window.clearInterval(pollingIntervalId);
    pollingIntervalId = null;
  }
}

validateBtn.addEventListener("click", async () => {
  const file = csvFileInput.files[0];
  const executedBy = executedByInput.value.trim();
  const rebootEnabled = rebootEnabledInput.checked;
  const digiUser = digiUserInput.value.trim();
  const digiPassword = digiPasswordInput.value;

  if (!file) {
    setMessage("Please select a CSV file first.");
    return;
  }

  if (!validateCredentialPair(digiUser, digiPassword)) {
    return;
  }

  const formData = new FormData();
  formData.append("file", file);
  formData.append("executed_by", executedBy);
  formData.append("reboot_enabled", rebootEnabled ? "true" : "false");
  formData.append("digi_user", digiUser);
  formData.append("digi_pass", digiPassword);

  try {
    setStatus("Validating...");
    currentPhaseLabel.textContent = "Preparation / Validation";
    setPausedControls(false);
    stopPolling();

    const response = await fetch("/validate", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();

    if (!response.ok) {
      setMessage(data.error || "Validation failed.");
      setStatus("Error");
      return;
    }

    currentExecutionId = data.execution_id;
    executionIdLabel.textContent = currentExecutionId;
    executeBtn.disabled = false;
    refreshBtn.disabled = false;

    renderSummary(data.execution);
    renderRouters(data.routers);

    const messages = [];
    if (data.validation_errors && data.validation_errors.length > 0) {
      messages.push("Validation Errors:");
      messages.push(...data.validation_errors);
    } else {
      messages.push("Validation completed successfully.");
    }

    setMessage(messages.join("\n"));
    setStatus("Validated");
    setIdleControls();
  } catch (error) {
    setMessage(`Unexpected error during validation: ${error}`);
    setStatus("Error");
  }
});

executeBtn.addEventListener("click", async () => {
  if (!currentExecutionId) {
    setMessage("No execution available. Validate first.");
    return;
  }

  const digiUser = digiUserInput.value.trim();
  const digiPassword = digiPasswordInput.value;

  if (!validateCredentialPair(digiUser, digiPassword)) {
    return;
  }

  try {
    setStatus("Starting...");
    currentPhaseLabel.textContent = "Execution Starting";
    setRunningControls(true);

    const response = await fetch("/execute", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        execution_id: currentExecutionId,
        reboot_enabled: rebootEnabledInput.checked,
        digi_user: digiUser,
        digi_pass: digiPassword,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      setMessage(data.error || "Execution failed to start.");
      setStatus("Error");
      setIdleControls();
      return;
    }

    renderSummary(data.execution);
    renderRouters(data.routers);
    setMessage(data.message || "Execution started in background.");
    setStatus("Running");
    currentPhaseLabel.textContent = "Execution Running";
    startPolling();
  } catch (error) {
    setMessage(`Unexpected error during execution start: ${error}`);
    setStatus("Error");
    setIdleControls();
  }
});

continueBtn.addEventListener("click", async () => {
  if (!currentExecutionId) {
    setMessage("No paused execution available.");
    return;
  }

  const digiUser = digiUserInput.value.trim();
  const digiPassword = digiPasswordInput.value;

  if (!validateCredentialPair(digiUser, digiPassword)) {
    return;
  }

  try {
    setStatus("Continuing...");
    currentPhaseLabel.textContent = "Continue Execution";
    setRunningControls(true);

    const response = await fetch(`/execution/${currentExecutionId}/continue`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        reboot_enabled: rebootEnabledInput.checked,
        digi_user: digiUser,
        digi_pass: digiPassword,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      setMessage(data.error || "Continue execution failed.");
      setStatus("Error");
      setPausedControls(true);
      return;
    }

    renderSummary(data.execution);
    renderRouters(data.routers);
    setMessage(data.message || "Execution continue started in background.");
    setStatus("Running");
    currentPhaseLabel.textContent = "Execution Running";
    startPolling();
  } catch (error) {
    setMessage(`Unexpected error during continue execution: ${error}`);
    setStatus("Error");
    setPausedControls(true);
  }
});

stopBtn.addEventListener("click", async () => {
  if (!currentExecutionId) {
    setMessage("No paused execution available.");
    return;
  }

  try {
    setStatus("Stopping...");
    currentPhaseLabel.textContent = "Stop Execution";

    const response = await fetch(`/execution/${currentExecutionId}/stop`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
    });

    const data = await response.json();

    if (!response.ok) {
      setMessage(data.error || "Stop execution failed.");
      setStatus("Error");
      return;
    }

    renderSummary(data.execution);
    renderRouters(data.routers);
    setMessage(data.message || "Execution was cancelled.");
    setStatus("Cancelled");
    currentPhaseLabel.textContent = "Cancelled";
    setIdleControls();
    stopPolling();
  } catch (error) {
    setMessage(`Unexpected error during stop execution: ${error}`);
    setStatus("Error");
  }
});

refreshBtn.addEventListener("click", async () => {
  if (!currentExecutionId) {
    setMessage("No execution available to refresh.");
    return;
  }

  const digiUser = digiUserInput.value.trim();
  const digiPassword = digiPasswordInput.value;

  if (!validateCredentialPair(digiUser, digiPassword)) {
    return;
  }

  try {
    setStatus("Refreshing...");
    currentPhaseLabel.textContent = "Refresh Status";

    const response = await fetch(`/execution/${currentExecutionId}/refresh`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        digi_user: digiUser,
        digi_pass: digiPassword,
      }),
    });

    const data = await response.json();

    if (!response.ok) {
      setMessage(data.error || "Refresh failed.");
      setStatus("Error");
      return;
    }

    renderSummary(data.execution);
    renderRouters(data.routers);
    setMessage("Execution detail refreshed from Digi.");
    setStatus("Refreshed");
  } catch (error) {
    setMessage(`Unexpected error during refresh: ${error}`);
    setStatus("Error");
  }
});