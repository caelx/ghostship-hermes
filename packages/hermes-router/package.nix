{ python311Packages, ghostshipCliContract }:
python311Packages.buildPythonApplication {
  pname = "ghostship-hermes-router";
  version = "0.1.0";
  pyproject = true;
  src = ./.;

  build-system = with python311Packages; [
    hatchling
  ];

  dependencies = with python311Packages; [
    ghostshipCliContract
    fastapi
    httpx
    uvicorn
  ];

  nativeCheckInputs = with python311Packages; [
    pytestCheckHook
  ];

  doCheck = false;

  pythonImportsCheck = [ "hermes_router" ];
}
