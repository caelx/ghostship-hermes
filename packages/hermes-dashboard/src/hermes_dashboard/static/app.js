const homeButton = document.getElementById("home-button");
const openButton = document.getElementById("open-terminal");
const closeButton = document.getElementById("close-terminal");
const tabsRoot = document.getElementById("terminal-tabs");
const blankHome = document.getElementById("blank-home");
const terminalStage = document.getElementById("terminal-stage");
const terminalPanes = document.getElementById("terminal-panes");
const terminalLoading = document.getElementById("terminal-loading");
const runtimeFactsRoot = document.getElementById("runtime-facts");
const providerPillsRoot = document.getElementById("provider-pills");
const providerListRoot = document.getElementById("provider-list");
const profileListRoot = document.getElementById("profile-list");

const state = {
  activeTerminalId: null,
  environment: null,
  sessions: [],
  showHome: true,
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
  if (state.showHome) {
    return;
  }

  const available = new Set(payload.sessions.map((session) => session.id));
  if (state.activeTerminalId && available.has(state.activeTerminalId)) {
    return;
  }
  state.activeTerminalId = payload.active_terminal_id || payload.sessions[0]?.id || null;
}

function formatValue(value, fallback = "not set") {
  if (value === null || value === undefined || value === "") {
    return fallback;
  }
  return String(value);
}

function makePill(label, accent = false) {
  const pill = document.createElement("span");
  pill.className = "meta-pill";
  if (accent) {
    pill.classList.add("is-accent");
  }
  pill.textContent = label;
  return pill;
}

function renderHome() {
  const environment = state.environment || {};
  const profiles = (environment.profiles || []);
  renderProviderPills(environment, environment.endpoints || environment.providers || [], environment.sections || []);

  const homeRenderKey = JSON.stringify({
    environment,
    visibleSessionCount: visibleSessions().length,
  });
  if (state.homeRenderKey === homeRenderKey) {
    return;
  }
  state.homeRenderKey = homeRenderKey;
  homeCardsRoot.innerHTML = "";

  const layout = document.createElement("div");
  layout.className = "dashboard-layout";
  layout.append(
    renderOverviewPanel(environment, profiles, environment.endpoints || environment.providers || [], environment.sections || []),
    renderProfilesPanel(profiles),
  );

  homeCardsRoot.appendChild(layout);
}
function renderTabs() {
  homeButton.classList.toggle("is-active", state.showHome);
  tabsRoot.innerHTML = "";

  state.sessions.forEach((session, index) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "rail-tab";
    button.title = session.label;
    button.dataset.label = session.label;
    button.setAttribute("aria-label", session.label);
    button.textContent = String(index + 1).padStart(2, "0");
    if (!state.showHome && session.id === state.activeTerminalId) {
      button.classList.add("is-active");
    }
    button.addEventListener("click", () => {
      state.activeTerminalId = session.id;
      state.showHome = false;
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
    pane.classList.toggle("is-active", !state.showHome && session.id === state.activeTerminalId);
  }

  terminalPanes.classList.toggle("is-hidden", state.showHome || !activeSession);
}

function renderStage() {
  const session = state.showHome ? null : currentSession();
  const showHome = state.showHome || !session;

  blankHome.classList.toggle("is-hidden", !showHome);
  terminalStage.classList.toggle("is-hidden", showHome);
  closeButton.classList.toggle("is-hidden", showHome);
  closeButton.disabled = showHome;

  if (showHome) {
    terminalLoading.classList.add("is-hidden");
    terminalPanes.classList.add("is-hidden");
    return;
  }

  terminalLoading.classList.toggle("is-hidden", Boolean(session.ready));
  syncFrames();
}

function render() {
  renderHome();
  renderTabs();
  renderStage();
}

function applyPayload(payload) {
  state.sessions = payload.sessions || [];
  state.environment = payload.environment || null;

  if (!state.sessions.length) {
    state.activeTerminalId = null;
    state.showHome = true;
  } else {
    syncActiveId(payload);
  }

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
    state.showHome = false;
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
    if (!payload.sessions?.length) {
      state.showHome = true;
    }
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

homeButton.addEventListener("click", () => {
  state.showHome = true;
  render();
});
openButton.addEventListener("click", () => void openTerminal());
closeButton.addEventListener("click", () => void closeTerminal());

window.addEventListener("DOMContentLoaded", () => {
  render();
  startPolling();
});
