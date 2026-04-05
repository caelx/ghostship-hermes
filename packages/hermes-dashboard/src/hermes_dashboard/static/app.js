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
  const providers = environment.providers || [];
  const profiles = environment.profiles || [];

  providerPillsRoot.innerHTML = "";
  if (providers.length) {
    providers.forEach((provider) => {
      providerPillsRoot.appendChild(makePill(provider.name, provider.configured));
    });
  } else {
    providerPillsRoot.appendChild(makePill("no provider"));
  }

  runtimeFactsRoot.innerHTML = "";
  const facts = [
    ["Host", environment.host],
    ["Dashboard", environment.dashboard_bind],
    ["Home", environment.home],
    ["Hermes", environment.managed_hermes_home],
    ["Shell root", environment.terminal_cwd],
    ["Default profile", environment.default_profile],
    ["Root model", environment.model],
    ["Live sessions", String(state.sessions.length)],
  ];

  facts.forEach(([label, value]) => {
    const wrapper = document.createElement("div");
    wrapper.className = "fact-item";

    const term = document.createElement("dt");
    term.textContent = label;

    const detail = document.createElement("dd");
    detail.textContent = formatValue(value);

    wrapper.append(term, detail);
    runtimeFactsRoot.appendChild(wrapper);
  });

  providerListRoot.innerHTML = "";
  if (!providers.length) {
    const empty = document.createElement("p");
    empty.className = "empty-line";
    empty.textContent = "No provider metadata detected.";
    providerListRoot.appendChild(empty);
  } else {
    providers.forEach((provider) => {
      const card = document.createElement("article");
      card.className = "provider-card";

      const top = document.createElement("div");
      top.className = "card-topline";

      const name = document.createElement("strong");
      name.className = "card-title";
      name.textContent = provider.name;

      const status = makePill(provider.configured ? "configured" : "incomplete", provider.configured);
      top.append(name, status);

      const grid = document.createElement("div");
      grid.className = "detail-grid";
      [
        ["Base URL", provider.base_url],
        ["API key", provider.has_api_key ? "present" : "missing"],
        ["Referer", provider.has_referer ? "present" : "missing"],
        ["Title", provider.title],
      ].forEach(([label, value]) => {
        const item = document.createElement("div");
        item.className = "detail-item";

        const key = document.createElement("span");
        key.className = "detail-key";
        key.textContent = label;

        const detail = document.createElement("span");
        detail.className = "detail-value";
        detail.textContent = formatValue(value);

        item.append(key, detail);
        grid.appendChild(item);
      });

      card.append(top, grid);
      providerListRoot.appendChild(card);
    });
  }

  profileListRoot.innerHTML = "";
  profiles.forEach((profile) => {
    const card = document.createElement("article");
    card.className = "profile-card";

    const top = document.createElement("div");
    top.className = "card-topline";

    const name = document.createElement("strong");
    name.className = "card-title";
    name.textContent = profile.name;

    const flags = document.createElement("div");
    flags.className = "meta-row";
    flags.appendChild(makePill(profile.is_default ? "default" : "profile", profile.is_default));
    flags.appendChild(makePill(formatValue(profile.provider, "provider unknown")));
    flags.appendChild(makePill(formatValue(profile.model, "model unset")));
    top.append(name, flags);

    const grid = document.createElement("div");
    grid.className = "detail-grid";
    [
      ["Service", profile.service],
      ["Path", profile.path],
      ["Config", profile.has_config ? "present" : "missing"],
      ["Env", profile.has_env ? "present" : "missing"],
    ].forEach(([label, value]) => {
      const item = document.createElement("div");
      item.className = "detail-item";

      const key = document.createElement("span");
      key.className = "detail-key";
      key.textContent = label;

      const detail = document.createElement("span");
      detail.className = "detail-value";
      detail.textContent = formatValue(value);

      item.append(key, detail);
      grid.appendChild(item);
    });

    card.append(top, grid);
    profileListRoot.append(card);
  });
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
