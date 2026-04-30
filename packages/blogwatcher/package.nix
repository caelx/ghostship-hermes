{
  lib,
  stdenvNoCC,
  fetchurl,
}:
let
  version = "0.2.0";
  srcs = {
    x86_64-linux = {
      url = "https://github.com/JulienTant/blogwatcher-cli/releases/download/v0.2.0/blogwatcher-cli_linux_amd64.tar.gz";
      hash = "sha256-6qJeu+E2H+kifBGPOP13fOi6ihdelU95BgiefSzs8iI=";
    };
    aarch64-linux = {
      url = "https://github.com/JulienTant/blogwatcher-cli/releases/download/v0.2.0/blogwatcher-cli_linux_arm64.tar.gz";
      hash = "sha256-y/YuHFPSYPSDrO73l5+q3Ky+bFepB4ZQd2t6gmwmHxk=";
    };
  };
  source =
    srcs.${stdenvNoCC.hostPlatform.system}
      or (throw "blogwatcher-cli is unsupported on ${stdenvNoCC.hostPlatform.system}");
in
stdenvNoCC.mkDerivation {
  pname = "blogwatcher-cli";
  inherit version;

  src = fetchurl source;

  sourceRoot = ".";

  installPhase = ''
    runHook preInstall
    install -Dm755 blogwatcher-cli $out/bin/blogwatcher-cli
    runHook postInstall
  '';

  meta = with lib; {
    description = "CLI RSS/Atom feed watcher";
    homepage = "https://github.com/JulienTant/blogwatcher-cli";
    license = licenses.mit;
    platforms = [
      "x86_64-linux"
      "aarch64-linux"
    ];
    mainProgram = "blogwatcher-cli";
  };
}
