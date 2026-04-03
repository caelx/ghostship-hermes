{
  buildGoModule,
  fetchFromGitHub,
  lib,
}:
buildGoModule rec {
  pname = "feed";
  version = "0.2.0";

  src = fetchFromGitHub {
    owner = "odysseus0";
    repo = "feed";
    rev = "v${version}";
    hash = "sha256-dOWNhEssN8g7V3kK1dTt0wsOOscLdCjVrfOS/+xxwA4=";
  };

  vendorHash = "sha256-gzPYgvxb9CBMZm7aX1ZWwjhQATY3e0dP7WEpv2Mhq14=";

  subPackages = [ "." ];

  ldflags = [
    "-s"
    "-w"
  ];

  meta = with lib; {
    description = "Headless RSS engine for AI agents";
    homepage = "https://github.com/odysseus0/feed";
    license = licenses.mit;
    mainProgram = "feed";
    platforms = platforms.linux ++ platforms.darwin;
  };
}
