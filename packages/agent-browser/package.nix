{
  lib,
  stdenvNoCC,
  fetchurl,
  autoPatchelfHook,
  glibc,
}:
let
  pname = "agent-browser";
  version = "0.24.1";
  platformBinary =
    {
      x86_64-linux = "agent-browser-linux-x64";
      aarch64-linux = "agent-browser-linux-arm64";
    }.${stdenvNoCC.hostPlatform.system} or (throw "Unsupported system for ${pname}: ${stdenvNoCC.hostPlatform.system}");
  src = fetchurl {
    url = "https://registry.npmjs.org/agent-browser/-/${pname}-${version}.tgz";
    hash = "sha512-csWJtYEQow52b+p93zVZfNrcNBwbxGCZDXDMNWl2ij2i0MFKubIzN+icUeX2/NrkZe5iIau8px+HQlxata2oPw==";
  };
in
stdenvNoCC.mkDerivation {
  inherit pname version src;

  nativeBuildInputs = [ autoPatchelfHook ];
  buildInputs = [ glibc ];

  sourceRoot = "package";

  installPhase = ''
    runHook preInstall

    mkdir -p $out/bin $out/share/${pname}
    cp -R skills README.md LICENSE $out/share/${pname}/
    install -m0755 bin/${platformBinary} $out/bin/${pname}

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
