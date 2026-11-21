---
name: project-workflow
description: Plan, resume, or implement a VMMS feature or milestone across its backend, analytics, admin web, and VMMS mobile flows. Use when the task concerns project progress, a feature slice, or completing an in-progress VMMS change.
---

# VMMS project workflow

Use this workflow to move a requested VMMS slice to a clear, reviewable state.

## Find the right work

- Start from the user's requested outcome. Before deciding scope, inspect workspace `AGENTS.md`, the shared suite overview and relevant shared scope/specs, then inspect VMMS scope/specs, target repo instructions, and repo status. Reconcile both ownership layers before planning; preserve existing edits.
- Use `docs/scope/vmms/index.md` as the initial VMMS tracker; it is linked from the shared suite index. Do not infer project priorities from VRMS plans, stale handoffs, or code presence alone. If the task depends on an unrecorded priority or acceptance rule, make progress on independent work and ask for that decision.
- Use VMMS specs as three linked records: `index.md` is the build contract, `rationale.md` records context and decisions, and `verify.md` records acceptance-criteria-derived verification and remaining evidence.
- Check all likely VMMS surfaces: `welinc-backend-vmms`, `welinc-backend-vmms-analytics-ai`, `welinc-web-vmms`, and the VMMS flows in `welinc-mobile-vrms_vmms`.
- Treat shared scope/specs as authoritative for shared-service ownership. Login activity and account-change audit belong to shared services and use the portal audit UI; account creation, role assignment, lock/unlock, and deactivation are not VMMS implementation. Do not recommend duplicate VMMS audit or account-management UI. Identify only VMMS integration defects against the documented shared contract.

## Build a complete slice

- Prefer one small working flow across its required layers over unrelated partial edits. A feature may touch API and persistence, analytics, admin web, or mobile; include only the layers needed by the request.
- For VMMS web journeys requiring browser-level development or acceptance checks, use `../playwright/SKILL.md` with the feature's acceptance criteria and the repository's existing E2E setup.
- Work in one repository at a time, preserve existing edits, and keep shared auth, gateway, portal, and other-system code out of scope unless a spec authorizes a cross-repository change.
- Keep business rules in the owning service and enforce authorization at the server boundary. Treat analytics data as a derived view, not as the source of current assignment or session access.
- Follow the target repo's package scripts and code patterns. Do not introduce a library or alter a contract when the existing spec or caller does not support that choice.

## Close the work clearly

- Review the exact diff and report files changed, behavior delivered, and known limits.
- Keep implementation status distinct from verification status. Do not claim tests, builds, or live behavior were verified unless they were run at the user's request.
- Do not mark scope or spec items complete when only one repository or layer is finished.
