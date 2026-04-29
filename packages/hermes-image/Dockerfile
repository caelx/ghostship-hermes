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
    GHOSTSHIP_NIX_DEFAULT_PROFILE=/nix/var/nix/profiles/per-user/hermes/ghostship-defaults \
    DISCORD_REACTIONS=false \
    DISCORD_REQUIRE_MENTION=false \
    DISCORD_AUTO_THREAD=true \
    GHOSTSHIP_TTYD_SOCKET=/run/user/3000/ttyd.sock \
    GHOSTSHIP_TTYD_BASE_PATH=/terminal \
    GHOSTSHIP_TERMINAL_CWD=/workspace \
    BITWARDENCLI_APPDATA_DIR=/home/hermes/.local/state/bitwarden-cli \
    PATH=/home/hermes/.local/bin:/home/hermes/.cargo/bin:/home/hermes/.nix-profile/bin:/nix/var/nix/profiles/per-user/hermes/ghostship-defaults/bin:/opt/ghostship/bin:/opt/hermes/venv/bin:/opt/ghostship-router/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
    S6_CMD_WAIT_FOR_SERVICES_MAXTIME=0

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    ca-certificates \
    fd-find \
    curl \
    ffmpeg \
    findutils \
    fonts-liberation \
    gnupg \
    git \
    grep \
    jq \
    libasound2t64 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcairo-gobject2 \
    libcairo2 \
    libcups2t64 \
    libdbus-1-3 \
    libdbus-glib-1-2 \
    libdrm2 \
    libevent-2.1-7t64 \
    libfontconfig1 \
    libfreetype6 \
    libgdk-pixbuf-2.0-0 \
    libgbm1 \
    libglib2.0-0 \
    libgtk-3-0 \
    libharfbuzz0b \
    libnspr4 \
    libnss3 \
    libopus0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libpangoft2-1.0-0 \
    libvpx9 \
    libwebp7 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcb-shm0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxext6 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    libxrender1 \
    libxt6 \
    libxtst6 \
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
    xdg-utils \
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
    && ln -s "$(readlink -f /home/hermes/.nix-profile/bin/nix-store)" /usr/local/bin/nix-store


FROM base AS final

ARG DEBIAN_FRONTEND=noninteractive
ARG HERMES_REF

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    pkg-config \
    libffi-dev \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /src /opt/ghostship/bin /opt/ghostship /opt/ghostship-router
COPY flake.nix /src/
COPY flake.lock /src/
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
    && /opt/hermes/venv/bin/pip install --upgrade pip setuptools wheel uv \
    && printf '%s\n' \
      'aiosqlite==0.22.0' \
      'alibabacloud-credentials-api==1.0.0' \
      'alibabacloud-dingtalk==2.2.44' \
      'alibabacloud-endpoint-util==0.0.4' \
      'alibabacloud-gateway-dingtalk==1.0.2' \
      'alibabacloud-gateway-spi==0.0.3' \
      'alibabacloud-openapi-util==0.2.4' \
      'alibabacloud-tea-openapi==0.4.4' \
      'alibabacloud-tea-util==0.3.14' \
      'APScheduler==3.11.2' \
      'asyncpg==0.30.0' \
      'alibabacloud-tea==0.4.3' \
      'alibabacloud-tea-xml==0.0.3' \
      'alibabacloud_credentials==1.0.8' \
      'base58==2.1.1' \
      'cryptography==46.0.6' \
      'darabonba-core==1.0.5' \
      'davey==0.1.4' \
      'daytona==0.157.0' \
      'honcho-ai==2.1.1' \
      'lark-oapi==1.5.5' \
      'Markdown==3.10.1' \
      'mautrix==0.20.8' \
      'mistralai==2.4.2' \
      'opentelemetry-api==1.39.1' \
      'opentelemetry-exporter-otlp-proto-common==1.39.1' \
      'opentelemetry-exporter-otlp-proto-http==1.39.1' \
      'opentelemetry-instrumentation==0.60b1' \
      'opentelemetry-instrumentation-aiohttp-client==0.60b1' \
      'opentelemetry-proto==1.39.1' \
      'opentelemetry-sdk==1.39.1' \
      'opentelemetry-semantic-conventions==0.60b1' \
      'opentelemetry-util-http==0.60b1' \
      'pypng==0.20220715.0' \
      'python-telegram-bot==22.6' \
      'qrcode==7.4.2' \
      'slack-bolt==1.24.0' \
      'slack-sdk==3.39.0' \
      'tornado==6.5.4' \
      'tzlocal==5.3.1' \
      > /tmp/hermes-pip-constraints.txt \
    && UV_EXCLUDE_NEWER=2026-04-24T00:00:00Z /opt/hermes/venv/bin/uv pip install --python /opt/hermes/venv/bin/python --constraint /tmp/hermes-pip-constraints.txt "/tmp/hermes-agent[all]" \
    && python3 -m venv /opt/ghostship-router/venv \
    && /opt/ghostship-router/venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/ghostship-router/venv/bin/pip install /src/packages/hermes-router \
    && python3 -m venv /opt/cloakbrowser-venv \
    && /opt/cloakbrowser-venv/bin/pip install --upgrade pip setuptools wheel \
    && /opt/cloakbrowser-venv/bin/pip install "cloakbrowser==0.3.25" \
    && mkdir -p /opt/ghostship/cloakbrowser-cache \
    && mkdir -p /opt/ghostship/home-seed/.hermes \
    && cp -R /tmp/hermes-agent/skills /opt/ghostship/home-seed/.hermes/skills \
    && cloakbrowser_bin="$(HOME=/root CLOAKBROWSER_CACHE_DIR=/opt/ghostship/cloakbrowser-cache /opt/cloakbrowser-venv/bin/python -c 'import os; from cloakbrowser.download import ensure_binary; print(ensure_binary(), flush=True); os._exit(0)')" \
    && cloakbrowser_dir="$(dirname "$cloakbrowser_bin")" \
    && ln -sfn "$cloakbrowser_dir" /opt/ghostship/cloakbrowser-current \
    && touch /opt/ghostship/cloakbrowser-cache/.welcome_shown \
    && cd /src \
    && tirith_path="$(runuser -u hermes -- env HOME=/home/hermes PATH=/home/hermes/.nix-profile/bin:/usr/local/bin:/usr/bin:/bin nix --extra-experimental-features 'nix-command flakes' build --impure --no-write-lock-file --no-link --print-out-paths .#tirith)" \
    && ln -sf "${tirith_path}/bin/tirith" /usr/local/bin/tirith \
    && default_tools_path="$(runuser -u hermes -- env HOME=/home/hermes PATH=/home/hermes/.nix-profile/bin:/usr/local/bin:/usr/bin:/bin NIXPKGS_ALLOW_UNFREE=1 nix --extra-experimental-features 'nix-command flakes' build --impure --no-write-lock-file --no-link --print-out-paths .#ghostship-default-tools)" \
    && printf '%s\n' "$default_tools_path" > /opt/ghostship/nix-default-tools.out-path \
    && runuser -u hermes -- env HOME=/home/hermes PATH=/home/hermes/.nix-profile/bin:/usr/local/bin:/usr/bin:/bin sh -lc 'closure_paths="$(nix-store -qR "'"$default_tools_path"'")"; nix-store --export $closure_paths' \
      | zstd -19 -T0 -o /opt/ghostship/nix-default-tools.export.zst \
    && ln -sf /usr/bin/fdfind /opt/ghostship/bin/fd \
    && cp /src/packages/hermes-image/build/init_home.py /opt/ghostship/bin/init_home.py \
    && apt-get purge -y build-essential gnupg pkg-config libffi-dev libssl-dev \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/* /tmp/hermes-agent

RUN mkdir -p /opt/ghostship/home-seed/.hermes /opt/ghostship/home-seed/.local /opt/ghostship/home-seed/.config/nixpkgs \
    && printf '%s\n' '{ allowUnfreePredicate = pkg: builtins.elem (builtins.parseDrvName pkg.name).name [ "bitwarden-cli" ]; }' > /opt/ghostship/home-seed/.config/nixpkgs/config.nix \
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
    /usr/local/bin/google-chrome \
    /usr/local/bin/nix \
    /usr/local/bin/nix-store \
    /usr/local/bin/ps \
    && ln -sf /usr/local/bin/google-chrome /usr/local/bin/google-chrome-stable

EXPOSE 7681
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=5 CMD bash -lc 'curl -fsS "http://127.0.0.1:${GHOSTSHIP_WEB_PORT}/api/status" >/dev/null'
ENTRYPOINT ["/init"]
