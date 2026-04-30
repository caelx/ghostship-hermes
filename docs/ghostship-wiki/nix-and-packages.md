# Nix And Packages

## Persisted Nix

`/nix` persists across container replacement. The image owns a default profile at:

`/nix/var/nix/profiles/per-user/hermes/ghostship-defaults`

The user's mutable profile is:

`/home/hermes/.nix-profile`

Use the user profile for task-specific installs:

```bash
nix --extra-experimental-features 'nix-command flakes' profile install nixpkgs#package-name
```

## When To Use Nix

Use Nix for durable CLI tools that should survive container replacement. Use `uv`,
`npm`, or language-native package managers for project-local dependencies. Avoid
installing large tools into the image unless they are required for boot, Hermes,
browser operation, dashboard/terminal operation, or a stable default utility.

## Useful Checks

```bash
command -v nix
nix profile list
command -v bw gh gcloud gws blogwatcher-cli
```
