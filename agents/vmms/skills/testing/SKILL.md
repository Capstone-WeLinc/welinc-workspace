---
name: testing
description: Plan or run VMMS tests and verification for a requested feature, bug fix, or release candidate using the target repository's existing checks.
---

# VMMS testing and verification

Use this skill when the user asks to test, verify, or prepare release evidence for VMMS work. Do not run tests merely because code was edited; first obtain an explicit request to verify, consistent with `agents/vmms/AGENTS.md`.

## Select meaningful checks

- Read repository instructions and package scripts; inspect the changed code and existing tests before selecting commands.
- Read `docs/specs/vmms/NNNN-title/verify.md` and map checks to its acceptance criteria; use `index.md` to separate the build contract from runtime status and `rationale.md` to resolve settled decision questions.
- Map acceptance criteria to checks. Prefer focused unit or integration tests for the changed behavior, then relevant typecheck, lint, build, migration validation, or broader suites when warranted and documented.
- For real-browser tests of VMMS web journeys, follow `../playwright/SKILL.md` alongside this skill. Keep unit, API, mobile, and browser coverage distinct.
- Include authorization and negative-path cases when behavior is access-controlled; include persistence and API contract cases when those layers changed; include mobile offline/sync cases only when applicable.
- Do not invent test commands, change dependencies, create a new test framework, or alter production data just to obtain a green result. Ask before destructive, costly, external, or production-like verification.
- Do not read `.env` values. If a check needs unavailable configuration or services, report the exact missing prerequisite without exposing secrets.

## Run and report

- Check repository status first and keep test-generated files out of the change unless the task calls for fixtures or snapshots.
- Run the smallest relevant documented check first; expand only when results or requested confidence justify it.
- Report each command and whether it passed, failed, or could not run. Include concise error context and distinguish code failures from environment/setup failures.
- Tie results to requirements and acceptance criteria. A passing build is not proof of business behavior, and an unrun test is not verification.
- Do not claim end-to-end, cross-service, mobile-device, or release verification unless that environment and path were actually exercised.
