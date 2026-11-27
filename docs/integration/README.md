# Integration

How VMMS and BMS work with the shared services (auth, portal, gateway). Setting up and running the stack is in the workspace [README](../../README.md).

| File | Open it for |
|---|---|
| [hosting.md](hosting.md) | Running on staging: your apps, what to send the lead, deploying, the defense freeze |
| [links.md](links.md) | Every address: health checks, ports, databases, Azure, outside accounts |
| [seed-accounts.md](seed-accounts.md) | Test logins and passwords, and where the emailed codes go |
| [web-login.md](web-login.md) | The sign in flow your backend and web app copy from VRMS |
| [account-screens.md](account-screens.md) | Profile, activity, the portal admin section, account deletion |
| [fleet-api.md](fleet-api.md) | The trucks API: VMMS serves it, BMS reads it |
| [bms-integration.md](bms-integration.md) | BMS with VMMS and VRMS: the fleet list and truck availability, maintenance dates that avoid booked trips, repair dates and Job Orders, and each group's checklist |
| [bms-vmms-operational-handoffs.md](bms-vmms-operational-handoffs.md) |BMS-to-VMMS handoffs for completed-trip odometer evidence, utilization summaries, and delivery fuel purchases |
| [repair-integration.md](repair-integration.md) | Repairs across systems: VMMS referrals into VRMS, repair status back to VMMS, repair impact and expedite requests with BMS, the retry rule, and the asks |
| [error-monitoring.md](error-monitoring.md) | Optional: reporting your crashes and errors to Sentry, with the gateway tunnel for web apps |
| [security-checks.md](security-checks.md) | The weekly ZAP scan of your web app, the security headers to copy, secret scanning |

Every welinc-auth route with its exact inputs and errors: `http://localhost:3000/auth/docs` (or `https://staging-api.welinc.app/auth/docs`).
