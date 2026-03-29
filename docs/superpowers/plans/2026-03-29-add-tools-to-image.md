# Add Tools to Hermes Image Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `delta`, `bat`, `miller`, `sqlite-utils`, `yt-dlp`, `exiftool`, `visidata`, and `hn-text` to the `ghostship-hermes` image.

**Architecture:** Modify `packages/hermes-image/image.nix` to include these packages in the `contents` list.

**Tech Stack:** Nix, DockerTools.

---

### Task 1: Update image.nix

**Files:**
- Modify: `packages/hermes-image/image.nix`

- [ ] **Step 1: Add new packages to the contents list**

Modify the `contents` list in `packages/hermes-image/image.nix` to include:
- `bat`
- `delta`
- `exiftool`
- `hn-text`
- `miller`
- `sqlite-utils`
- `visidata`
- `yt-dlp`

```nix
  contents = with pkgs; [
    bash
    bat
    binutils
    bubblewrap
    cacert
    coreutils
    curl
    delta
    exiftool
    fd
    ffmpeg
    file
    findutils
    gh
    ghostshipHermesRuntime
    git
    gnugrep
    gnused
    hn-text
    jq
    lsof
    miller
    nix
    nodejs_22
    p7zip
    psmisc
    python311
    ripgrep
    ripgrep-all
    rsync
    sqlite-utils
    strace
    tmux
    tree
    ttyd
    unzip
    uv
    visidata
    wget
    yq-go
    yt-dlp
    zip
    codex
    gemini-cli
    opencode
    rootfs
  ] ++ ghostshipUtilities;
```

- [ ] **Step 2: Commit changes**

```bash
git add packages/hermes-image/image.nix
git commit -m "feat: add bat, delta, exiftool, hn-text, miller, sqlite-utils, visidata, yt-dlp to image"
```

### Task 2: Validate the image build

- [ ] **Step 1: Build the image package**

Run: `nix build .#ghostship-hermes-image`

Expected: SUCCESS.

- [ ] **Step 2: Verify binary availability**

Check if one of the new binaries is present in the build output.
Run: `ls result/bin | grep -E "bat|delta|exiftool|hn|mlr|sqlite-utils|visidata|yt-dlp"`

Expected: List of binaries.
