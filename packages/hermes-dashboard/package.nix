{ python311Packages }:
python311Packages.buildPythonApplication {
  pname = "hermes-dashboard";
  version = "0.1.0";
  pyproject = true;
  src = ./.;

  build-system = with python311Packages; [
    hatchling
  ];

  dependencies = with python311Packages; [
    fastapi
    uvicorn
    websockets
    httpx
  ];

  nativeCheckInputs = with python311Packages; [
    pytestCheckHook
  ];

  doCheck = false;

  pythonImportsCheck = [ "hermes_dashboard" ];
}
