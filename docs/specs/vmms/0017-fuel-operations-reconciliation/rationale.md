# Rationale — 0017 Fuel operations reconciliation and anomaly follow-up

## Context

VMMS scope marks the Module 5 fuel baseline done. It separately records pending
runtime, migration, workbook-matrix, and receipt-scanning pilot evidence in
specs 0005, 0006, and 0007. This proposal is not a substitute for those
completion checks.

The existing import flow already provides editable rows and per-row save
results. The anomaly flow already supports severity, notes, attachments,
acknowledgment, resolution, and staged notifications. A concise reconciliation
summary and visible anomaly age could improve operations without changing
those business rules.

## Forces

- Import totals must reflect persisted VMMS values, not workbook-provided
  totals.
- Partial row failures must remain visible and actionable.
- Import drafts are private to the creating Operations user; a shared history
  view would introduce new data-access and retention decisions.
- Existing anomaly escalation timing and permissions are approved behavior.
- The displayed anomaly age must not be mistaken for a newly defined response
  SLA.

## Options considered

1. **Transient import summary and informational anomaly age (recommended).**
   Reuse existing row outcomes and anomaly data. No new history, persistence,
   or alert policy.
2. **Persistent import reconciliation history.** Useful for later financial
   review, but adds retention, ownership, export, and audit decisions.
3. **New age-based anomaly alerts.** Could make follow-up more proactive, but
   changes an approved notification policy and requires recipient and
   deduplication decisions.

## Approved decision

The user approved Option 1 on 2026-11-27. Keep the summary within the current
owner's import workflow and do not add a separate history. Add persisted
`totalCost` to successful import-row results so the web summary totals use
VMMS values. Display anomaly age in elapsed 24-hour periods, matching the
existing escalation thresholds; the escalation job remains scheduled at
midnight Asia/Manila. Do not add new notifications or change escalation rules.

## Tradeoffs

- **Benefits:** clearer import outcomes and faster triage of long-open
  anomalies, with limited data and security impact.
- **Limitations:** no historical import-reconciliation report and no new SLA
  monitoring; existing backend results remain the source of truth.

## Approval record

- Summary retention: transient current-flow presentation only; no separate
  retained reconciliation history.
- Saved-row totals: backend adds the persisted VMMS `totalCost` per successful
  row; no new persistence or migration.
- Anomaly age: elapsed 24-hour periods from `createdAt`, matching existing
  thresholds; scheduled evaluation remains midnight Asia/Manila.
- Access: Admin/Operations retain web visibility; import results remain scoped
  to the owning Operations user; existing edit, acknowledgment, and resolution
  permissions are unchanged.
