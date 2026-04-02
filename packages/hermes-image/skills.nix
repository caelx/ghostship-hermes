{ pkgs }:
let
  localSkillsTree = builtins.path {
    path = ../../skills;
    name = "ghostship-hermes-skills-local";
  };

  vendoredGoogleWorkspaceSkillsTree = builtins.path {
    path = ../../vendor/googleworkspace-cli/skills;
    name = "ghostship-hermes-skills-googleworkspace";
  };
in
pkgs.runCommand "ghostship-hermes-skills" { } ''
  mkdir -p "$out"
  cp -R ${localSkillsTree}/. "$out/"
  for skill_dir in ${vendoredGoogleWorkspaceSkillsTree}/*; do
    skill_name="$(basename "$skill_dir")"
    if [ -e "$out/$skill_name" ]; then
      echo "skill name collision: $skill_name" >&2
      exit 1
    fi
    cp -R "$skill_dir" "$out/$skill_name"
  done
''
