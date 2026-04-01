{ python311Packages }:
python311Packages.buildPythonPackage {
  pname = "ghostship-cli-contract";
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

  pythonImportsCheck = [ "ghostship_cli_contract" ];
}
