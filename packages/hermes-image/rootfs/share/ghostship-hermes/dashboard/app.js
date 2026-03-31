const profilesRoot = document.getElementById("profiles");
const activeName = document.getElementById("active-name");
const popoutLink = document.getElementById("popout-link");
const profileFrame = document.getElementById("profile-frame");

const state = {
  profiles: [],
  activeSlug: null,
};

function currentSlugFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return params.get("profile");
}

function pickDefaultProfile(profiles) {
  const requested = currentSlugFromUrl();
  if (requested && profiles.some((profile) => profile.slug === requested)) {
    return requested;
  }
  const defaultProfile = profiles.find((profile) => profile.is_default);
  return defaultProfile ? defaultProfile.slug : profiles[0]?.slug ?? "default";
}

function syncUrl(slug) {
  const url = new URL(window.location.href);
  url.searchParams.set("profile", slug);
  window.history.replaceState({}, "", url);
}

function renderProfiles() {
  profilesRoot.innerHTML = "";
  for (const profile of state.profiles) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "profile-card";
    button.dataset.profile = profile.slug;
    if (profile.slug === state.activeSlug) {
      button.classList.add("active");
    }

    const gatewayText = profile.gateway_expected ? "Gateway On" : "Gateway Off";
    button.innerHTML = `
      <span class="profile-title">${profile.name}</span>
      <span class="profile-meta">${profile.is_default ? "Default profile" : "Named profile"}</span>
      <span class="status ${profile.gateway_expected ? "status-on" : "status-off"}">${gatewayText}</span>
    `;

    button.addEventListener("click", () => activateProfile(profile.slug));
    profilesRoot.appendChild(button);
  }
}

function activateProfile(slug, options = {}) {
  const { reloadFrame = true } = options;
  const profile = state.profiles.find((entry) => entry.slug === slug);
  if (!profile) {
    return;
  }

  state.activeSlug = slug;
  activeName.textContent = profile.name;
  if (reloadFrame || profileFrame.getAttribute("src") !== profile.terminal_path) {
    profileFrame.src = profile.terminal_path;
  }
  popoutLink.href = profile.terminal_path;
  syncUrl(slug);
  renderProfiles();
}

async function loadProfiles() {
  const response = await fetch("/api/profiles.json", { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`profiles request failed: ${response.status}`);
  }
  const payload = await response.json();
  state.profiles = payload.profiles ?? [];
  if (!state.activeSlug || !state.profiles.some((profile) => profile.slug === state.activeSlug)) {
    state.activeSlug = pickDefaultProfile(state.profiles);
  }
  activateProfile(state.activeSlug, { reloadFrame: false });
}

async function refreshProfiles() {
  try {
    await loadProfiles();
  } catch (error) {
    console.error(error);
  }
}

window.addEventListener("DOMContentLoaded", async () => {
  await refreshProfiles();
  window.setInterval(refreshProfiles, 5000);
});
