{
  fetchPypi,
  python311Packages,
}:
python311Packages.buildPythonPackage rec {
  pname = "honcho-ai";
  version = "2.0.1";
  pyproject = true;

  src = fetchPypi {
    pname = "honcho_ai";
    inherit version;
    hash = "sha256-b97r+UVOYrxSPVeIjlA1nme6r9sh9oYh+cFOCNwAYjo=";
  };

  build-system = with python311Packages; [
    setuptools
    wheel
  ];

  dependencies = with python311Packages; [
    httpx
    pydantic
    typing-extensions
  ];

  doCheck = false;

  pythonImportsCheck = [ "honcho" ];
}
