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
const agentDetailsRoot = document.getElementById("agent-details");

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
  const agent = environment.agent || {};

  providerPillsRoot.innerHTML = "";
  if (providers.length) {
    providers.forEach((provider) => {
      const routerReady = provider.router ? provider.router.ready : provider.configured;
      providerPillsRoot.appendChild(makePill(provider.name, routerReady));
    });
  } else {
    providerPillsRoot.appendChild(makePill("no endpoint"));
  }

  runtimeFactsRoot.innerHTML = "";
  const facts = [
    ["Host", environment.host],
    ["Dashboard", environment.dashboard_bind],
    ["Home", environment.home],
    ["Hermes", environment.managed_hermes_home],
    ["Shell root", environment.terminal_cwd],
    ["Gateway service", environment.gateway_service],
    ["Primary provider", environment.model_provider],
    ["Primary endpoint", environment.base_url],
    ["Primary model", environment.model],
    ["Fallback provider", environment.fallback_provider],
    ["Fallback endpoint", environment.fallback_base_url],
    ["Fallback model", environment.fallback_model],
    ["Disabled models", environment.router_disabled_models],
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
    empty.textContent = "No endpoint metadata detected.";
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

      const statusLabel = provider.router
        ? (provider.router.ready ? "router ready" : "router degraded")
        : (provider.configured ? "configured" : "incomplete");
      const status = makePill(statusLabel, provider.router ? provider.router.ready : provider.configured);
      top.append(name, status);

      const grid = document.createElement("div");
      grid.className = "detail-grid";
      [
        ["Kind", provider.kind],
        ["Base URL", provider.base_url],
        ["Auth", provider.auth_source ? `present via ${provider.auth_source}` : "not detected"],
        ["Runtime", (provider.models || []).length ? "managed agent" : "inactive"],
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

      if (provider.router) {
        const routerWrap = document.createElement("section");
        routerWrap.className = "provider-models";

        const routerLabel = document.createElement("span");
        routerLabel.className = "subsection-label";
        routerLabel.textContent = "Router aliases";
        routerWrap.appendChild(routerLabel);

        const routerMeta = document.createElement("div");
        routerMeta.className = "meta-row";
        routerMeta.appendChild(makePill(provider.router.ready ? "ready" : "degraded", provider.router.ready));
        if (provider.router.detail) {
          routerMeta.appendChild(makePill(provider.router.detail));
        }
        routerWrap.appendChild(routerMeta);

        const aliasCards = document.createElement("div");
        aliasCards.className = "model-subcards";
        (provider.router.aliases || []).forEach((alias) => {
          const aliasCard = document.createElement("article");
          aliasCard.className = "model-subcard";

          const aliasTop = document.createElement("div");
          aliasTop.className = "card-topline";

          const aliasName = document.createElement("strong");
          aliasName.className = "card-title model-title";
          aliasName.textContent = alias.name;

          const aliasFlags = document.createElement("div");
          aliasFlags.className = "meta-row";
          aliasFlags.appendChild(makePill(`${alias.candidate_count || 0} candidates`, (alias.candidate_count || 0) > 0));
          aliasTop.append(aliasName, aliasFlags);
          aliasCard.appendChild(aliasTop);

          if (alias.description) {
            const aliasDescription = document.createElement("p");
            aliasDescription.className = "empty-line";
            aliasDescription.textContent = alias.description;
            aliasCard.appendChild(aliasDescription);
          }

          const candidateRow = document.createElement("div");
          candidateRow.className = "meta-row";
          const candidates = alias.candidates || [];
          if (candidates.length) {
            candidates.slice(0, 4).forEach((candidate) => {
              candidateRow.appendChild(makePill(`${candidate.provider_name}:${candidate.backend_model}`));
            });
          } else {
            candidateRow.appendChild(makePill("no candidates"));
          }
          aliasCard.appendChild(candidateRow);
          aliasCards.appendChild(aliasCard);
        });
        routerWrap.appendChild(aliasCards);
        card.appendChild(routerWrap);

        const providerHealth = document.createElement("section");
        providerHealth.className = "provider-models";

        const healthLabel = document.createElement("span");
        healthLabel.className = "subsection-label";
        healthLabel.textContent = "Provider health";
        providerHealth.appendChild(healthLabel);

        const healthRow = document.createElement("div");
        healthRow.className = "meta-row";
        (provider.router.providers || []).forEach((item) => {
          healthRow.appendChild(makePill(item.enabled ? item.provider_name : `${item.provider_name} disabled`, item.enabled));
        });
        providerHealth.appendChild(healthRow);
        card.appendChild(providerHealth);
      }

      const models = provider.models || [];
      if (models.length) {
        const modelsWrap = document.createElement("section");
        modelsWrap.className = "provider-models";

        const label = document.createElement("span");
        label.className = "subsection-label";
        label.textContent = "Configured models";
        modelsWrap.appendChild(label);

        const subcards = document.createElement("div");
        subcards.className = "model-subcards";

        models.forEach((model) => {
          const modelCard = document.createElement("article");
          modelCard.className = "model-subcard";

          const modelTop = document.createElement("div");
          modelTop.className = "card-topline";

          const modelName = document.createElement("strong");
          modelName.className = "card-title model-title";
          modelName.textContent = model.name;

          const modelFlags = document.createElement("div");
          modelFlags.className = "meta-row";
          if (model.vendor) {
            modelFlags.appendChild(makePill(model.vendor));
          }
          if ((model.scopes || []).includes("root")) {
            modelFlags.appendChild(makePill("root", true));
          }
          modelTop.append(modelName, modelFlags);

          modelCard.appendChild(modelTop);

          const profileRow = document.createElement("div");
          profileRow.className = "meta-row";
          const scopes = model.scopes || [];
          if (scopes.length) {
            scopes.forEach((scope) => {
              profileRow.appendChild(makePill(scope === "managed" ? "managed agent" : scope));
            });
          } else {
            profileRow.appendChild(makePill("managed agent"));
          }

          modelCard.appendChild(profileRow);
          subcards.appendChild(modelCard);
        });

        modelsWrap.appendChild(subcards);
        card.appendChild(modelsWrap);
      }

      providerListRoot.appendChild(card);
    });
  }

  agentDetailsRoot.innerHTML = "";
  const card = document.createElement("article");
  card.className = "agent-card";

  const top = document.createElement("div");
  top.className = "card-topline";

  const name = document.createElement("strong");
  name.className = "card-title";
  name.textContent = agent.name || "Managed Agent";

  const flags = document.createElement("div");
  flags.className = "meta-row";
  flags.appendChild(makePill(formatValue(agent.endpoint_name, "endpoint unknown"), true));
  flags.appendChild(makePill(formatValue(agent.model, "model unset")));
  top.append(name, flags);

  const grid = document.createElement("div");
  grid.className = "detail-grid";
  [
    ["Service", agent.service],
    ["Path", agent.path],
    ["Primary provider", agent.model_provider],
    ["Primary base URL", agent.base_url],
    ["Fallback provider", agent.fallback_provider],
    ["Fallback model", agent.fallback_model],
    ["Fallback base URL", agent.fallback_base_url],
    ["Disabled models", agent.router_disabled_models],
    ["Config", agent.has_config ? "present" : "missing"],
    ["Env", agent.has_env ? "present" : "missing"],
    ["Auth", agent.has_auth ? "present" : "missing"],
    ["SOUL", agent.has_soul ? "present" : "missing"],
    ["gateway.pid", agent.has_gateway_pid ? "present" : "missing"],
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
  agentDetailsRoot.append(card);
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
