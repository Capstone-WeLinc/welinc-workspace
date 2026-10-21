# Roles and users

> Source: BRD v1.1 (2026-05-26), the `UserRole` enum in `welinc-auth/prisma/schema.prisma`, and Jira epic WL-E1 (`VRMS-5`), checked 2026-10-22. Jira wins; the permission matrix itself is still to be written (WL-109).

## System roles

Roles are stored per system (`user_roles` / `UserRoleAssignment` with a `SystemType` of VRMS, VMMS or BMS), so one person can hold different roles in different subsystems.

| Role | Status | In VRMS they can | They can't |
|---|---|---|---|
| **Admin** (IT, office staff) | In code | Create and assign tickets, set priority, cancel, encode costs, transfer to outsourced shops and close them, approve transfer requests, manage users and lookup lists, export reports | |
| **Chief Mechanic** | Jira, confirmed (WL-104), not in code yet | View all tickets, verify or reject finished work (name is logged), handle outsourced closing | Exact permissions wait on the stakeholder flowchart |
| **Mechanic** | In code | See and update the status of their own tickets, upload vehicle photos and proof, request a transfer, put a ticket on hold for parts | Close or verify tickets, touch tickets not assigned to them, see costs, the driver verification flag or license photos |
| **Driver** | Jira, unanswered (WL-105) | Maybe record drop-off and pick-up at outsourced shops | Nothing to build until confirmed |

The code enum is `ADMIN, MECHANIC, CUSTOMER_SUPPORT, OPERATIONS`. Jira never mentions Operations or Customer Support, so they have no VRMS permissions; Chief Mechanic has to be added.

## Key rules

- Every action is checked on the server against one permission matrix (WL-109) and returns 403 when denied; the UI only hides what the server already blocks.
- Mechanics never see cost data, the driver verification flag, or license photos (BRD).
- Mechanics log in with OTP today. Admin OTP (WL-102) and reCAPTCHA on login (WL-103) are planned.
- The sidebar shows the logged-in user's role, taken from the token (WL-101).
- Assignment shows each mechanic's open-ticket count (WL-201). The BRD's "one active ticket per mechanic" rule is not in Jira; confirm it before enforcing it.
- Outsourced shops never get accounts.
- Deactivated accounts can't log in, but their records stay.

## Team

Capstone 2, BSIT 3-1, Group 14. VRMS is our subsystem; VMMS (maintenance) and BMS (booking) belong to other groups. Industry adviser: Ms. Ain Geuel Escober. Jira story owners are the roles Full-Stack Dev, UI / Mobile Dev and QA Tester. Individual people: see the Team Roles doc in Google Drive.
