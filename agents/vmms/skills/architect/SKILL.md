---
name: architect
description: Define a VMMS feature design and acceptance contract before implementation when a key business, data, integration, or UI decision is unresolved.
---

# VMMS feature design

Use this skill when a request requires a decision that current VMMS requirements, specs, and implementation do not settle. For straightforward work already covered by an approved spec, use the coding skill directly.

## Decide what needs a spec

- Read the relevant VMMS scope item, BRD/RTM requirements, repository instructions, and existing VMMS specs before recommending a design.
- Separate settled requirements from assumptions. Identify conflicts, especially shared identity ownership, cross-system data access, repair-cost ownership, and Admin versus Operations analytics access.
- Ask only for decisions that change user-visible behavior, data ownership, security, compatibility, or a hard-to-reverse implementation choice. Present a recommended option and its tradeoffs.
- Do not silently select a new provider, library, database model, or cross-repository contract when the project artifacts leave it undecided.

## Write the design

- For a material feature decision, create or update a VMMS-owned spec under `docs/specs/vmms/NNNN-title/` with an `index.md`, `rationale.md`, and `verify.md`, following neighboring suite conventions.
- In `index.md`, record the build contract: summary, requirements/decision, behavior, acceptance criteria, API/data/migration impact, security/failure behavior, affected repositories, and verification plan or implementation status.
- In `rationale.md`, record context, forces, options considered, tradeoffs, the chosen option, and smaller decisions that affect implementation.
- In `verify.md`, derive observable manual/API/automated steps from the acceptance criteria, distinguish completed evidence from remaining checks, and include acceptance-criteria coverage.
- Link `[rationale.md](rationale.md)` and `[verify.md](verify.md)` from `index.md`.
- Include summary, source requirements and IDs, user roles, behavior, acceptance criteria that can be observed, data/API impact, failure and edge cases, security, migration needs, affected VMMS repositories, risks, and verification approach.
- Link each build task to acceptance criteria and keep scope coarse in `docs/scope/vmms/index.md`; do not turn the scope page into an implementation checklist.
- Never edit shared workspace specs, the shared scope index, auth, portal, gateway, or another system. A cross-repository boundary change needs the workspace spec-first process and authorization.

## Handoff

- State the decision made, remaining assumptions, affected repositories, and the next implementation slice.
- Do not claim the design was approved unless the user approved it. Do not implement while a blocking product decision remains open unless the user explicitly chooses to proceed on a recorded assumption.
