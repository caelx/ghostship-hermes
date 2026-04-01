{ python311Packages }:
python311Packages.buildPythonApplication {
  pname = "ghostship-pricebuddy";
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

  doCheck = false;

  pythonImportsCheck = [ "ghostship_pricebuddy" ];
}
