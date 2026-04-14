ARG HERMES_REF=v2026.4.13
ARG S6_OVERLAY_VERSION=3.2.1.0

FROM ubuntu:24.04 AS base

ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH
ARG HERMES_REF
ARG S6_OVERLAY_VERSION

ENV HOME=/home/hermes \
    HERMES_HOME=/home/hermes/.hermes \
    XDG_CONFIG_HOME=/home/hermes/.config \
    XDG_CACHE_HOME=/home/hermes/.cache \
    XDG_DATA_HOME=/home/hermes/.local/share \
    NPM_CONFIG_PREFIX=/home/hermes/.local \
    npm_config_audit=false \
    npm_config_fund=false \
    npm_config_update_notifier=false \
    CARGO_HOME=/home/hermes/.cargo \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    NIX_CONFIG=experimental-features\ =\ nix-command\ flakes \
    NIXPKGS_ALLOW_UNFREE=1 \
    RUSTUP_HOME=/home/hermes/.rustup \
    GHOSTSHIP_WORKSPACE_ROOT=/workspace \
    GHOSTSHIP_WEB_PORT=7681 \
    GHOSTSHIP_DASHBOARD_HOST=127.0.0.1 \
    GHOSTSHIP_DASHBOARD_PORT=9119 \
    GHOSTSHIP_ROUTER_HOST=127.0.0.1 \
    GHOSTSHIP_ROUTER_PORT=8788 \
    GHOSTSHIP_ROUTER_URL=http://127.0.0.1:8788/v1 \
    GHOSTSHIP_TTYD_SOCKET=/run/user/3000/ttyd.sock \
    GHOSTSHIP_TTYD_BASE_PATH=/terminal \
    GHOSTSHIP_TERMINAL_CWD=/workspace \
    PATH=/home/hermes/.local/bin:/home/hermes/.cargo/bin:/home/hermes/.nix-profile/bin:/opt/ghostship-utils/venv/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    fd-find \
    curl \
    ffmpeg \
    findutils \
    gnupg \
    git \
    grep \
    jq \
    nginx \
    procps \
    python3 \
    python3-venv \
    ripgrep \
    sed \
    tar \
    tmux \
    ttyd \
    util-linux \
    xz-utils \
    yq \
    zstd \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && mkdir -p /etc/apt/keyrings \
    && curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list \
    && apt-get update && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd --gid 3000 hermes && useradd --uid 3000 --gid 3000 --create-home --home-dir /home/hermes --shell /bin/bash hermes

RUN case "$TARGETARCH" in \
      amd64) s6_arch=x86_64 ;; \
      arm64) s6_arch=aarch64 ;; \
      *) echo "unsupported TARGETARCH: $TARGETARCH" >&2; exit 1 ;; \
    esac \
    && curl -fsSL -o /tmp/s6-overlay-noarch.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" \
    && curl -fsSL -o /tmp/s6-overlay-arch.tar.xz "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${s6_arch}.tar.xz" \
    && tar -C / -Jxpf /tmp/s6-overlay-noarch.tar.xz \
    && tar -C / -Jxpf /tmp/s6-overlay-arch.tar.xz \
    && rm -f /tmp/s6-overlay-noarch.tar.xz /tmp/s6-overlay-arch.tar.xz

RUN mkdir -p /nix \
    && chown 3000:3000 /nix \
    && runuser -u hermes -- env HOME=/home/hermes sh -c 'curl -fsSL https://nixos.org/nix/install | sh -s -- --no-daemon --yes --no-modify-profile' \
    && ln -s "$(readlink -f /home/hermes/.nix-profile/bin/nix)" /usr/local/bin/nix \
    && tirith_path="$(runuser -u hermes -- env HOME=/home/hermes PATH=/home/hermes/.nix-profile/bin:/usr/local/bin:/usr/bin:/bin nix --extra-experimental-features 'nix-command flakes' build --no-link --print-out-paths nixpkgs#tirith)" \
    && ln -s "${tirith_path}/bin/tirith" /usr/local/bin/tirith

RUN mkdir -p /opt/hermes \
    && curl -fsSL "https://github.com/NousResearch/hermes-agent/archive/refs/tags/${HERMES_REF}.tar.gz" -o /tmp/hermes-agent.tar.gz \
    && mkdir -p /tmp/hermes-agent \
    && tar -xzf /tmp/hermes-agent.tar.gz -C /tmp/hermes-agent --strip-components=1 \
    && rm -f /tmp/hermes-agent.tar.gz \
    && cd /tmp/hermes-agent/web \
    && npm install --include=optional --no-audit --no-fund \
    && npm run build \
    && python3 -m venv /opt/hermes/venv \
    && /opt/hermes/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/hermes/venv/bin/pip install "/tmp/hermes-agent[all]" \
    && apt-get purge -y build-essential gnupg pkg-config libffi-dev libssl-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/hermes-agent


FROM base AS final

ARG DEBIAN_FRONTEND=noninteractive
ARG HERMES_REF

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /src /opt/ghostship/bin /opt/ghostship /opt/ghostship-router /opt/ghostship-utils
COPY flake.nix /src/
COPY packages /src/packages

RUN curl -fsSL "https://github.com/NousResearch/hermes-agent/archive/refs/tags/${HERMES_REF}.tar.gz" -o /tmp/hermes-agent.tar.gz \
    && mkdir -p /tmp/hermes-agent \
    && tar -xzf /tmp/hermes-agent.tar.gz -C /tmp/hermes-agent --strip-components=1 \
    && rm -f /tmp/hermes-agent.tar.gz \
    && find /src/packages -type d \( -name .venv -o -name __pycache__ -o -name .pytest_cache -o -name .mypy_cache \) -prune -exec rm -rf {} + \
    && python3 /src/packages/hermes-image/build/prepare_upstream_hermes.py /tmp/hermes-agent \
    && cd /tmp/hermes-agent/web \
    && npm install --include=optional --no-audit --no-fund \
    && npm run build \
    && rm -rf /opt/hermes/venv \
    && python3 -m venv /opt/hermes/venv \
    && /opt/hermes/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/hermes/venv/bin/pip install "/tmp/hermes-agent[all]" \
    && python3 -m venv /opt/ghostship-router/venv \
    && /opt/ghostship-router/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/ghostship-router/venv/bin/pip install /src/packages/ghostship-cli-contract /src/packages/hermes-router \
    && python3 -m venv /opt/ghostship-utils/venv \
    && /opt/ghostship-utils/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/ghostship-utils/venv/bin/pip install /src/packages/ghostship-cli-contract /src/packages/*-cli uv \
    && cd /src \
    && tool_paths="$(runuser -u hermes -- env HOME=/home/hermes PATH=/home/hermes/.nix-profile/bin:/usr/local/bin:/usr/bin:/bin NIXPKGS_ALLOW_UNFREE=1 nix --extra-experimental-features 'nix-command flakes' build --impure --no-write-lock-file --no-link --print-out-paths .#blogtato .#gws nixpkgs#bws nixpkgs#gh nixpkgs#google-cloud-sdk)" \
    && for tool_path in $tool_paths; do \
         if [ -d "$tool_path/bin" ]; then \
           for bin in "$tool_path"/bin/*; do \
             [ -e "$bin" ] || continue; \
             ln -sf "$bin" "/opt/ghostship/bin/$(basename "$bin")"; \
           done; \
         fi; \
       done \
    && if [ -x /opt/ghostship/bin/blog ] && [ ! -e /opt/ghostship/bin/blogtato ]; then ln -sf /opt/ghostship/bin/blog /opt/ghostship/bin/blogtato; fi \
    && ln -sf /usr/bin/fdfind /opt/ghostship/bin/fd \
    && cp /src/packages/hermes-image/build/init_home.py /opt/ghostship/bin/init_home.py \
    && apt-get purge -y build-essential pkg-config libffi-dev libssl-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/hermes-agent

RUN mkdir -p /opt/ghostship/home-seed/.local /opt/ghostship/home-seed/.config/nixpkgs \
    && printf '%s\n' '{ allowUnfreePredicate = pkg: builtins.elem (builtins.parseDrvName pkg.name).name [ "bws" ]; }' > /opt/ghostship/home-seed/.config/nixpkgs/config.nix \
    && printf '%s\n' \
      'set -g status-style bg=#041C1C,fg=#FFE6CB' \
      'set -g message-style bg=#0C3838,fg=#FFE6CB' \
      'set -g mode-style bg=#FFBD38,fg=#041C1C' \
      'set -g pane-border-style fg=#0C3838' \
      'set -g pane-active-border-style fg=#67E8F9' \
      'set -g status-left-length 30' \
      'set -g status-right-length 50' \
      "set -g status-left '#[fg=#67E8F9,bold] ghostship '" \
      "set -g status-right '#[fg=#5EEAD4]%Y-%m-%d #[fg=#FFE6CB]%H:%M '" \
      "set -g window-status-current-format '#[fg=#041C1C,bg=#FFBD38,bold] #I:#W '" \
      "set -g window-status-format '#[fg=#FFE6CB,bg=#0A2E2E] #I:#W '" \
      > /opt/ghostship/home-seed/.tmux.conf \
    && npm install --prefix /opt/ghostship/home-seed/.local -g --no-audit --no-fund @openai/codex @google/gemini-cli agent-browser opencode-ai

RUN mkdir -p /opt/ghostship \
    && tar --zstd -cpf /opt/ghostship/nix-seed.tar.zst /nix

COPY packages/hermes-image/rootfs/ /

RUN chmod +x /etc/cont-init.d/10-ghostship-prepare \
    /etc/services.d/hermes-gateway/run \
    /etc/services.d/hermes-dashboard/run \
    /etc/services.d/nginx/run \
    /etc/services.d/ttyd/run \
    /etc/services.d/ghostship-router/run \
    /usr/local/bin/nix \
    /usr/local/bin/ps

EXPOSE 7681
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=5 CMD bash -lc 'curl -fsS "http://127.0.0.1:${GHOSTSHIP_WEB_PORT}/api/status" >/dev/null'
ENTRYPOINT ["/init"]
