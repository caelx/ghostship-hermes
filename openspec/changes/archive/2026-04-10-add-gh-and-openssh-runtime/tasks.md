## 1. Runtime Wiring

- [x] 1.1 Add `gh` and the OpenSSH client package to the default Hermes image/runtime package wiring so `gh`, `ssh`, `scp`, and `ssh-keygen` resolve on PATH inside the container.
- [x] 1.2 Keep the implementation scoped so Chromium and ffmpeg remain absent from the default image contract.

## 2. Policy And Documentation

- [x] 2.1 Update the repo runtime policy and operator-facing docs to list `gh` and OpenSSH client tools, including `ssh-keygen`, as approved extra CLIs in the default image.
- [x] 2.2 Update any image guidance or README references that describe the default runtime tool inventory so they match the new contract.

## 3. Verification

- [x] 3.1 Add or update verification coverage so the built image/runtime checks for `gh`, `ssh`, `scp`, and `ssh-keygen` availability on PATH.
- [x] 3.2 Run the relevant repo validation for the image/runtime wiring and confirm the documentation/spec changes align with the implemented package set.
