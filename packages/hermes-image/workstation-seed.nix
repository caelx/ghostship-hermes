{ pkgs }:
let
  workstationSeedTree = builtins.path {
    path = ./workstation-seed;
    name = "ghostship-hermes-workstation-seed-tree";
  };

  codexSkillsTree = builtins.path {
    path = ../../.codex/skills;
    name = "ghostship-hermes-codex-skills";
  };

  geminiCommandsTree = builtins.path {
    path = ../../.gemini/commands;
    name = "ghostship-hermes-gemini-commands";
  };

  geminiSkillsTree = builtins.path {
    path = ../../.gemini/skills;
    name = "ghostship-hermes-gemini-skills";
  };

  opencodeCommandsTree = builtins.path {
    path = ../../.opencode/command;
    name = "ghostship-hermes-opencode-command";
  };

  opencodeSkillsTree = builtins.path {
    path = ../../.opencode/skills;
    name = "ghostship-hermes-opencode-skills";
  };
in
pkgs.runCommand "ghostship-hermes-workstation-seed" { } ''
  mkdir -p "$out"
  cp -R ${workstationSeedTree}/. "$out/"

  mkdir -p "$out/.codex" "$out/.gemini" "$out/.opencode"
  rm -rf "$out/.codex/skills" "$out/.gemini/commands" "$out/.gemini/skills" "$out/.opencode/command" "$out/.opencode/skills"
  cp -R ${codexSkillsTree} "$out/.codex/skills"
  cp -R ${geminiCommandsTree} "$out/.gemini/commands"
  cp -R ${geminiSkillsTree} "$out/.gemini/skills"
  cp -R ${opencodeCommandsTree} "$out/.opencode/command"
  cp -R ${opencodeSkillsTree} "$out/.opencode/skills"
''
