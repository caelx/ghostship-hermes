# Hybrid API Doc Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Bring every `ghostship-*` API-backed utility under `docs/api/` with a canonical reference artifact, using official raw specs where upstream publishes them and repo-owned full reference sheets where it does not.

**Architecture:** Keep the existing raw OpenAPI or Swagger mirrors for services that publish machine-readable specs, then add companion Markdown spec sheets that explain auth, base URLs, and source provenance. For services without a published spec, add repo-owned full endpoint reference sheets that enumerate the whole API surface the repo can rely on.

**Tech Stack:** Markdown, mirrored OpenAPI or Swagger JSON, upstream official documentation, upstream repository code and tests, shell tooling (`curl`, `jq`, `rg`).

---

### Task 1: Coverage Inventory

**Files:**
- Modify: `docs/api/README.md`
- Create: `docs/superpowers/plans/2026-03-29-hybrid-api-doc-coverage.md`

- [ ] **Step 1: Inventory utility coverage**

Run: `for d in packages/*-cli; do basename "$d" | sed 's/-cli$//'; done | sort`
Expected: full utility list for API-backed packages.

- [ ] **Step 2: Inventory current API artifacts**

Run: `find docs/api -maxdepth 1 -type f | sort`
Expected: current mirrored raw specs and curated Markdown files.

- [ ] **Step 3: Classify each utility**

Create a working table with these columns:
- utility name
- upstream source of truth
- raw spec available (`yes` or `no`)
- repo-owned Markdown spec needed (`yes` or `no`)

### Task 2: Raw Spec Harvesting

**Files:**
- Create or update: `docs/api/*.json`

- [ ] **Step 1: For each utility with official machine-readable docs, fetch the live upstream spec**

Run the exact upstream fetch command for each service and save the artifact under `docs/api/`.

- [ ] **Step 2: Normalize filenames**

Use this naming pattern:
- `<service>-openapi.json`
- `<service>-swagger.json`

- [ ] **Step 3: Record provenance**

For each mirrored raw spec, note the official upstream URL in the companion Markdown sheet.

### Task 3: Repo-Owned Full Reference Sheets

**Files:**
- Create: `docs/api/*.md`

- [ ] **Step 1: Add one canonical Markdown spec sheet per utility**

Each file must include:
- service identity
- base URL and API base path
- auth model and environment variable mapping
- full endpoint inventory or command inventory from upstream docs
- notes on pagination, filters, response conventions, and known caveats
- source links

- [ ] **Step 2: Mark the source quality**

Every sheet must clearly label whether it is based on:
- official OpenAPI or Swagger
- official narrative docs
- upstream source code or tests
- repo inference

- [ ] **Step 3: Keep the raw spec and the Markdown sheet aligned**

If a raw spec exists, the Markdown sheet should summarize and point to it rather than duplicating every schema.

### Task 4: Repo Integration

**Files:**
- Modify: `docs/api/README.md`
- Modify: `README.md`
- Modify: `CHANGELOG.md`
- Modify: `AGENTS.md`

- [ ] **Step 1: Update the API index**

Make `docs/api/README.md` list every utility and identify whether its canonical artifact is a raw mirrored spec, a repo-owned Markdown sheet, or both.

- [ ] **Step 2: Update root docs**

Add a short note in `README.md` pointing maintainers to `docs/api/` as the canonical API reference area.

- [ ] **Step 3: Update memory**

Record any newly discovered upstream API facts in `AGENTS.md`.

### Task 5: Verification

**Files:**
- Verify: `docs/api/`

- [ ] **Step 1: Verify coverage count**

Run: `for d in packages/*-cli; do basename "$d" | sed 's/-cli$//'; done | sort`
Expected: one matching canonical API doc entry per utility in `docs/api/README.md`.

- [ ] **Step 2: Verify file presence**

Run: `find docs/api -maxdepth 1 -type f | sort`
Expected: complete hybrid documentation set with no missing utilities.

- [ ] **Step 3: Verify repo diff**

Run: `git diff --stat`
Expected: added or updated API artifacts plus index and memory documentation updates.
