const openButton = document.getElementById("open-terminal");
const closeButton = document.getElementById("close-terminal");
const statusNode = document.getElementById("terminal-status");
const workspaceNode = document.getElementById("terminal-workspace");
const routeNode = document.getElementById("terminal-route");
const frame = document.getElementById("terminal-frame");

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.error || `request failed: ${response.status}`);
  }

  return payload;
}

function renderStatus(payload) {
  const running = Boolean(payload.running);
  const terminalUrl = payload.terminal_url || "/terminal";

  statusNode.textContent = running ? "Running" : "Stopped";
  workspaceNode.textContent = payload.workspace || "/workspace";
  routeNode.textContent = terminalUrl;
  openButton.disabled = running;
  closeButton.disabled = !running;

  if (running) {
    if (frame.dataset.src !== terminalUrl) {
      frame.src = terminalUrl;
      frame.dataset.src = terminalUrl;
    }
  } else {
    frame.removeAttribute("src");
    frame.dataset.src = "";
  }
}

async function refreshStatus() {
  try {
    const payload = await requestJson("/api/status");
    renderStatus(payload);
  } catch (error) {
    statusNode.textContent = error.message;
  }
}

openButton.addEventListener("click", async () => {
  statusNode.textContent = "Starting";
  try {
    const payload = await requestJson("/api/terminal/open", { method: "POST" });
    renderStatus(payload);
  } catch (error) {
    statusNode.textContent = error.message;
  }
});

closeButton.addEventListener("click", async () => {
  statusNode.textContent = "Stopping";
  try {
    const payload = await requestJson("/api/terminal/close", { method: "POST" });
    renderStatus(payload);
  } catch (error) {
    statusNode.textContent = error.message;
  }
});

refreshStatus();
setInterval(refreshStatus, 5000);
