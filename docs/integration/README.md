# Integration

How VMMS and BMS work with the shared services (auth, portal, gateway). Setting up and running the stack is in the workspace [README](../../README.md).

| File | Open it for |
|---|---|
| [move-vmms.md](move-vmms.md) | VMMS: what's done, what's left |
| [move-bms.md](move-bms.md) | BMS: what's done, what's left |
| [hosting.md](hosting.md) | Running on staging: your apps, what to send the lead, deploying, the defense freeze |
| [links.md](links.md) | Every address: health checks, ports, databases, Azure, outside accounts |
| [seed-accounts.md](seed-accounts.md) | Test logins and passwords, and where the emailed codes go |
| [web-login.md](web-login.md) | The sign in flow your backend and web app copy from VRMS |
| [account-screens.md](account-screens.md) | Profile, activity, the portal admin section, account deletion |
| [fleet-api.md](fleet-api.md) | The trucks API: VMMS serves it, BMS reads it |

Every welinc-auth route with its exact inputs and errors: `http://localhost:3000/auth/docs` (or `https://staging-api.welinc.app/auth/docs`).
