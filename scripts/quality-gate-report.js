// Quality Gate Report - JavaScript Module

// Costanti per l'auto-refresh
const MAX_CHECKS = 3000; // 5 minutes at 100ms interval
const REPORT_DATA_URL = window.reportDataUrl || "report-data.json";

// Variabile globale per tracciare l'ultimo timestamp in millisecondi
let lastTimestampMs = null;
let checkCount = 0;
let qualityGateResults;

// Utility function to get the appropriate icon and color class
function getStatusVisuals(status) {
  if (status === "PASSED") {
    const icon = `<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 icon-pass" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><path d="M9 11l3 3L22 4"></path></svg>`;
    return {
      icon,
      statusTextClass: "text-lime-400",
      cardBorder: "card-border-pass",
      bg: "bg-black/50 hover:bg-black/70",
    };
  } else if (status === "SKIPPED") {
    const icon = `<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 icon-skipped" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`;
    return {
      icon,
      statusTextClass: "text-orange-400",
      cardBorder: "card-border-skipped",
      bg: "bg-black/50 hover:bg-black/70",
    };
  } else if (status === "PENDING") {
    const icon = `<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 text-gray-500 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M6 2h12v6a6 6 0 0 1-6 6 6 6 0 0 1-6-6V2Z"></path><path d="M6 22h12v-6a6 6 0 0 0-6-6 6 6 0 0 0-6 6v6Z"></path></svg>`;
    return {
      icon,
      statusTextClass: "text-gray-500",
      cardBorder: "border-2 border-gray-700",
      bg: "bg-black/30",
    };
  } else {
    const icon = `<svg xmlns="http://www.w3.org/2000/svg" class="w-6 h-6 icon-fail" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>`;
    return {
      icon,
      statusTextClass: "matrix-fail-text",
      cardBorder: "card-border-fail",
      bg: "bg-black/50 hover:bg-black/70",
    };
  }
}

// Toggle accordion function (Resa globale per essere chiamata dall'HTML)
window.toggleAccordion = function (id) {
  const accordion = document.getElementById(id);
  const icon = document.getElementById(id + "-icon");

  if (accordion.classList.contains("hidden")) {
    accordion.classList.remove("hidden");
    icon.classList.add("rotate-180");
  } else {
    accordion.classList.add("hidden");
    icon.classList.remove("rotate-180");
  }
};

// Copy details function (Resa globale per essere chiamata dall'HTML)
window.copyDetails = function (detailsId, button) {
  const text = document.getElementById(detailsId).textContent;
  const input = document.createElement("textarea");
  input.value = text;
  input.classList.add("hidden-textarea");
  document.body.appendChild(input);
  input.select();

  let success = false;
  try {
    success = document.execCommand("copy");
  } catch (err) {
    console.error("Copia fallita:", err);
  }

  document.body.removeChild(input);

  if (success) {
    const copyText = button.querySelector(".copy-text");
    const originalText = copyText.textContent;
    copyText.textContent = "COPIED!";
    setTimeout(() => {
      copyText.textContent = originalText;
    }, 1500);
  }
};

// Function to determine border color based on severity
function getSeverityBorderClass(status, severity) {
  // PENDING, SKIPPED, or no severity - use default status border
  if (
    status === "PENDING" ||
    status === "SKIPPED" ||
    !severity ||
    severity === "N/A"
  ) {
    return null; // Will use default from getStatusVisuals
  }

  // Check severity text for errors, warnings, or info
  const severityLower = severity.toLowerCase();

  // Red border if contains errors
  if (/\d+\s+errors?/i.test(severity)) {
    return "border-2 border-red-500 shadow-red-500/50";
  }

  // Yellow border if contains warnings
  if (/\d+\s+warnings?/i.test(severity)) {
    return "border-2 border-yellow-500 shadow-yellow-500/50";
  }

  // Blue border if contains info/notes/violations/files
  if (
    /\d+\s+(info|notes?|conventions?|refactors?|violations?|files?)/i.test(
      severity
    )
  ) {
    return "border-2 border-blue-500 shadow-blue-500/50";
  }

  // Default to status border
  return null;
}

// Function to create the HTML for a single standard
function createStandardItem(standard) {
  const { icon, statusTextClass, cardBorder, bg } = getStatusVisuals(
    standard.status
  );

  // Determine border based on severity (overrides status border if severity detected)
  const severityBorder = getSeverityBorderClass(
    standard.status,
    standard.severity
  );
  const finalBorder = severityBorder || cardBorder;

  const detailsId = `details-${Math.random().toString(36).substr(2, 9)}`;
  const accordionId = `accordion-${Math.random().toString(36).substr(2, 9)}`;

  let severityContent;
  let accordionSection = "";

  // Add accordion for details if available (show for all statuses except PENDING)
  if (
    standard.details &&
    standard.status !== "PENDING" &&
    standard.details.trim() !== ""
  ) {
    accordionSection = `
      <div class="mt-2 border-t border-lime-500/20 pt-2">
        <button
          onclick="toggleAccordion('${accordionId}')"
          class="w-full flex items-center justify-between text-xs text-lime-400 hover:text-lime-300 transition"
        >
          <span>📋 Show Output Details</span>
          <svg id="${accordionId}-icon" class="w-4 h-4 transform transition-transform" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <polyline points="6 9 12 15 18 9"></polyline>
          </svg>
        </button>
        <div id="${accordionId}" class="hidden mt-2 bg-black rounded p-3 max-h-64 overflow-y-auto matrix-pass-glow">
          <div class="flex justify-between items-center mb-2">
            <span class="text-xs text-lime-500 font-semibold">Command Output:</span>
            <button
              onclick="copyDetails('${detailsId}', this)"
              class="px-2 py-1 bg-lime-600 hover:bg-lime-500 text-black text-xs rounded flex items-center space-x-1 transition duration-150"
              title="Copy output"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
                <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
              </svg>
              <span class="copy-text">COPY</span>
            </button>
          </div>
          <pre id="${detailsId}" class="text-xs text-lime-300 font-mono whitespace-pre-wrap">${
      standard.details || "No output - check passed with no issues."
    }</pre>
        </div>
      </div>
    `;
  }

  if (standard.status === "FAILED") {
    // Color-code severity: errors in red, warnings in yellow, info/files/violations in blue
    let coloredSeverity = standard.severity
      .replace(/(\d+)\s+(errors?)/gi, '<span class="text-red-400">$1 $2</span>')
      .replace(
        /(\d+)\s+(warnings?)/gi,
        '<span class="text-yellow-400">$1 $2</span>'
      )
      .replace(
        /(\d+)\s+(info|notes?|conventions?|refactors?|violations?|files?)/gi,
        '<span class="text-blue-400">$1 $2</span>'
      );
    severityContent = `<p class="text-xs font-medium pt-1">${coloredSeverity}</p>`;
  } else if (standard.status === "SKIPPED") {
    severityContent = `<p class="text-xs text-orange-400/70 pt-1">${standard.severity}</p>`;
  } else if (standard.status === "PENDING") {
    severityContent = `<p class="text-xs pending-status-text pt-1">Waiting...</p>`;
  } else {
    // PASSED: color-code as well for consistency
    let coloredSeverity = standard.severity
      .replace(
        /(\d+)\s+(warnings?)/gi,
        '<span class="text-yellow-400">$1 $2</span>'
      )
      .replace(
        /(\d+)\s+(info|notes?|conventions?|refactors?|violations?|files?)/gi,
        '<span class="text-blue-400">$1 $2</span>'
      );
    severityContent = `<p class="text-xs text-lime-600/70 pt-1">${coloredSeverity}</p>`;
  }

  const pendingClass = standard.status === "PENDING" ? "pending-card" : "";
  const iconClass = standard.status === "PENDING" ? "pending-icon" : "";
  const matrixRain = standard.status === "PENDING" ? createMatrixRain() : "";

  return `
    <div class="p-4 rounded-md ${finalBorder} ${bg} ${pendingClass} shadow-lg transition duration-200" style="position: relative; overflow: hidden; min-height: 120px;">
      ${matrixRain}
      <div class="flex items-center" style="position: relative; z-index: 2;">
        <div class="mr-4 p-2 rounded-sm matrix-pass-glow ${iconClass}">
          ${icon}
        </div>
        <div class="flex-grow">
          <p class="text-lg font-semibold text-lime-300 ${
            standard.status === "PENDING" ? "pending-text" : ""
          }">${standard.name}</p>
          <p class="text-sm text-lime-500/70">${standard.role}</p>
        </div>
        <div class="text-right flex flex-col items-end">
          <span class="font-bold uppercase text-sm ${statusTextClass}">${
    standard.status
  }</span>
          ${severityContent}
        </div>
      </div>
      ${accordionSection}
      ${
        standard.status === "PENDING"
          ? '<div class="pending-progress"></div>'
          : ""
      }
    </div>
  `;
}

// Function to create matrix rain effect
function createMatrixRain() {
  const chars = "01234567890ABCDEFx§¶ßÇÐÑØæçðñø";
  let rainHtml = '<div class="matrix-rain-container">';

  for (let i = 0; i < 15; i++) {
    const char = chars[Math.floor(Math.random() * chars.length)];
    const left = Math.random() * 100;
    const duration = 1.5 + Math.random() * 2.5;
    const delay = Math.random() * 2;

    rainHtml += `<span class="matrix-char" style="left: ${left}%; animation-duration: ${duration}s; animation-delay: ${delay}s;">${char}</span>`;
  }

  rainHtml += "</div>";
  return rainHtml;
}

// Function to create the HTML for an entire section
function createSection(title, standards) {
  const itemsHtml = standards.map(createStandardItem).join("");

  return `
    <div class="bg-black p-6 rounded-md shadow-2xl matrix-pass-glow h-full flex flex-col">
      <h2 class="text-xl font-bold mb-6 text-lime-400 border-b border-lime-400/50 pb-3">${title}</h2>
      <div class="space-y-4 flex-grow">
        ${itemsHtml}
      </div>
    </div>
  `;
}

// Main rendering logic
function renderReport(data) {
  qualityGateResults = data;

  const statusBox = document.getElementById("overall-status-box");
  const statusText = document.getElementById("overall-status-text");
  const timestampDisplay = document.getElementById("timestamp-display");

  // Update timestamp display
  const date = new Date(data.timestamp);
  const timeString = date.toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  timestampDisplay.textContent = `[Log Scan ${timeString}]`;

  // Determine status styling
  let bgColor, textColor;
  if (data.overallStatus === "RUNNING" || data.overallStatus === "PENDING") {
    bgColor = "bg-yellow-900 matrix-pass-glow";
    textColor = "text-yellow-200";
    statusText.textContent = "[STATUS: RUNNING CHECKS...]";
  } else if (data.overallStatus === "PASSED") {
    bgColor = "status-pass matrix-pass-glow";
    textColor = "text-lime-200";
    statusText.textContent = `[STATUS: ${data.overallStatus}]`;
  } else {
    bgColor = "status-fail matrix-fail-glow";
    textColor = "text-red-300";
    statusText.textContent = `[STATUS: ${data.overallStatus}]`;
  }

  statusBox.className = `mt-6 inline-block px-8 py-3 rounded-md shadow-2xl transition duration-300 ${bgColor}`;
  statusText.className = `text-2xl font-bold uppercase tracking-widest ${textColor}`;

  const reportContainer = document.getElementById("report-container");

  const frontendSection = createSection(
    "1. :: FRONTEND MODULES [TYPESCRIPT]",
    data.frontend
  );
  const backendSection = createSection(
    "2. :: BACKEND MODULES [PYTHON]",
    data.backend
  );

  reportContainer.innerHTML = frontendSection + backendSection;
}

// Auto-refresh functionality
async function checkForUpdates() {
  checkCount++;

  if (!qualityGateResults) return;

  if (checkCount > MAX_CHECKS) {
    console.log("Auto-refresh stopped: max time exceeded");
    return;
  }

  try {
    const response = await fetch(REPORT_DATA_URL + "?_=" + Date.now(), {
      cache: "no-cache",
    });

    if (!response.ok) {
      console.warn(
        `Fetch of ${REPORT_DATA_URL} failed: ${response.status}. Retrying.`
      );
      return;
    }

    const newData = await response.json();

    // Use millisecond timestamp for precise change detection
    if (newData.timestampMs && newData.timestampMs !== lastTimestampMs) {
      console.log(
        `Update detected. Old: ${lastTimestampMs}, New: ${newData.timestampMs} (${newData.timestamp}). Updating DOM...`
      );
      console.log(
        "Frontend phases:",
        newData.frontend.map((p) => `${p.name}: ${p.status}`).join(", ")
      );
      console.log(
        "Backend phases:",
        newData.backend.map((p) => `${p.name}: ${p.status}`).join(", ")
      );
      console.log("Overall status:", newData.overallStatus);
      lastTimestampMs = newData.timestampMs;
      renderReport(newData);

      // Stop polling after receiving final status and waiting a bit more
      if (
        newData.overallStatus !== "RUNNING" &&
        newData.overallStatus !== "PENDING"
      ) {
        console.log("Final status received, will stop polling in 5 seconds...");
        setTimeout(() => {
          checkCount = MAX_CHECKS;
        }, 5000);
      }
    }
  } catch (error) {
    console.error("Error fetching or parsing JSON data:", error);
  }
}

// Initial bootstrap function
async function initReport() {
  console.log("Initializing report. Data URL:", REPORT_DATA_URL);

  try {
    const initialResponse = await fetch(REPORT_DATA_URL);
    if (!initialResponse.ok) {
      throw new Error(
        `Unable to load initial data from ${REPORT_DATA_URL}. Status: ${initialResponse.status}`
      );
    }
    qualityGateResults = await initialResponse.json();
    lastTimestampMs = qualityGateResults.timestampMs;

    console.log("Initial load:", {
      timestampMs: qualityGateResults.timestampMs,
      timestamp: qualityGateResults.timestamp,
      overallStatus: qualityGateResults.overallStatus,
      frontend: qualityGateResults.frontend
        .map((p) => `${p.name}: ${p.status}`)
        .join(", "),
      backend: qualityGateResults.backend
        .map((p) => `${p.name}: ${p.status}`)
        .join(", "),
    });

    renderReport(qualityGateResults);

    // Always start polling - it will stop after final status + 5 seconds
    console.log(
      "Auto-refresh enabled: checking every 0.1 seconds for live updates."
    );
    setInterval(checkForUpdates, 100);
  } catch (e) {
    console.error(
      "Fatal error initializing report. Page loaded via file:// protocol or HTTP server not active:",
      e
    );
    document.getElementById("overall-status-text").textContent =
      "[ERROR: SERVER NOT FOUND OR ACCESS BLOCKED]";
    document.getElementById("overall-status-box").className =
      "mt-6 inline-block px-8 py-3 rounded-md shadow-2xl bg-red-900 matrix-fail-glow";
  }
}

// Initialize on page load
window.onload = initReport;
