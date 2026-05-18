{
  lib,
  bashInteractive,
  buildNpmPackage,
  makeWrapper,
  python311Packages,
  ttyd,
}:
let
  pythonSitePackages = python311Packages.python.sitePackages;
  runtimeBinPath = lib.makeBinPath [
    bashInteractive
    ttyd
  ];
  fastapiRuntime = python311Packages.fastapi.overridePythonAttrs (_: {
    doCheck = false;
    doInstallCheck = false;
    nativeCheckInputs = [ ];
  });
  huduiFrontend = buildNpmPackage {
    pname = "hermes-dashboard-frontend";
    version = "0.2.0";
    src = ./frontend;
    npmDepsHash = "sha256-KBHeTNkPc3q7i/2Lsu7PSvIZmjYSEcNRb8fzw0XbjCw=";
    installPhase = ''
      runHook preInstall
      mkdir -p "$out"
      cp -r dist/* "$out/"
      runHook postInstall
    '';
  };
in
python311Packages.buildPythonApplication {
  pname = "hermes-dashboard";
  version = "0.2.0";
  pyproject = true;
  src = ./.;

  build-system = with python311Packages; [
    hatchling
  ];

  dependencies = with python311Packages; [
    fastapiRuntime
    httpx
    pyyaml
    uvicorn
    watchfiles
    websockets
  ];

  nativeBuildInputs = [
    makeWrapper
  ];

  nativeCheckInputs = with python311Packages; [
    pytestCheckHook
  ];

  doCheck = false;

  postPatch = ''
    rm -rf src/hermes_dashboard/static
    mkdir -p src/hermes_dashboard/static
    cp -r ${huduiFrontend}/* src/hermes_dashboard/static/
  '';

  pythonImportsCheck = [ "hermes_dashboard" ];

  postFixup = ''
    wrapProgram "$out/bin/hermes-dashboard"       --prefix PATH : "${runtimeBinPath}"       --set-default GHOSTSHIP_BASH "${bashInteractive}/bin/bash"
  '';

  postInstall = ''
    test -x "$out/bin/hermes-dashboard"
    test -f "$out/${pythonSitePackages}/hermes_dashboard/static/index.html"
    test -d "$out/${pythonSitePackages}/hermes_dashboard/static/assets"
  '';
}
