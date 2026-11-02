# Requirements (BRD detail)

> Source: BRD v1.1 (2026-05-26), Product Backlog v1.0 (VRMS001 to VRMS025, 2026-05-11) and Gap Analysis v1.0 (2026-05-11), all Capstone 1 docs in `docs/_source/` (git ignored). Distilled 2026-10-25. These are the field-level rules, limits and targets the other context files summarize away. **Jira wins** when it disagrees; the known overrides are listed first. Code wins on architecture.

## Where later decisions override the BRD

| BRD says | Now | Source |
|---|---|---|
| Head mechanic works under the Admin role | Separate **Chief Mechanic** role | Jira WL-104 |
| Four statuses, forward only, no reversal | Longer status list; verification can **reject back to In Progress** | Jira WL-200 |
| Cancel from any stage **without a reason**, irreversible | Cancellation with a reason (story missing in Jira) | Jira WL-213 |
| Outsourced mechanics and shop name are **free text** | Admin-managed **shop directory**; transfer with job order, close with receipt | Jira WL-402/404/405 |
| One active ticket per mechanic (auto-removed from the picker) | Not in Jira; the picker shows each mechanic's open-ticket count instead | Jira WL-201 |
| Shared monolith, shared database | Microservices, one database per service | Code; team lead 2026-10-22 |
| 8 sprints of 2 weeks | Jira's sprint plan | Jira |
| Mechanic required on every new ticket, driver typed by name | Mechanics are optional so a ticket starts Open and is assigned later; a driver is picked by search or added in place, keyed by the LTO license number; a truck can have one open ticket at a time | Spec 0016 |
| Driver details, license photo, cost vs income, daily and monthly reports | Not carried in Jira; treat as possibly dropped | [system-overview.md](system-overview.md) |
| Mechanics on a separate mobile app | Responsive web now, then one mobile app shared with VMMS | Scope, slice 7 (feature 48) |

The old backlog also contradicts the BRD on who fills the repair form: the BRD says Admin creates tickets, while VRMS002/009/010/012 say the mechanic submits it on mobile. Jira WL-201 decides.

## Process flow (BRD TO-BE)

1. A problem is reported to Admin, who creates a ticket and assigns one or more mechanics.
2. Status is **Pending**; the assigned mechanics are notified.
3. A mechanic starts work and sets **In Progress**, then fills vehicle system, root cause and repair description.
4. The mechanic marks it **Done**; the ticket becomes **For Verification** and Admin is notified.
5. The head mechanic physically tests the repair. Satisfactory: Admin marks **Completed**. Not satisfactory: Admin cancels.
6. Admin encodes parts and labor costs (only from For Verification on).
7. Completed and Cancelled tickets move to Repair History and lock.

## Scope

**Out of scope (BRD):** automated driver verification against government databases, booking system integration, preventive maintenance (VMMS), parts inventory and purchase orders, procurement and supplier management, full HR.

**Success criteria (BRD §8):** Admin creates, assigns and monitors tickets across all three garages; mechanics receive, update and mark Done; the workflow is enforced on both platforms; driver info captured on every ticket; costs encoded from For Verification; history searchable by Admin; daily and monthly reports generate on their own; alerts delivered; every edit audited; RBAC enforced on web and mobile; account changes take effect immediately.

## Module rules

IDs are the BRD's (`VR-` validation rule, `AC-` acceptance criterion) and the old backlog's (`VRMS0nn`). Response time targets assume normal network conditions.

### Login and accounts (Module I, VRMS001, VRMS025)

- Username and password. Invalid credentials show an error **within 1 s**; login completes **within 3 s** (VR-LM-02/03).
- Redirect to the role's own dashboard; permissions apply without a page refresh (VR-LM-04).
- **Inactivity auto logout** after a defined period (AC-LM-03). Period not specified.
- No restricted content is ever rendered before auth or for the wrong role (VR-LM-05, AC-LM-05).
- Admin only, web only: create (role Admin or Mechanic), edit name, username and role, deactivate and reactivate, list with role and Active/Inactive status (VR-LM-09).
- Deactivated accounts fail login in 100% of cases; their records stay (VR-LM-08).
- Account changes show on web and mobile immediately (VR-LM-07).

### Repair logging (Module II, VRMS002, 003, 009 to 013, 019, 020)

| Field | Rule |
|---|---|
| Repair number | Unique, generated on submit, format `REP-YYYYMMDD-XXXX`, never changes after go live |
| Created date and time | Auto (MM/DD/YYYY, HH:MM:SS in the BRD; the UI shows `YYYY-MM-DD` per `design.md`), not editable by anyone |
| Account type | Dropdown: Online, Corporate. Mandatory. Saved on the ticket (spec 0016) |
| Corporation | Dropdown, shown only for Corporate. Admin-managed lookup list; the ticket stores the name as a snapshot (spec 0016) |
| Plate number | Dropdown from Admin-managed list. Mandatory |
| Garage location | Dropdown, predefined. Mandatory (VR-RL-09) |
| Driver name | Text, required, **max 100** chars (VR-RL-05/07) |
| Driver license number | Text, required, format validated, unique identifier to prevent duplicate drivers (VR-RL-06). It is the driver key: an LTO number such as `A01-23-456789`, and a duplicate answers with the existing driver (spec 0016) |
| Odometer | Required, numeric (VR-RL-10) |
| isVerified | Per ticket, unverified by default, Admin sets it. **Never visible to mechanics** (VR-RL-08) |
| License photo | Optional, Admin only, web only, hidden from mechanics |
| Mechanics | Multi-select, grouped and labeled In-House vs Outsourced. Reassignment shows on both platforms within 3 s (VR-RL-12) |
| Shop name | Text, **max 100**, editable by mechanic and Admin. Every change logged (previous value, new value, who, when), Admin only view (VRMS020) |
| Priority | Set by Admin at creation; only Admin changes it (VR-RL-17) |
| Repair issues | At least 1, "Add Another Issue", each has vehicle system (dropdown), root cause (dropdown or typed), description (**max 500**). Must handle **10+** issues; shown in entry order (VR-RL-16/18/19) |
| Submit | Disabled on click until the server answers; on failure re-enabled with an error (VR-RL-21) |

- All dropdowns load **within 2 s** of opening the form; Admin list changes show live on both platforms (VR-RL-03/04).

### Current repair (Module III, VRMS004 to 006, 008, 014, 015, 021)

- Active view lists Pending and In Progress tickets; a mechanic sees their assigned ticket within 2 s.
- Vehicle status goes `UNDER_REPAIR` when a ticket is created and back to `AVAILABLE` on Completed or Cancelled. An unavailable truck is flagged red, updated within 3 s (VRMS004).
- Status changes reach every open session **within 3 s** (VR-CR-04). Users only see the transitions they are allowed (VR-CR-05).
- Optional **remarks** on every status update, both platforms.
- **Target due date:** optional, Admin sets it on web, read-only on mobile, not earlier than the creation date (VR-CR-12).
- **Duration:** shown in days and hours from creation; stops at Completed and records the final value to the hour (VR-CR-16/17).
- **Lock:** Completed and Cancelled tickets lock. Admin unlocks one edit with a reason (**max 1000** chars); it re-locks as soon as the edit saves (VR-CR-14/15). Cancelled locks immediately.
- **Audit:** every edit logs who, the new values and when, stored within 1 s (VR-CR-13).
- **Costs:** Admin only, web only, hidden from mechanics everywhere (VR-CR-07). Editable only from For Verification on (VR-CR-08). Labor is one total. Parts are either itemized, each line saved as added (within 1 s), or one lump sum. Total = parts + labor, computed within 1 s.
- **Notifications:** mechanic on new assignment, Admin on For Verification, both within 1 min (VR-CR-03, VRMS008).

### Repair history (Module IV, VRMS007, 016, 017)

- Completed and Cancelled in one view, chronological, status filter (Completed, Cancelled, both). Loads within 3 s.
- Admin, web only filters: repair number, mechanic name, driver license, plate number (also shows that truck's **total repair count**), status, garage (one at a time), external shop name. Results within 3 s.
- Garage and shop name are list columns and appear in the detail view.
- Detail shows garage, driver info, shop name and cost breakdown (AC-RH-05). Archived records keep all original data.

### Dashboard and reports (Module V, VRMS018, 022 to 024)

- **Repair frequency graph** per truck for the month, filterable by period, loads within 3 s. Frequently repaired trucks are flagged (threshold not defined).
- **Cost vs income** per truck for a period; trucks whose repair cost exceeds earnings are flagged non-profitable. Admin only. Needs truck income, which VRMS does not have.
- **Alerts** (in-app, within 1 min; SMS optional per VRMS024):
  - Pending for **more than 3 days**
  - High priority not moved to In Progress within a threshold (not defined)
  - Past its target due date (immediately)
- **Daily report** at a set time: trucks under repair, cancelled tickets, overdue tickets.
- **Monthly report** on the 1st: all repairs completed in the previous month.

## Gap analysis priorities

The ten gaps the system was justified against. High: repair logging (GAP-01), status tracking (02), an accessible tool after Excel and Google Forms failed (03), driver accountability (04), cost tracking (05), history (06), mechanic assignment (07), RBAC (10). Medium: notifications (08), reporting (09). GAP-03 also asks for **onboarding and training sessions** for Admin and mechanics before rollout.
