{
  lib,
  rustPlatform,
  fetchFromGitHub,
  openssl,
  pkg-config,
}:
rustPlatform.buildRustPackage rec {
  pname = "blogtato";
  version = "0.1.23";

  src = fetchFromGitHub {
    owner = "kantord";
    repo = "blogtato";
    tag = "v${version}";
    hash = "sha256-t5vXui/oJgte8J+kMEUOer0XB6i+A4NqWD9R0hTh8JQ=";
  };

  cargoHash = "sha256-gDyEv7oJdAjY+CxYsYC9VafxNK3jpOFFVDnvbRtnyB8=";

  nativeBuildInputs = [ pkg-config ];
  buildInputs = [ openssl ];

  doCheck = false;

  meta = with lib; {
    description = "A CLI RSS/Atom feed reader inspired by Taskwarrior";
    homepage = "https://github.com/kantord/blogtato";
    license = [ licenses.mit licenses.asl20 ];
    mainProgram = "blog";
    platforms = platforms.linux;
  };
}
