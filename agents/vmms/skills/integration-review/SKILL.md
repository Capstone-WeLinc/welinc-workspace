---
name: integration-review
description: Review VMMS feature flows and contracts across the VMMS API, analytics, web, and VMMS mobile surfaces, including documented dependencies on shared services or other systems.
---

# VMMS integration review

Check whether the requested VMMS flow works across its actual producers and consumers without crossing service ownership boundaries.

## Review the path

- Read relevant VMMS specs and target repository instructions, then identify the caller, endpoint, authorization, business logic, persistence, response, and UI handling for the flow.
- Use the spec's `index.md` as the contract, `rationale.md` for settled design decisions, and `verify.md` for acceptance evidence still missing.
- Review only the repositories and surfaces needed for the requested change. For `welinc-mobile-vrms_vmms`, limit findings and any authorized edits to VMMS behavior.
- Compare route, HTTP method, request/response shape, identifiers, enums, pagination, validation, and error handling at both ends. Check compatibility with existing callers and documented contracts.
- Confirm shared authentication and roles are consumed from `welinc-auth`; do not introduce a second identity store or bypass server-side authorization.
- Confirm inter-system data is exchanged through documented APIs or gateway routes, never by reading another system's database. Keep analytics as a derived consumer of core VMMS data.
- Check lifecycle and failure cases that cross layers: retries, duplicate submissions, stale state, partial failure, offline mobile sync, and refresh behavior when relevant to the feature.

## Report or fix

- When asked to review, report confirmed findings first with severity, exact repo/path/line, reproduction or triggering condition, impact, and a concrete correction. Label contract assumptions and unverified runtime behavior clearly.
- When asked to fix, change only the authorized VMMS surface and preserve unrelated work. A cross-repository or shared-contract change requires a spec first and must follow workspace ownership rules.
- Do not contact other teams, deploy, publish, or claim runtime integration was exercised unless that action was requested and actually performed.
