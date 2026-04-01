{ python311Packages, ghostshipCliContract }:
python311Packages.buildPythonApplication {
  pname = "ghostship-flaresolverr";
  version = "0.1.0";
  pyproject = true;

  src = ./.;

  build-system = with python311Packages; [
    hatchling
  ];

  doCheck = false;

  dependencies = with python311Packages; [
    ghostshipCliContract
    httpx
    typer
  ];

  nativeCheckInputs = with python311Packages; [
    pytest
  ];
}
