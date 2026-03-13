let currentExecutionId = null;

const executedByInput = document.getElementById("executedBy");
const csvFileInput = document.getElementById("csvFile");
const rebootEnabledInput = document.getElementById("rebootEnabled");

const validateBtn = document.getElementById("validateBtn");
const executeBtn = document.getElementById("executeBtn");
const refreshBtn = document.getElementById("refreshBtn");

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

    const doneCount = routers.filter(r => r.system_status_after === "done").length;
    progressText.textContent = `${doneCount} / ${routers.length}`;

    for (const router of routers) {
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${router.device_name ?? "-"}</td>
            <td>${router.ip_address ?? "-"}</td>
            <td>${router.old_location ?? "-"}</td>
            <td>${router.new_location ?? "-"}</td>
            <td>${router.device_type ?? "-"}</td>
            <td>${router.connection_status_before ?? "-"}</td>
            <td>${router.system_status_before ?? "-"}</td>
            <td>${router.system_status_after ?? "-"}</td>
            <td>${router.update_result ?? "-"}</td>
            <td>${router.reboot_result ?? "-"}</td>
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
    executeBtn.disabled = false;
    refreshBtn.disabled = false;
}

validateBtn.addEventListener("click", async () => {
    const file = csvFileInput.files[0];
    const executedBy = executedByInput.value.trim();
    const rebootEnabled = rebootEnabledInput.checked;

    if (!file) {
        setMessage("Please select a CSV file first.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);
    formData.append("executed_by", executedBy);
    formData.append("reboot_enabled", rebootEnabled ? "true" : "false");

    try {
        setStatus("Validating...");
        currentPhaseLabel.textContent = "Preparation / Validation";

        const response = await fetch("/validate", {
            method: "POST",
            body: formData
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

    try {
        setStatus("Executing...");
        currentPhaseLabel.textContent = "Execution";

        const response = await fetch("/execute", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                execution_id: currentExecutionId,
                reboot_enabled: rebootEnabledInput.checked
            })
        });

        const data = await response.json();

        if (!response.ok) {
            setMessage(data.error || "Execution failed.");
            setStatus("Error");
            return;
        }

        renderSummary(data.execution);
        renderRouters(data.routers);
        setMessage("Execution completed.");
        setStatus("Completed");
    } catch (error) {
        setMessage(`Unexpected error during execution: ${error}`);
        setStatus("Error");
    }
});

refreshBtn.addEventListener("click", async () => {
    if (!currentExecutionId) {
        setMessage("No execution available to refresh.");
        return;
    }

    try {
        setStatus("Refreshing...");
        currentPhaseLabel.textContent = "Refresh Status";

        await loadExecution(currentExecutionId);

        setMessage("Execution detail refreshed from database.");
        setStatus("Refreshed");
    } catch (error) {
        setMessage(`Unexpected error during refresh: ${error}`);
        setStatus("Error");
    }
});