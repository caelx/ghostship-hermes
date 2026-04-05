const openButton = document.getElementById("open-terminal");
const closeButton = document.getElementById("close-terminal");
const tabsRoot = document.getElementById("terminal-tabs");
const blankHome = document.getElementById("blank-home");
const terminalStage = document.getElementById("terminal-stage");
const terminalPanes = document.getElementById("terminal-panes");
const terminalLoading = document.getElementById("terminal-loading");

const state = {
  activeTerminalId: null,
  sessions: [],
};

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || payload.error || `request failed: ${response.status}`);
  }
  return payload;
}

function currentSession() {
  return state.sessions.find((session) => session.id === state.activeTerminalId) || null;
}

function syncActiveId(payload) {
  const available = new Set(payload.sessions.map((session) => session.id));
  if (state.activeTerminalId && available.has(state.activeTerminalId)) {
    return;
  }
  state.activeTerminalId = payload.active_terminal_id || payload.sessions[0]?.id || null;
}

function renderTabs() {
  tabsRoot.innerHTML = "";

  state.sessions.forEach((session, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "rail-tab";
    button.title = session.label;
    button.dataset.label = session.label;
    button.setAttribute("aria-label", session.label);
    button.textContent = String(index + 1).padStart(2, "0");
    if (session.id === state.activeTerminalId) {
      button.classList.add("is-active");
    }
    button.addEventListener("click", () => {
      state.activeTerminalId = session.id;
      render();
    });
    tabsRoot.appendChild(button);
  });
}

function ensureFrame(session) {
  let pane = terminalPanes.querySelector(`[data-terminal-id="${session.id}"]`);
  if (!pane) {
    pane = document.createElement("section");
    pane.className = "terminal-pane";
    pane.dataset.terminalId = session.id;

    const frame = document.createElement("iframe");
    frame.className = "terminal-frame";
    frame.title = `tty-${session.id}`;
    frame.scrolling = "no";
    frame.setAttribute("sandbox", "allow-same-origin allow-scripts allow-forms allow-downloads");
    pane.appendChild(frame);
    terminalPanes.appendChild(pane);
  }

  const frame = pane.querySelector("iframe");
  if (session.ready && frame.dataset.src !== session.terminal_url) {
    frame.src = session.terminal_url;
    frame.dataset.src = session.terminal_url;
  }

  return pane;
}

function syncFrames() {
  const activeSession = currentSession();
  const sessionIds = new Set(state.sessions.map((session) => session.id));

  for (const pane of terminalPanes.querySelectorAll(".terminal-pane")) {
    if (!sessionIds.has(pane.dataset.terminalId)) {
      pane.remove();
    }
  }

  for (const session of state.sessions) {
    const pane = ensureFrame(session);
    pane.classList.toggle("is-active", session.id === state.activeTerminalId);
  }

  terminalPanes.classList.toggle("is-hidden", !activeSession);
}

function renderStage() {
  const session = currentSession();
  const hasSession = Boolean(session);

  blankHome.classList.toggle("is-hidden", hasSession);
  terminalStage.classList.toggle("is-hidden", !hasSession);
  closeButton.classList.toggle("is-hidden", !hasSession);
  closeButton.disabled = !hasSession;

  if (!hasSession) {
    terminalLoading.classList.add("is-hidden");
    terminalPanes.classList.add("is-hidden");
    return;
  }

  terminalLoading.classList.toggle("is-hidden", Boolean(session.ready));
  syncFrames();
}

function render() {
  renderTabs();
  renderStage();
}

function applyPayload(payload) {
  state.sessions = payload.sessions || [];
  syncActiveId(payload);
  render();
}

async function refreshStatus() {
  try {
    const payload = await requestJson("/api/status");
    applyPayload(payload);
  } catch (error) {
    console.error("Status refresh failed:", error);
  }
}

async function openTerminal() {
  openButton.disabled = true;
  try {
    const payload = await requestJson("/api/terminal/open", { method: "POST" });
    state.activeTerminalId = payload.active_terminal_id || null;
    applyPayload(payload);
  } catch (error) {
    console.error("Open terminal failed:", error);
  } finally {
    openButton.disabled = false;
  }
}

async function closeTerminal() {
  const session = currentSession();
  if (!session) return;

  closeButton.disabled = true;
  try {
    const payload = await requestJson(`/api/terminals/${session.id}/close`, { method: "POST" });
    state.activeTerminalId = payload.active_terminal_id || null;
    applyPayload(payload);
  } catch (error) {
    console.error("Close terminal failed:", error);
  } finally {
    closeButton.disabled = false;
  }
}

function startPolling() {
  const tick = async () => {
    await refreshStatus();
    window.setTimeout(tick, 500);
  };
  void tick();
}

openButton.addEventListener("click", () => void openTerminal());
closeButton.addEventListener("click", () => void closeTerminal());

window.addEventListener("DOMContentLoaded", () => {
  startPolling();
});
