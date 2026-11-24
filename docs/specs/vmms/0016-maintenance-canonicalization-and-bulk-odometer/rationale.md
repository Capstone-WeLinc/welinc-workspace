# Rationale — 0016 Maintenance canonicalization, navigation alignment, and bulk odometer API

## Context

Recent VMMS web fixes addressed several UI/behavior issues in isolation (drill-through search prefill, TIME overdue display preferring `targetDueDate`, navigation consistency, and a client-side bulk odometer UX). These improved usability but left known gaps: notification deep-links used an unsupported `scheduleId` query param, schedule due/status derivation could diverge between frontend recomputation and backend-stored/computed values, and bulk manual odometer updates issued one request per vehicle without a dedicated JSON batch contract.

The user requested fixing these first, with backend work allowed, in spec-first order across VMMS-owned components.

## Forces

- **Consistency vs. workflow integrity:** derived states (Pending/Due/Overdue) must align with calendar/odometer rules, but workflow/approval states (In Progress/Done/Completed/Cancelled, verification/return states) and audit history must not be corrupted by naive recomputation.
- **Compatibility:** existing clients, stored data, tests, and sync/read-model consumers depend on current fields/semantics; additive fields and careful normalization are safer than breaking renames.
- **Spec-first and repo boundaries:** API/behavior changes require VMMS spec documentation and should be implemented one repo at a time; shared services and other systems remain untouched.
- **Partial failure vs. atomicity:** current bulk UI behavior is effectively partial-success per vehicle; a JSON bulk endpoint should define semantics explicitly (per-item results) and not silently change user expectations.
- **Performance/operability:** a batch endpoint reduces request fan-out but must enforce the same validation/authz rules as single updates.

## Options considered

1. **Frontend-only fixes only**
   - Pros: smallest change set, no contract risk.
   - Cons: leaves canonical status/due divergence and lacks efficient/contracted bulk JSON updates; server and other clients remain inconsistent.

2. **Full backend-only canonicalization and new endpoints without frontend adaptation**
   - Pros: centralizes logic.
   - Cons: UI may not consume new fields; user-visible issues (deep-links, bulk UX/result handling) persist.

3. **Spec-first, incremental cross-layer alignment (chosen)**
   - Pros: documents decisions, fixes navigation immediately, adds canonical/computed response fields and a JSON bulk contract with per-item results, and wires frontend to prefer canonical data while keeping compatibility fallbacks.
   - Cons: more coordination and verification effort; requires careful regression testing across trigger types and roles.

## Chosen option

Option 3. Implement in order: (a) spec + navigation/deep-link alignment, (b) core backend canonical due/status exposure/normalization with tests, (c) frontend consumption/mapping updates, (d) bulk odometer JSON endpoint in core backend with tests, (e) frontend bulk wiring and UX/result handling, (f) verification and scope/spec reconciliation.

## Smaller decisions

- **Deep-link identifier:** prefer front-end business identifiers (`workOrderNumber`, `title`, `plate`) when available; allow schedule id as a search value only as a compatibility fallback because existing page search can match it.
- **TIME due precedence:** `targetDueDate` takes precedence; computed `startReferenceDate + interval` is fallback. This matches existing backend helpers and the frontend fix already applied.
- **Bulk endpoint semantics:** partial success with per-item outcomes (not transactional all-or-nothing) to align with current UX and avoid rejecting whole batches for one bad row; clients must display failures clearly.
- **No DB migration by default:** prefer derived/serialized response fields and existing columns; introduce schema changes only if strictly necessary and justified.
- **Analytics follow-up:** treat `welinc-backend-vmms-analytics-ai` as out of scope for this slice unless direct contract breakage is found; record follow-up if sync/derived status needs alignment.
