# Integration

What VMMS and BMS need to move onto the shared services (auth, portal, gateway). Setting up and running the stack is in the workspace [README](../../README.md).

## Start here

| Your group | Read this, top to bottom |
|---|---|
| VMMS | [move-vmms.md](move-vmms.md) |
| BMS | [move-bms.md](move-bms.md) |

That checklist is the only page you need to read through. Each item links the exact section of a reference page below when it needs more detail, so open those only when an item sends you there.

## Reference

| File | Open it for |
|---|---|
| [web-login.md](web-login.md) | The session routes your backend copies from VRMS, the web app's boot sequence, Switch system and sign out |
| [account-screens.md](account-screens.md) | Your Users page moving to the portal, the admin code answer, temporary roles, profile and admin activity, account deletion, erasure |
| [fleet-api.md](fleet-api.md) | The trucks and garages API: VMMS serves it, BMS dispatch reads it |
| [seed-accounts.md](seed-accounts.md) | Every test login and password, and how your seed copies the shared people |
| [links.md](links.md) | Every address to open or check, per system: health routes, ports, databases, API docs, Azure resources, logs and outside accounts |
| [hosting.md](hosting.md) | Going online on Azure: your apps, what makes a service hosting ready, secrets, deploying |
| API docs: `/auth/docs` ([`openapi.json`](https://github.com/Capstone-WeLinc/welinc-auth/blob/development/docs/openapi.json)) | Every welinc-auth route with its exact inputs, replies and error codes, generated from the code. Served locally (`http://localhost:3000/auth/docs`) and on staging, never in production. You can paste an access token and try a request |

The rules behind all of this are in the shared services contract, [suite spec 0001](../specs/_root/0001-shared-services-contract/index.md); the move itself is [suite spec 0014](../specs/_root/0014-move-vmms-bms-shared-services/index.md). What changed in the shared repos this term is in [docs/context/shared-repo-changes.md](../context/shared-repo-changes.md).
