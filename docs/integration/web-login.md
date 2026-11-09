# Join the shared web login

How a system's web app signs people in through the shared portal, the way VRMS does today. Written for the VMMS and BMS groups, who move onto it in S11. The rules behind it are in the shared services contract, [spec 0001](../specs/_root/0001-shared-services-contract/index.md), sections 5 and 7; the launcher is [spec 0007](../specs/_root/0007-app-initiated-login-launcher/index.md).

## How it works in one paragraph

Your web app never sees a password, a login code or a refresh token. When someone opens your app without a session, your app sends them to your own backend, which starts a login at welinc-auth. welinc-auth sends them through the portal (the password form, or no form when they are already signed in) and back to your backend with a one time code. Your backend swaps the code for tokens, keeps the refresh token in an HttpOnly cookie, and hands your app a short lived access token that lives in memory only. The person lands on the exact address they first opened.

## What you need

| Piece | Where it is |
|---|---|
| Your client row | Already seeded in welinc-auth (`prisma/seeds/clients.seed.ts`): id `vmms` or `bms`, callback `<API_PUBLIC_URL>/<sys>/session/callback`, web address from `CLIENT_<ID>_WEB_ADDRESS` (local defaults `http://localhost:8002` and `http://localhost:8003`) |
| Your client key | Make one with `npm run keys:client -- <vmms or bms> <your backend .env> <welinc-auth .env>` in welinc-auth, then `npm run seed:clients`. The steps are in `welinc-auth/docs/keys.md` |
| The gateway route | `/vmms` and `/bms` arrive with S9. Until then, call your backend on its own port |
| Test accounts | [seed-accounts.md](seed-accounts.md): one, two and three system people (`vrms.admin@`, `multi.chief@`, `multi.lead@` and the `multi.*` rows that hold your system) |

## Backend: copy the VRMS session folder

Copy `welinc-backend-vrms/src/session/` into your backend and rename `vrms` to your prefix (`vmms` or `bms`): the routes, the cookie names and the client id.

| File | What it does |
|---|---|
| `session.controller.ts` | The six routes: `GET start`, `GET callback`, `POST refresh`, `POST activity`, `POST logout`, `GET status`, all under `/<sys>/session` |
| `auth-client.ts` | Calls welinc-auth's `/auth/token` with your signed client assertion, and reads the grant answer |
| `cookies.ts` | The refresh cookie `<sys>_rt` and the login state cookie `<sys>_login_<state prefix>` (HttpOnly, `SameSite=Lax`, path `/<sys>/session`, `__Secure-` when hosted) |
| `csrf.guard.ts` | Every cookie POST needs `Content-Type: application/json`, an `Origin` equal to your web address, and a same site `Sec-Fetch-Site` |
| `session.config.ts` | Your addresses, read from your env |

Keep the refresh answer's `user` object whole when you pass it to your app, and ignore fields in it you don't know. welinc-auth may add more, and `user.systems` (below) is one of them.

## Web app: the boot sequence

Copy the idea from `welinc-web-vrms/src/lib/session/` (`session.ts`, `bootGuard.ts`).

1. On load, call `POST /<sys>/session/refresh`. On 200, keep the access token in memory and run the app.
2. On 401, set a flag in `sessionStorage` (a timestamp, never a token) and send the whole page to `GET /<sys>/session/start?return=<path, query and hash>`. Your backend keeps only a return address on your own origin.
3. If the app loads again with that flag set and `refresh` still answers 401, clear the flag and send the browser to `<portal>/?error=LOGIN_FAILED`. This stops a loop.
4. Run one refresh at a time across tabs with a Web Lock named `<sys>-refresh`.
5. A 401 `SESSION_ENDED` while the app is in use (sign out elsewhere, idle cutoff, an admin) means: drop the token and go to `<portal>/login?reason=idle` or `<portal>/login` as VRMS does.

**Never send a signed out person to the bare `<portal>/`.** The portal sends someone with one system straight back into it, so that would loop. Go to your own `session/start`, or to `<portal>/?error=<code>` when something failed. The portal never forwards on its own while an `error` is in the address.

## Web app: Switch system and sign out

- **Switch system:** show it only when `user.systems` (from the refresh answer) has two or more entries. It opens `<portal>/?from=<SYS>` in the same tab, where the launcher lists the person's systems and tags yours "You're here". A missing `user.systems` counts as an empty list. VRMS's version is `welinc-web-vrms/src/lib/session/switchSystem.ts` and `src/components/layout/useShellActions.ts`.
- **Sign out:** `POST /<sys>/session/logout`, then send the browser to `<portal>/login?reason=logout`. That ends the shared session, so every other app signs out within 30 seconds too.

## Remove the old handoff

Delete any code that reads `?token=` from the address, or that keeps a token in `localStorage`. With this login no token ever appears in a URL.

## Test it

Sign in with the seed accounts and check each one:

1. **One system** (a plain `vmms.*` or `bms.*` account): open a deep link in your app while signed out, sign in at the portal, and land on that exact address. Switch system is hidden. Opening the portal again sends you straight back.
2. **Two systems** (`multi.chief@`, `multi.admin@` or `multi.mixed@` when they hold your system): the same deep link test, then Switch system opens the launcher with your card tagged "You're here".
3. **Three systems** (`multi.lead@`): the launcher shows BMS, VMMS and VRMS in that order.
4. **Sign out** in your app, then open another app: it asks for the password.

Local welinc-auth mail flows send real email, so don't use forgot password with seed accounts while testing.
