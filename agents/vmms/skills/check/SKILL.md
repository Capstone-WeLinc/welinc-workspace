---
name: check
description: Verify a requested VMMS change against its acceptance criteria or review its diff for defects before handoff.
---

# VMMS change check

Use one of two modes, based on the user's request.

## Verify behavior

- Read the governing VMMS spec and list each acceptance criterion and required surface.
- Use `docs/specs/vmms/NNNN-title/verify.md` as the verification checklist and `rationale.md` to understand settled product decisions that may affect interpretation.
- Read repository instructions and identify the documented way to run the affected API, web, analytics, or VMMS mobile flow.
- Exercise observable behavior, including relevant role permissions, validation, failure states, and persistence. Check every named surface; passing unit tests alone does not prove an end-to-end flow.
- Run tests or launch services only when the user requested verification. Avoid production data and do not expose secrets.
- Report pass, fail, or not verified per criterion, with evidence and environment limits. Do not edit application code in this mode.

## Review the change

- Inspect the requested diff, repository status, relevant spec, callers, and authorization/data boundaries.
- Lead with confirmed findings, highest severity first. Include repository path and line, trigger, impact, and a specific correction. Mark questions and runtime-only risks as unverified.
- Write a durable review only if requested, under VMMS-owned `docs/reviews/vmms/`. Never edit code during review mode.

If the user has not asked to verify or review and the intended mode is unclear, ask which one they want before running checks.
