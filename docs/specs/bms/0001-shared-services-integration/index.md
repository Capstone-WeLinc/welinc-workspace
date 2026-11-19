# BMS shared-services integration

Implements suite spec 0014 and `docs/integration/move-bms.md` in BMS only.

## Contract

- Shared auth, portal, gateway, VRMS and VMMS source remain unchanged.
- BMS gateway owns `/bms/session/*` and explicitly proxies BMS business routes.
- All person-facing BMS services verify ES256 BMS access tokens and confirm sessions.
- Dispatch owns crew and dispatch metadata; VMMS owns vehicles and garages.
- Analytics owns its PostgreSQL read model and report storage.
- Web access tokens stay in memory. Accounts are managed through the portal.
- Public customer tracking and signed booking webhooks remain available.

## Delivery

Use Node 24, the compose service names and ports in the lead's guide, and fresh
BMS database volumes. Seeds are repeatable and use exact copies of the auth
people manifest. No legacy data or unrelated volumes are deleted.

Copy reference verification/session code and tests from the local VRMS checkout,
adapting only BMS names, imports and configuration. Existing business workflows
and BMS role checks remain in place.

## Verification

Build and test each BMS component, run the supplied static checker, exercise
portal sessions and BMS workflows, and retain evidence in the BMS checklist.
VMMS fleet live verification and the lead's cross-system sign-off remain pending
until their dependencies are available. No checklist item is marked verified
without supporting results.

## Checklist status and personal backup

At the client's request, update `docs/integration/move-bms.md` to record the
completed BMS implementation and local verification. Preserve its requirements
and leave unmet setup-command, PR, external runtime and lead-sign-off steps open.
This status update does not change a shared API or another group's source.

Create a private personal GitHub backup containing the three BMS source trees,
BMS Compose configuration, and integration documentation/context. Exclude local
environment values, keys, dependencies, generated output and runtime/test data.
The personal backup is separate from the suite's coordinated delivery PRs.
