# Security Policy

## Reporting

Do not open public issues for suspected secrets exposure or vulnerabilities that could affect deployed systems.

Instead, report the issue privately to the maintainer with:

- a description of the issue
- impact assessment
- reproduction steps
- any suggested mitigation

## Scope

Security-sensitive areas include:

- container image publishing
- Hermes bootstrap and dependency installation
- mounted runtime volumes
- secrets passed through environment variables or config files
