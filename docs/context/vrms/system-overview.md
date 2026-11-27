# System overview

> Source: BRD v1.1, System Description, the code in this workspace, and Jira project `VRMS`, checked 2026-10-22. The **code is the source of truth for architecture**; **Jira** is the source of truth for what's planned. The architecture diagrams in Google Drive are out of date (see Decisions).

## What VRMS does

Admin creates a repair ticket and assigns it, in-house first. Mechanics update it from their phones with photos and proof. The Chief Mechanic verifies the work. Repairs nobody in-house can do go to an outsourced shop and are closed with its receipt. Every event lands in the audit log, which feeds the history timeline, notifications and reports.

## Modules

These match the Jira epics. Story-level detail and status are in Jira; every story is To Do as of 2026-10-22.

| Epic | Covers |
|---|---|
| WL-E1 Roles & Access | RBAC matrix, Chief Mechanic role, Admin OTP, reCAPTCHA, role badge; Driver role and Admin override are unanswered |
| WL-E2 Ticket / Repair Workflow | Status state machine, new repair form and assignment, mechanic status updates, auto-fill, uploads (photos, proof), verification, audit log, transfer requests, history timeline, no-parts hold, deadlines |
| WL-E3 Notifications & Escalation | In-app notifications, unread badge, stuck-in-pending alerts, stale escalation (unanswered) |
| WL-E4 Outsourced Repairs | In-house-first rule, shop directory, transfer with a printable job order, receipt-based closing, possible management approval |
| WL-E5 Vehicle Management | Vehicle unavailable while under repair (unanswered) |
| WL-E6 Reports | One Reports module with filters and CSV/Excel export; specific report types not defined yet |
| WL-E7 Emerging Tech / AI | Common-issues knowledge base and picker; AI suggestions are optional |
| WL-E8 Mobile App & Platform | Mechanic mobile experience, offline save and sync |
| WL-E9 Deployment / Infra | Hosting, CI/CD, staging and production |
| WL-E10 Documentation, WL-E11 QA & UAT | Manuals per role, page numbers, sprint demos, regression and security testing |

BRD items Jira doesn't carry: cost-vs-income per truck, driver details and verification, license photos, daily and monthly reports. Treat them as possibly dropped until Jira says otherwise.

## How it's built (as of the code today)

Microservices, one repo each, behind an Nginx gateway on port 3000. See the table in the root `AGENTS.md` for repos and ports.

```
browser ─► web-portal (:8000, login) ─► web-vrms (:8001)
                │                           │
                └────────► gateway :3000 ◄──┘
                     /auth ─► welinc-auth (:3001) ─► Postgres (auth)
                     /vrms ─► backend-vrms (:3002, includes AI and analytics) ─► Postgres (vrms)
```

Trucks and garages belong to VMMS; VRMS keeps a read only copy synced from VMMS (`Vehicle.vmmsVehicleId`, spec 0029 child 0001). VRMS owns its repair tickets and their history.

## Decisions (confirmed by the team lead, 2026-10-22)

- **Architecture is microservices**, as in the code. The BRD and diagrams that show a modular monolith are outdated.
- **Mechanic mobile app: one app shared with VMMS** (decided 2026-10-29). VMMS already has a mobile app; VRMS adds its repair screens to it. Its platform and repo are settled after the integration meeting (scope feature 56). Jira still lists this as an open platform decision (WL-801, ticket missing). Update Jira.
- **Hosting: Azure** (Static Web Apps, Container Apps, one shared PostgreSQL server) with GitHub Actions, per spec 0008; this replaced the earlier Vercel and Render plan. Email goes through Brevo from `noreply@welinc.app` when hosted; SMS is dropped as not worth the cost. Staging went live on 2026-11-19; production exists as code only and is never run live (spec 0008 AC-24). Jira still says "Vercel vs Netlify" (WL-901, ticket missing). Update Jira. License photo storage may be dropped.
- **AI and analytics is a Capstone 2 addition** not covered by BRD v1.1. It lives in `welinc-backend-vrms` (`src/modules/ai` and `src/modules/analytics`), not the old separate analytics repo, and stays optional.

## Still open

1. **AI provider.** The code uses Gemini (behind an `AiProvider` adapter) plus pgvector, inside `welinc-backend-vrms` (spec 0013 retired the Python service and its MongoDB, Redis and DuckDB stores); Jira WL-E7 says "optional local AI (Ollama)". Decide the provider with `/architect` (scope feature in `reports-ai.md`), then align Jira.
2. **Missing Jira tickets.** Stories depend on WL-106 (role-per-process flowchart), WL-213 (cancellation with reason), WL-701/703 (AI), WL-801 (platform) and WL-901 (hosting), but none of them exist in Jira.
3. **Status names.** WL-200 must fix the final list before the migration from the code's four statuses.
4. **Schema copy.** Resolved: `welinc-backend-vrms/prisma/schema.prisma` no longer defines `Booking` or maintenance models.
5. **Stakeholder questions** are collected in WL-1101: Driver role, Admin override, stuck threshold, escalation, no-parts verifier, fix-time targets, management approval, vehicle disable flow, report types.
6. **Sprints.** Jira stories carry a planned sprint (1 to 7+); Jira holds the current plan, not the BRD's 8 sprints.
