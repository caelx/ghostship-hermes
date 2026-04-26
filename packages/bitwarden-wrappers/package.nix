{
  lib,
  stdenvNoCC,
}:

stdenvNoCC.mkDerivation {
  pname = "ghostship-bitwarden-wrappers";
  version = "0.1.0";

  src = ./.;

  installPhase = ''
    runHook preInstall
    install -Dm755 bin/bw-unlock "$out/bin/bw-unlock"
    install -Dm755 bin/bw-lock "$out/bin/bw-lock"
    runHook postInstall
  '';

  meta = with lib; {
    description = "Ghostship Bitwarden CLI session wrappers";
    license = licenses.mit;
    platforms = platforms.linux;
  };
}
