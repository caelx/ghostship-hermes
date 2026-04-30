{
  lib,
  stdenvNoCC,
  fetchurl,
  autoPatchelfHook,
  glibc,
  makeWrapper,
}:
let
  pname = "agent-browser";
  version = "0.26.0";
  platformBinary =
    {
      x86_64-linux = "agent-browser-linux-x64";
      aarch64-linux = "agent-browser-linux-arm64";
    }.${stdenvNoCC.hostPlatform.system} or (throw "Unsupported system for ${pname}: ${stdenvNoCC.hostPlatform.system}");
  src = fetchurl {
    url = "https://registry.npmjs.org/agent-browser/-/${pname}-${version}.tgz";
    hash = "sha512-pdqSfjwbFSp+qnwlb2g23e9wXveIOfMi19xpPA9xZUbzEAUp6W4YBZj6Ybj8z4M7WkcbGDDYc+oDIHDt9R3EDQ==";
  };
in
stdenvNoCC.mkDerivation {
  inherit pname version src;

  nativeBuildInputs = [ autoPatchelfHook makeWrapper ];
  buildInputs = [ glibc ];

  sourceRoot = "package";

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/${pname}/package
    cp -R . $out/share/${pname}/package/
    chmod -R u+w $out/share/${pname}/package
    install -m0755 bin/${platformBinary} $out/share/${pname}/package/bin/${platformBinary}
    makeWrapper $out/share/${pname}/package/bin/${platformBinary} $out/bin/${pname}

    runHook postInstall
  '';

  meta = with lib; {
    description = "Browser automation CLI for AI agents";
    homepage = "https://agent-browser.dev";
    license = licenses.asl20;
    platforms = [ "x86_64-linux" "aarch64-linux" ];
    mainProgram = pname;
    sourceProvenance = with sourceTypes; [ binaryNativeCode ];
  };
}
