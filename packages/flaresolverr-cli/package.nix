{
  lib,
  python3,
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

  propagatedBuildInputs = with python3.pkgs; [
    httpx
    typer
  ];

  meta = with lib; {
    description = "FlareSolverr CLI wrapper for ghostship-hermes";
    license = licenses.mit;
  };
}
