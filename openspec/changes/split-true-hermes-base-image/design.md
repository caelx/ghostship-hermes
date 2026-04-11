## Context

The current image architecture uses one shared NixOS module for both `ghostship-hermes-base` and the final `ghostship-hermes` image. The base variant swaps the real repo-owned commands for shim binaries that forward into `/opt/ghostship-overlay`, which keeps the existing systemd units and PATH wiring intact but means the base image still embeds repo-specific service assumptions. That is workable as a transition, but it is not a true Hermes base layer.

## Goals / Non-Goals

**Goals:**
- Produce a real reusable base image whose NixOS closure contains the Hermes runtime, container boot contract, and the stable shared runtimes/dependency closures that many repo-owned packages repeatedly need.
- Move repo-owned router/dashboard/runtime service wiring and utility exposure out of the base layer and into the final image composition path.
- Remove shim binaries from the base image entirely.
- Preserve the existing final `ghostship-hermes` runtime behavior, published tags, and consumer-facing image semantics.

**Non-Goals:**
- Replacing the final overlay bundle with a different packaging technology.
- Changing the published mutable tag scheme or GHCR repository names.
- Redesigning the Hermes runtime itself beyond what is needed to split the base and final layers cleanly.

## Decisions

### 1. Split the shared image module into base and final roles

Instead of building both images from the same `nixos-module.nix`, introduce a base-focused module or module flag that includes only the Hermes runtime, boot/storage contract, and any system services that must exist before repo-owned content is added. The final image layer then adds the repo-specific router/dashboard/runtime and utility services.

Alternatives considered:
- Keep the shared module and keep improving shim boundaries: smaller immediate diff, but it preserves the same architectural coupling that makes the base image impure.
- Move all repo-owned service definitions into shell scripts outside NixOS modules: possible, but it weakens the declarative service contract and makes the final image harder to reason about.

### 2. Put only stable shared dependencies in the base layer

The base image may include stable shared runtimes and dependency closures that are broadly reused by the repo-owned layer, such as interpreters, language runtimes, or common support packages, but only when those dependencies are not themselves carrying repo-owned service semantics. That gives the overlay less to copy while keeping the base image decoupled from repo-specific commands.

Alternatives considered:
- Keep every non-Hermes dependency in the overlay: simplest conceptual split, but it leaves obvious high-fanout shared closures out of the reusable layer and reduces the benefit of the new base boundary.
- Move all repo package dependencies into base aggressively: larger reuse, but it risks pulling repo coupling and churn back into the base layer.

### 3. Treat repo-owned services as final-image-only wiring

`ghostship-hermes-router`, `ghostship-hermes-runtime`, `hermes-dashboard`, and the `ghostship-*` utilities should be absent from the base NixOS closure. The final image composition path should add those real binaries and whichever systemd/PATH integration they need.

Alternatives considered:
- Keep tiny placeholder binaries in base: easy, but it defeats the point of making the base truly upstream-like and low-churn.

### 4. Keep the final image contract stable while changing the internal layering

The base/final split is an internal publication architecture change. The final published `ghostship-hermes` image must still expose `/init`, `HOME=/home/hermes`, `HERMES_HOME=/home/hermes/.hermes`, the expected services, and the documented multi-arch publish semantics.

Alternatives considered:
- Publish a new consumer-facing image contract for the base layer: unnecessary right now; the base image is an internal reuse artifact, not the primary operator-facing product.

## Risks / Trade-offs

- [Base image accidentally drops required boot/runtime behavior] -> Keep the base module scoped to boot/storage/Hermes essentials plus intentionally selected stable shared dependencies, and verify the final image still satisfies the documented runtime contract.
- [Final image assembly becomes harder to reason about] -> Make the boundary explicit in flake/module structure so maintainers can see what belongs to base versus final content.
- [Some repo-owned runtime assumptions are more deeply embedded than expected] -> Extract those assumptions incrementally into final-image-only modules/scripts rather than trying to rewrite unrelated runtime logic at the same time.
- [Cold publish time may still remain high] -> Treat this as an architectural cleanup that should improve base reuse quality, not as a guaranteed complete solution to publish latency on its own.

## Migration Plan

1. Introduce distinct base and final image composition paths in the flake/module layout.
2. Identify which shared runtimes/dependency closures belong in base versus final content.
3. Move repo-owned services and PATH wiring out of the base path.
4. Remove shim binaries from the base image.
5. Update publish logic and docs to describe the true base/final split.
6. Validate that the final published image still matches the current runtime contract and that overlay-only changes no longer require a repo-coupled base rebuild path.

Rollback strategy:
- Revert to the current shared-module-plus-shims architecture if the split drops required runtime behavior or becomes too invasive for the current release window.

## Open Questions

- Which stable shared dependency closures actually pay their way in the base image without reintroducing repo coupling?
- Which services or PATH assumptions still need to exist in the base image for first-boot correctness?
- Should the final image add repo-owned service definitions through a second NixOS module, a post-base overlay module, or a small finalization layer generated from flake outputs?
- Do any current image tests need to be split so base-only validation and final-image validation remain clear?
