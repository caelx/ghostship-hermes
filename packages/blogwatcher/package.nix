{
  lib,
  stdenvNoCC,
  fetchurl,
}:
let
  version = "0.2.1";
  srcs = {
    x86_64-linux = {
      url = "https://github.com/JulienTant/blogwatcher-cli/releases/download/v0.2.1/blogwatcher-cli_linux_amd64.tar.gz";
      hash = "sha256-DYBO+f+6Z6H6taBtzo+SC2f6i93+hOQIZ8nRICr0Qzk=";
    };
    aarch64-linux = {
      url = "https://github.com/JulienTant/blogwatcher-cli/releases/download/v0.2.1/blogwatcher-cli_linux_arm64.tar.gz";
      hash = "sha256-0vc0FXu8KS53Zoz7s60lvE46YkaySUnetdWqiut7Z4A=";
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
