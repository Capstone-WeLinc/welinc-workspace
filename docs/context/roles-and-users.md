# Roles and users

> Source: BRD v1.1 (2026-05-26), the `UserRole` enum in `welinc-auth/prisma/schema.prisma`, and Jira epic WL-E1 (`VRMS-5`), checked 2026-10-22, updated 2026-10-29 for the permission matrix (spec 0011, WL-109). Jira wins.

## System roles

Roles are stored per system (`user_roles` / `UserRoleAssignment` with a `SystemType` of VRMS, VMMS or BMS), so one person can hold different roles in different subsystems.

| Role | Status | In VRMS they can | They can't |
|---|---|---|---|
| **Admin** (IT, office staff) | In code | Create and assign tickets, set priority, cancel, encode costs, transfer to outsourced shops and close them, approve transfer requests, manage users and lookup lists, export reports | |
| **Chief Mechanic** | In code since spec 0007 (WL-104); sees every ticket since spec 0011 | See every ticket (read only on other mechanics' tickets, no costs), work the tickets assigned to them, edit the knowledge base. Planned: verify or reject finished work (name is logged) and handle outsourced closing, with features 17 and 23 | Create tickets, close or cancel, see costs, manage users; further rights wait on the stakeholder flowchart |
| **Mechanic** | In code | See and update the status of their own tickets, upload vehicle photos and proof, request a transfer, put a ticket on hold for parts | Close or verify tickets, touch tickets not assigned to them, see costs, the driver verification flag or license photos |
| **Driver** | Jira, unanswered (WL-105) | Maybe record drop-off and pick-up at outsourced shops | Nothing to build until confirmed |

The code enum is `ADMIN, MECHANIC, CHIEF_MECHANIC, CUSTOMER_SUPPORT, OPERATIONS` (Chief Mechanic added by spec 0007). Jira never mentions Operations or Customer Support, so they have no VRMS permissions. Which role may do what is no longer fixed in code: the permission catalog (`welinc-backend-vrms/src/auth/permissions/catalog.ts`, 16 keys) holds the defaults and locks, and the `role_permissions` table holds each role's on or off. An Admin changes them through `PATCH /vrms/permissions` (the Settings screen comes with feature 52). Rights are the union over every VRMS role a person holds. Verification ownership for the Chief comes with scope features 17 and 23.

## Key rules

- Every action is checked on the server against one permission matrix (WL-109, spec 0011) and returns 403 when denied; the UI only hides what the server already blocks. `users.manage` and `permissions.manage` are locked to Admin so nobody can lock themselves out, and every matrix change is logged with who made it.
- Mechanics never see cost data, the driver verification flag, or license photos (BRD).
- Mechanics log in with OTP today. Admin OTP (WL-102) and reCAPTCHA on login (WL-103) are planned.
- The sidebar shows the logged-in user's role, taken from the token (WL-101).
- Assignment shows each mechanic's open-ticket count (WL-201). The BRD's "one active ticket per mechanic" rule is not in Jira; confirm it before enforcing it.
- Outsourced shops never get accounts.
- Deactivated accounts can't log in, but their records stay.

## Team

Capstone 2, BSIT 3-1, Group 14. VRMS is our subsystem; VMMS (maintenance) and BMS (booking) belong to other groups. Industry adviser: Ms. Ain Geuel Escober. Jira story owners are the roles Full-Stack Dev, UI / Mobile Dev and QA Tester. Individual people: see the Team Roles doc in Google Drive.
