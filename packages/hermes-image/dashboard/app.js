const openButton = document.getElementById("open-terminal");
const closeButton = document.getElementById("close-terminal");
const tabsRoot = document.getElementById("terminal-tabs");
const tabCount = document.getElementById("tab-count");
const blankHome = document.getElementById("blank-home");
const terminalStage = document.getElementById("terminal-stage");
const activeLabel = document.getElementById("active-label");
const terminalPanes = document.getElementById("terminal-panes");
const terminalLoading = document.getElementById("terminal-loading");
const profileList = document.getElementById("profile-list");
const homePath = document.getElementById("home-path");
const profileRoot = document.getElementById("profile-root");
const defaultProfile = document.getElementById("default-profile");

const state = {
  activeTerminalId: null,
  home: "/home/hermes",
  managedHermesHome: "/home/hermes/.hermes",
  defaultProfile: "operations",
  profiles: [],
  sessions: [],
};

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
  tabCount.textContent = String(state.sessions.length);

  for (const session of state.sessions) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "terminal-tab";
    button.title = session.label;
    if (session.id === state.activeTerminalId) {
      button.classList.add("is-active");
      button.setAttribute("aria-current", "page");
    }
    button.textContent = session.label;
    button.addEventListener("click", () => {
      state.activeTerminalId = session.id;
      render();
    });
    tabsRoot.appendChild(button);
    if (session.id === state.activeTerminalId) {
      button.scrollIntoView({ block: "nearest" });
    }
  }
}

function renderProfiles() {
  profileList.innerHTML = "";
  for (const profile of state.profiles) {
    const item = document.createElement("article");
    item.className = "profile-card";
    const defaultBadge = profile.is_default ? `<span class="profile-badge">default</span>` : "";
    item.innerHTML = `
      <div class="profile-head">
        <strong>${profile.name}</strong>
        ${defaultBadge}
      </div>
      <code>${profile.service}</code>
      <p>${profile.path}</p>
    `;
    profileList.appendChild(item);
  }
}

function ensureFrame(session) {
  let pane = terminalPanes.querySelector(`[data-terminal-id="${session.id}"]`);
  if (!pane) {
    pane = document.createElement("section");
    pane.className = "terminal-pane";
    pane.dataset.terminalId = session.id;

    const frame = document.createElement("iframe");
    frame.className = "terminal-frame";
    frame.title = `ghostship-hermes terminal ${session.id}`;
    frame.loading = "lazy";
    frame.referrerPolicy = "same-origin";
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
  closeButton.disabled = !hasSession;

  if (!hasSession) {
    activeLabel.textContent = "No terminal selected";
    terminalLoading.classList.add("is-hidden");
    terminalPanes.classList.add("is-hidden");
    return;
  }

  activeLabel.textContent = session.label;
  terminalLoading.classList.toggle("is-hidden", Boolean(session.ready));
  syncFrames();
}

function render() {
  renderTabs();
  renderProfiles();
  renderStage();
}

function applyPayload(payload) {
  state.home = payload.home || "/home/hermes";
  state.managedHermesHome = payload.managed_hermes_home || "/home/hermes/.hermes";
  state.defaultProfile = payload.default_profile || "operations";
  state.profiles = payload.profiles || [];
  state.sessions = payload.sessions || [];

  homePath.textContent = state.home;
  profileRoot.textContent = `${state.managedHermesHome}/profiles`;
  defaultProfile.textContent = state.defaultProfile;

  syncActiveId(payload);
  render();
}

async function refreshStatus() {
  try {
    const payload = await requestJson("/api/status");
    applyPayload(payload);
  } catch (error) {
    console.error(error);
  }
}

async function openTerminal() {
  openButton.disabled = true;
  try {
    const payload = await requestJson("/api/terminal/open", { method: "POST" });
    state.activeTerminalId = payload.active_terminal_id || null;
    applyPayload(payload);
  } catch (error) {
    console.error(error);
  } finally {
    openButton.disabled = false;
  }
}

async function closeTerminal() {
  const session = currentSession();
  if (!session) {
    return;
  }

  closeButton.disabled = true;
  try {
    const payload = await requestJson(`/api/terminals/${session.id}/close`, { method: "POST" });
    state.activeTerminalId = payload.active_terminal_id || null;
    applyPayload(payload);
  } catch (error) {
    console.error(error);
  } finally {
    closeButton.disabled = false;
  }
}

function startPolling() {
  const tick = async () => {
    await refreshStatus();
    window.setTimeout(tick, 400);
  };
  void tick();
}

openButton.addEventListener("click", () => {
  void openTerminal();
});

closeButton.addEventListener("click", () => {
  void closeTerminal();
});

window.addEventListener("DOMContentLoaded", () => {
  startPolling();
});
