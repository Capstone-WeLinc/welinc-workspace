---
name: debug
description: Find and fix the root cause of a reproducible VMMS defect without adding features or unrelated refactors.
---

# VMMS debugging

Investigate the reported symptom with evidence, then make the smallest authorized fix in one VMMS repository at a time.

## Investigation

- Capture expected and observed behavior, reproduction steps, inputs, environment, and exact error output. If a necessary reproduction detail cannot be inferred, ask for it while continuing independent inspection.
- Read repository instructions and relevant specs; inspect status and preserve existing changes. Follow the path through caller, API, authorization, business logic, persistence, and presentation as relevant.
- Reproduce using existing documented commands or a narrow request. Do not read secrets or modify production data.
- Form one falsifiable root-cause hypothesis at a time and test it with the smallest relevant observation. Distinguish a proven cause from an unverified theory.

## Fix and close

- Make the minimal change at the root cause. Avoid opportunistic cleanup or feature work.
- Add or update a regression test only when the user has asked for tests; otherwise explain the recommended regression coverage without running tests.
- If the behavior is ambiguous because requirements conflict or omit a rule, stop before choosing product behavior and route the question through `architect`.
- Report the cause, evidence, files changed, verification actually performed, and any remaining uncertainty. Never claim a fix is verified if the reproduction was not rerun.
