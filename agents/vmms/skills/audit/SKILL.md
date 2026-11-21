---
name: audit
description: Review a VMMS repository or change for security, correctness, data handling, API compatibility, and maintainability. Use when asked to audit, review, or assess VMMS code.
---

# VMMS audit

Review the requested VMMS repository or change without modifying it unless the user also asks for fixes.

## Scope

- Read the repository's own instructions and relevant specs before judging behavior.
- Use a spec's `index.md` for the acceptance contract, `rationale.md` for approved decision context, and `verify.md` for known implementation and verification limits.
- Check `git status` and distinguish existing user changes from the requested review target.
- Stay inside the named VMMS repository. VMMS code also lives in the shared `welinc-mobile-vrms_vmms` app; limit changes there to VMMS screens and flows. Do not inspect secrets or edit shared services, other systems, or workspace files.
- Follow data across controller, authorization, service, persistence, and response boundaries where relevant.

## Review priorities

1. Authorization: verify role and system scoping, ownership/assignment checks, session revocation behavior, and access to legacy route aliases.
2. Sensitive data: check costs, personal data, tokens, uploaded files, and AI prompts in queries, logs, and responses.
3. Correctness: check state transitions, validation, concurrency, transactions, null/error handling, and stale analytics snapshots.
4. API/UI compatibility: check route, payload, pagination, and error shapes against callers and specs; ensure browser configuration contains no secrets.
5. Operations: inspect health checks, migration/build configuration, container behavior, and documented required variables.

## Findings

- Lead with confirmed defects, highest severity first.
- For each finding, give severity, exact file and line, the triggering condition, user or system impact, and a practical fix.
- Do not report speculative issues as confirmed. State what evidence or runtime check would resolve uncertainty.
- Summarize reviewed scope and any unverified areas. Do not claim tests or runtime behavior were verified unless they were actually run at the user's request.
