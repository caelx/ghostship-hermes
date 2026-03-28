{
  dockerTools,
  pkgs,
  runCommand,
  ghostshipHermesRuntime,
  hermesRelease,
  ghostshipSearxng,
}:
let
  skillsTree = runCommand "ghostship-hermes-default-skills" { } ''
    mkdir -p "$out/share/ghostship-hermes"
    cp -R ${../../skills} "$out/share/ghostship-hermes/skills"
  '';

  etcFiles = runCommand "ghostship-hermes-etc" { } ''
    mkdir -p "$out/etc" "$out/home/hermes"
    printf 'root:x:0:0:root:/root:/bin/sh\nhermes:x:1000:1000:Hermes:/home/hermes:/bin/bash\n' > "$out/etc/passwd"
    printf 'root:x:0:\nhermes:x:1000:\n' > "$out/etc/group"
  '';
in
dockerTools.buildLayeredImage {
  name = "ghostship-hermes";
  tag = hermesRelease;
  contents = with pkgs; [
    bash
    binutils
    bubblewrap
    cacert
    coreutils
    curl
    fd
    ffmpeg
    file
    findutils
    ghostshipHermesRuntime
    ghostshipSearxng
    git
    gnugrep
    gnused
    jq
    lsof
    nix
    nodejs_22
    p7zip
    psmisc
    python311
    ripgrep
    ripgrep-all
    rsync
    strace
    tmux
    tree
    ttyd
    unzip
    uv
    wget
    yq-go
    zip
    codex
    gemini-cli
    opencode
    etcFiles
    skillsTree
  ];

  config = {
    WorkingDir = "/home/hermes";
    Entrypoint = [ "${ghostshipHermesRuntime}/bin/ghostship-hermes-runtime" "entrypoint" ];
    Env = [
      "HOME=/home/hermes"
      "HERMES_HOME=/home/hermes/.hermes"
      "GHOSTSHIP_HERMES_REF=${hermesRelease}"
      "GHOSTSHIP_DEFAULT_SKILLS=/share/ghostship-hermes/skills"
      "NIX_CONFIG=experimental-features = nix-command flakes"
      "PATH=/home/hermes/.hermes/hermes-agent/venv/bin:/home/hermes/.hermes/hermes-agent/node_modules/.bin:/bin"
    ];
    ExposedPorts = {
      "7681/tcp" = { };
    };
    Volumes = {
      "/home/hermes/.hermes" = { };
      "/nix" = { };
    };
    Labels = {
      "org.opencontainers.image.title" = "ghostship-hermes";
      "org.opencontainers.image.description" = "Hermes container with ttyd and curated operator tooling";
      "org.opencontainers.image.version" = hermesRelease;
    };
  };
}
