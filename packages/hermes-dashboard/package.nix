{ python311Packages }:
let
  pythonSitePackages = python311Packages.python.sitePackages;
  fastapiRuntime = python311Packages.fastapi.overridePythonAttrs (old: {
    doCheck = false;
    doInstallCheck = false;
    nativeCheckInputs = [ ];
  });
in
python311Packages.buildPythonApplication {
  pname = "hermes-dashboard";
  version = "0.1.0";
  pyproject = true;
  src = ./.;

  build-system = with python311Packages; [
    hatchling
  ];

  dependencies = with python311Packages; [
    fastapiRuntime
    uvicorn
    websockets
    httpx
  ];

  nativeCheckInputs = with python311Packages; [
    pytestCheckHook
  ];

  doCheck = false;

  pythonImportsCheck = [ "hermes_dashboard" ];

  postInstall = ''
    test -x "$out/bin/hermes-dashboard"
    test -f "$out/${pythonSitePackages}/hermes_dashboard/static/index.html"
    test -f "$out/${pythonSitePackages}/hermes_dashboard/static/app.js"
    test -f "$out/${pythonSitePackages}/hermes_dashboard/static/styles.css"
    test -f "$out/${pythonSitePackages}/hermes_dashboard/static/logo.png"
  '';
}
