const openButton = document.getElementById("open-terminal");
const closeButton = document.getElementById("close-terminal");
const tabsRoot = document.getElementById("terminal-tabs");
const tabCount = document.getElementById("tab-count");
const blankHome = document.getElementById("blank-home");
const terminalStage = document.getElementById("terminal-stage");
const activeLabel = document.getElementById("active-label");
const terminalCwd = document.getElementById("terminal-cwd");
const managedHermesHome = document.getElementById("managed-hermes-home");
const popoutLink = document.getElementById("popout-link");
const frame = document.getElementById("terminal-frame");
const profileList = document.getElementById("profile-list");
const terminalLoading = document.getElementById("terminal-loading");

const state = {
  sessions: [],
  activeTerminalId: null,
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
    if (session.id === state.activeTerminalId) {
      button.classList.add("is-active");
      button.setAttribute("aria-current", "page");
    }
    button.innerHTML = `
      <span class="terminal-tab-title">${session.label}</span>
      <span class="terminal-tab-meta">${session.cwd}</span>
    `;
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

function renderProfiles(payload) {
  profileList.innerHTML = "";
  const profiles = payload.profiles || [];
  if (profiles.length === 0) {
    const empty = document.createElement("p");
    empty.className = "profile-empty";
    empty.textContent = "No Hermes profiles have been created yet.";
    profileList.appendChild(empty);
    return;
  }

  for (const profile of profiles) {
    const item = document.createElement("article");
    item.className = "profile-card";
    const commandHint = profile.name === "default" ? "hermes chat" : `hermes -p ${profile.name} chat`;
    item.innerHTML = `
      <div class="profile-card-header">
        <strong>${profile.name}</strong>
        <code>${commandHint}</code>
      </div>
      <p>${profile.path}</p>
    `;
    profileList.appendChild(item);
  }
}

function renderStage() {
  const session = currentSession();
  const hasSession = Boolean(session);

  blankHome.classList.toggle("is-hidden", hasSession);
  terminalStage.classList.toggle("is-hidden", !hasSession);
  closeButton.disabled = !hasSession;

  if (!hasSession) {
    frame.removeAttribute("src");
    frame.dataset.src = "";
    activeLabel.textContent = "Terminal";
    popoutLink.href = "#";
    terminalLoading.classList.add("is-hidden");
    return;
  }

  activeLabel.textContent = session.label;
  popoutLink.href = session.terminal_url;
  terminalLoading.classList.toggle("is-hidden", Boolean(session.ready));
  if (!session.ready) {
    frame.removeAttribute("src");
    frame.dataset.src = "";
    return;
  }

  if (frame.dataset.src !== session.terminal_url) {
    frame.src = session.terminal_url;
    frame.dataset.src = session.terminal_url;
  }
}

function render() {
  renderTabs();
  renderStage();
}

function applyPayload(payload) {
  state.sessions = payload.sessions || [];
  terminalCwd.textContent = payload.terminal_cwd || "/home/hermes";
  managedHermesHome.textContent = payload.managed_hermes_home || "/home/hermes/.hermes";
  renderProfiles(payload);
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

openButton.addEventListener("click", async () => {
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
});

closeButton.addEventListener("click", async () => {
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
});

window.addEventListener("DOMContentLoaded", async () => {
  await refreshStatus();
  window.setInterval(refreshStatus, 1000);
});
