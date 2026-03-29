# Ghostship-Onyx Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a fully featured CLI utility for the Onyx API.

**Architecture:** Python CLI using Typer and httpx, following the ghostship-hermes Python utility conventions.

**Tech Stack:** Python 3.11+, Typer, httpx, pytest.

**Output Standard:** Native JSON by default, with `--pretty` support.

---

### Task 1: Package Scaffolding [COMPLETED]

**Files:**
- Create: `packages/onyx-cli/pyproject.toml`
- Create: `packages/onyx-cli/package.nix`
- Create: `packages/onyx-cli/src/ghostship_onyx/__init__.py`
- Create: `packages/onyx-cli/src/ghostship_onyx/cli.py`
- Create: `packages/onyx-cli/tests/test_cli.py`

- [x] **Step 1: Write Scaffold**

### Task 2: Core API Client [COMPLETED]

**Files:**
- Create: `packages/onyx-cli/src/ghostship_onyx/client.py`

- [x] **Step 1: Implement client**

### Task 3: CLI Endpoints [COMPLETED]

**Files:**
- Modify: `packages/onyx-cli/src/ghostship_onyx/cli.py`

- [x] **Step 1: Implement Typer commands with JSON output**
- [x] **Step 2: Support `--pretty` flag**
- [x] **Step 3: Use environment variables for config**

### Task 4: Skill Documentation [COMPLETED]

**Files:**
- Create: `skills/onyx/SKILL.md`

- [x] **Step 1: Document commands and agent guidance**
