# Crew edit layout and Analytics & AI label

Status: pushed, not yet in a pull request. Web branch: `BMS/crew-edit-layout-and-analytics-label` (into `development`); workspace branch: `docs/bms-crew-edit-layout-and-analytics-label` (into `main`).

Decision history: [rationale.md](rationale.md). Review checklist: [verify.md](verify.md).

Touches `welinc-web-bms` only (Edit driver / Edit helper modal, admin sidebar label, ecosystem screens test). No API, database or route changes.

## 1. Edit driver / Edit helper: Status moves into the Profile card

**Before:** Account (read-only name, email, contact) → Work details (Status) → License (driver only) → Emergency contact.

**Now:**

- **Profile** card (renamed from Account): Full name; Email and Contact number (read-only, "Edit in portal" link kept); then, under a divider, **Status**.
- The separate **Work details** card is gone.
- Driver: Profile → License → Emergency contact.
- Helper: Profile → Emergency contact.
- Validation, saving and the fields themselves are unchanged.

## 2. Sidebar: "Analytics & Reports" renamed "Analytics & AI"

- Admin nav item for `/admin/reports` now reads **Analytics & AI**. The path and icon are unchanged.
- `tests/ecosystem-screens.spec.ts` updated to the new label.
