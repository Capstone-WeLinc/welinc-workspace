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

## Proposed decision

Submit Option 1 for approval. Keep the summary within the owner's import
workflow, calculate totals from saved rows only, and display anomaly age using
the existing Asia/Manila escalation clock. Do not add new notifications or
change escalation rules.

## Tradeoffs

- **Benefits:** clearer import outcomes and faster triage of long-open
  anomalies, with limited data and security impact.
- **Limitations:** no historical import-reconciliation report and no new SLA
  monitoring; existing backend results remain the source of truth.

## Decisions awaiting approval

- Whether the import summary should remain transient, as recommended, or have
  a separately approved retention period.
- Whether anomaly age should be displayed as calendar days in Asia/Manila,
  matching escalation stages, or elapsed 24-hour periods.
- Confirmation that existing role visibility and draft ownership are retained.
