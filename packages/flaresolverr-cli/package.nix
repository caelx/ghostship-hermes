{
  lib,
  python3,
  ghostshipCliContract,
  ...
}:
python3.pkgs.buildPythonApplication {
  pname = "ghostship-flaresolverr";
  version = "0.1.0";
  pyproject = true;

  src = ./.;

  nativeBuildInputs = [
    python3.pkgs.hatchling
  ];

  doCheck = false;

  propagatedBuildInputs = with python3.pkgs; [
    ghostshipCliContract
    httpx
    typer
  ];

  meta = with lib; {
    description = "FlareSolverr CLI wrapper for ghostship-hermes";
    license = licenses.mit;
  };
}
