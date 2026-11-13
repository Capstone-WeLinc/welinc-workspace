# Integration

Reference material the three systems share. Setting up and running the stack is in the workspace [README](../../README.md); the gateway is in [infra/gateway/](../../infra/gateway/README.md).

Big decisions become suite specs in `docs/specs/_root/` (the shared contract is [0001](../specs/_root/0001-shared-services-contract/index.md)). This folder holds the working material around them.

| File | What it is |
|---|---|
| [seed-accounts.md](seed-accounts.md) | Every seed login: the office accounts, multi system and broken state accounts, and how to reseed (spec 0006) |
| [web-login.md](web-login.md) | How a system's web app joins the shared web login: the session routes, the boot sequence, Switch system, sign out (spec 0007) |
| [account-activity.md](account-activity.md) | Moving VMMS and BMS activity screens onto welinc-auth's account events: routes, fields and labels (spec 0011) |
| [account-deletion.md](account-deletion.md) | Password recheck, the deletion request, admin review, restore and erasure; what the BMS and VMMS profile screens change (spec 0012) |
| [suite-admin.md](suite-admin.md) | The portal admin section and suite admins: the two new answers to handle, linking your menu item to the portal, deleting your user pages, temporary roles, the optional central matrix (spec 0013) |
| [move-vmms.md](move-vmms.md) | The VMMS checklist for moving onto the shared services: what to delete, what to copy from VRMS, the compose template, the checker and sign off (spec 0014) |
| [move-bms.md](move-bms.md) | The BMS checklist for the same move, plus the NestJS `bms-gateway`, drivers into dispatch, trucks from VMMS and the analytics database (spec 0014) |
| [fleet-api.md](fleet-api.md) | The VMMS fleet API BMS reads trucks and garages from: routes, fields, errors and the caching rule (spec 0014) |
| [shared-repo-changes.md](shared-repo-changes.md) | What changed in welinc-auth and welinc-web-portal this term, and what is planned |
