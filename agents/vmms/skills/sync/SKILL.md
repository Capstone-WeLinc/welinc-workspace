---
name: sync
description: Reconcile VMMS scope and VMMS-owned project guidance with a completed implementation, without overwriting curated instructions.
---

# VMMS project sync

Use after a VMMS change when asked to update project tracking or durable guidance to match the implementation.

## Reconcile from evidence

- Inspect the final diff, relevant VMMS scope item, spec status, and repository-local guidance. Check the status of each affected repository and preserve unrelated work.
- Update only VMMS-owned `docs/scope/vmms/index.md`, `docs/specs/vmms/`, and `AGENTS.md` files inside VMMS repositories when evidence supports the update.
- When a spec's implementation or verification status changes, keep `index.md`, `rationale.md`, and `verify.md` structurally consistent. The index is the build contract and status summary, the rationale records approved decisions, and the verify file records observable checks plus acceptance-criteria coverage. Do not add a reason or verification record to shared or another system's specs.
- Keep implementation status separate from test and runtime verification. A feature is not done merely because code exists; reconcile each requirement and the project's acceptance evidence.
- If the work reveals stale acceptance criteria, a product decision, or a new cross-system contract, flag it for the owner instead of rewriting approved design or shared workspace documentation.
- Make narrow edits to the exact status, link, or rule that changed. Do not replace whole curated sections or generate dated changelogs unless asked.

## Report

List the project records updated, the evidence used, and any unresolved requirement or decision. Do not change shared suite scope/spec files, another system's folders, auth, portal, or gateway.
