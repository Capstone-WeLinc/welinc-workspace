# VMMS on the shared services

**Status: done.** All four VMMS repos moved onto the shared login on Nov 17 and are merged into `development`. The checker passed (login 19 of 19, fleet 4 of 4), and so did the cross system checks.

## Still open

| What | Who |
|---|---|
| Analytics seed refuses `NODE_ENV=production` unless `SEED_ALLOW=staging` is set ([hosting.md](hosting.md#every-backend)) | VMMS |
| Work order and fuel attachments move to blob storage ([hosting.md](hosting.md#vmms-only)); tell the lead so your blob container exists first | VMMS, then the lead |
| Analytics CI is red: make it green | VMMS |
| Rerun `node scripts/check-system.mjs vmms` on `development` | the lead |

## How VMMS works now

| Before | Now |
|---|---|
| VMMS signed its own tokens (`JWT_SECRET`) | welinc-auth signs every token; VMMS checks them |
| `users`, `user_roles` and the other account tables | gone; a person is a welinc-auth id |
| VMMS `/auth/*` and `/users*` routes | gone; people sign in at the portal, admins manage them there |
| Token in `localStorage` | token in memory; refresh token in an HttpOnly cookie on `/vmms/session` |
| Mobile checked roles itself | `/auth/mobile/login` with `clientId: vmms-mobile` |
| BMS read trucks from the old database | BMS reads them from the [fleet API](fleet-api.md) |

- **Who uses what:** the web app admits Admin and Operations only. Mechanics and Chief Mechanics use the phone app. welinc-auth enforces this; don't check it yourself.
- **Your stack:** `docker-compose.vmms.yml` at the workspace root. Start it with `sh scripts/setup.sh vmms` (safe to run again).
- **Ports:** backend 3010, analytics 3011, web 8002, database 5438.
- **Before a pull request:** `node scripts/check-system.mjs vmms --static-only` scans your repos for old login code.

## Where to look

- Session routes and the web app's sign in: [web-login.md](web-login.md)
- Profile, activity, admin and deletion: [account-screens.md](account-screens.md)
- Test logins: [seed-accounts.md](seed-accounts.md)
- Every welinc-auth route: `http://localhost:3000/auth/docs`
