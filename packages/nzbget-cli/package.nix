{ python311Packages }:
python311Packages.buildPythonApplication {
  pname = "ghostship-nzbget";
  version = "0.1.0";
  pyproject = true;
  src = ./.;

  build-system = with python311Packages; [
    hatchling
  ];

  dependencies = with python311Packages; [
    httpx
    typer
  ];

  nativeCheckInputs = with python311Packages; [
    pytestCheckHook
  ];

  pythonImportsCheck = [ "ghostship_nzbget" ];
}
