# Glossary

> Distilled 2026-10-22 from the BRD, the Prisma schemas, and checked against Jira (project `VRMS`) the same day. Enum values marked *code* come from the schema; *Jira* means planned in the backlog. Jira wins when they disagree; update this file (or let `/sync` flag it) when either changes.

| Term | Meaning |
|---|---|
| **VRMS** | Vehicle Repair Management System. Unplanned repairs and breakdowns. Our subsystem. |
| **VMMS** | Vehicle Maintenance Management System. Planned, preventive maintenance. Another group. |
| **BMS** | Booking Management System. Bookings, trips and job orders. Another group. |
| **Portal** | The shared login and launcher (`welinc-web-portal`) that sends users into each subsystem. |
| **WL-xxx** | Story IDs from the stakeholder backlog, kept in Jira summaries (`[WL-201] …`). Jira keys are `VRMS-n`. Epics are `WL-E1`…`WL-E11`. |
| **Repair ticket** | One repair job on one truck. Number format `REP-YYYYMMDD-XXXX`, created automatically and never changed after go live. |
| **Repair issue** | One problem inside a ticket (vehicle system + root cause + description). A ticket has one or more. |
| **Vehicle system** | The part of the truck affected (engine, brakes, transmission…). Admin managed list. |
| **Root cause** | Why it broke (wear and tear, accident damage…). Admin managed list. |
| **Common issue** | *Jira (WL-702/704).* Admin-managed knowledge base entry (category, description template, suggested priority and fix). Mechanics pick one instead of typing. |
| **Ticket status** | *Code:* `PENDING → IN_PROGRESS → FOR_VERIFICATION → COMPLETED`, plus `CANCELLED`. *Jira (WL-200, names not final):* Open, Assigned, In Progress, On Hold – No Parts, For Verification, Outsourced, Completed/Closed, Cancelled, with a role-based transition table. Verification can reject back to In Progress. |
| **For Verification** | The mechanic finished and uploaded proof; the Chief Mechanic (or Admin) verifies → Closed, or rejects with a comment → In Progress. The verifier is stored (`verified_by`, `verified_at`). |
| **Proof of completion** | *Jira (WL-211).* At least one photo or PDF required before a ticket can be marked done. For outsourced work, the shop's receipt counts. |
| **On Hold – No Parts** | *Jira (WL-208, unsure).* Mechanic pauses a ticket for missing parts with a reason; someone verifies it. Hold time is tracked separately. |
| **Repair history** | Closed tickets, plus a clickable timeline per ticket built from the audit log (WL-205/219). BRD rule: closed tickets are locked; Admin unlocks one edit with a logged reason. |
| **Audit log** | Already exists on the admin side. Jira (WL-219) extends it to every ticket event: actor, role, time, before/after, note. Not editable. |
| **Vehicle status** | *Code:* `AVAILABLE`, `UNDER_REPAIR`, `UNDER_MAINTENANCE`, shared with VMMS; `UNDER_REPAIR` wins a conflict. *Jira (WL-501, unanswered):* set automatically from the ticket, plus a manual toggle with a reason. |
| **In house / Outsourced** | Who does the repair. Business rule (WL-401, confirmed): try in-house first; outsourcing needs a justification. In-house mechanics are records in `mechanics`. |
| **Outsourced shop** | *Jira (WL-405).* An entry in the Admin-managed shop directory. Shops get no system access: Admin or Chief Mechanic records the transfer, prints a job order, then uploads the receipt and total cost to close it (WL-404/402). Replaces the old free-text shop name. |
| **Driver verification** | `isVerified` flag on the ticket's driver, set by Admin. Hidden from mechanics. (BRD; not in Jira.) |
| **Lump sum** | Parts cost entered as one total instead of itemized parts. (BRD.) |
| **Total cost** | Parts cost + labor cost, computed automatically. Outsourced cost comes from the receipt. |
| **Account type** | On a ticket: Online or Corporate customer (Corporate needs a corporation). The code's `AccountType` enum means something else: `IN_HOUSE` / `OUTSOURCED`. |
