# Suite admin and the portal admin section

What the suite admin model (suite spec [0013](../specs/_root/0013-suite-admin-model/index.md), contract [0001](../specs/_root/0001-shared-services-contract/index.md) version 7) means for your system. Written for the VMMS and BMS groups. The routes in full are in contract section 10a; this page is what you change and in what order.

## What changed, in one paragraph

Account management now lives in one place: the admin section of the portal (`<portal>/admin`). A system admin there sees only their own system's people and gives only their own system's roles, with the same rules your pages enforce today. Above them sit 1 to 3 **suite admins**, who manage every account but hold no system role, so they see none of your data. When a suite admin really needs to look inside your system, they give themselves one of your roles for 1 to 8 hours with a written reason, and your admins get an email. Every admin also confirms each portal sign in with an emailed code. The role to permission matrix can live in welinc-auth too, but that part is optional for you.

## What you change

Everything below is a recommendation in the order we suggest. Steps 1 and 2 are the ones that stop your admins from getting stuck.

### 1. Handle the two new answers

| Answer | Where it comes from | What your app does |
|---|---|---|
| 403 `ADMIN_CODE_REQUIRED` | any admin call (`/auth/users*`, `/auth/activity`, deletion requests, sessions) while the admin's session hasn't passed the emailed code. A session from before version 7 is in this state | Show "Confirm your sign in in the portal" with a link to `<portal>/admin`. The portal asks for the code, and your existing tokens work again at once (no new sign in needed) |
| 200 `{ status: "SIGN_IN_CODE_REQUIRED", challengeId, email, resendAfter }` | `POST /auth/login`, for an admin with the right password. No cookie, no session yet | Only matters if your app calls `/auth/login` itself. Show the code screen and finish with `POST /auth/login/verify-email` `{ challengeId, code }`, exactly like `EMAIL_VERIFICATION_REQUIRED` (version 4) |

Where to put the first one, so every screen gets it:

- **VMMS** (`welinc-web-vmms`): `src/lib/api/httpClient.ts`, in `apiRequest` next to the 401 handling (around lines 143 to 165). The `ApiError` it throws already carries `data.code`.
- **BMS** (`welinc-web-bms`): `src/lib/api.ts`, in the response interceptor before the final `Promise.reject` (around line 53). The code is at `error.response.data.code`.

VRMS does the same (`welinc-web-vrms`, its Users page message for `ADMIN_CODE_REQUIRED`) if you want something to copy.

**BMS only:** `src/pages/auth/LogIn.tsx` posts to `/auth/login` itself and expects `accessToken` in the answer. That answer has carried no token since the shared login moved to the portal (contract section 7), and admins now get the code step too. The clean fix is the move in [web-login.md](web-login.md): your login page sends people to the portal and your backend runs the session routes. Until then, treat any answer with a `status` field as "finish signing in at the portal" and send the browser to `<portal>/login`.

### 2. Point your admin menu item at the portal

| | Menu item today | Becomes |
|---|---|---|
| VMMS | "User Management", `src/components/Sidebar/Sidebar.tsx` line 101, path `/users` | a link to `<VITE_PORTAL_URL>/admin/people?system=VMMS`, opened in a new tab |
| BMS | "User Accounts", `src/lib/auth.ts` line 137, path `/admin/users` | a link to `<VITE_PORTAL_URL>/admin/people?system=BMS`, opened in a new tab |

Deep links that work: `/admin/people?system=<SYS>` (the list), `/admin/people/<id>?system=<SYS>` (one person and every action on them), `/admin/people/new?system=<SYS>` (add someone, your system picked). An admin of one system lands straight on their people; an admin of two or more gets a system switcher.

The portal address: VMMS already reads `VITE_PORTAL_URL` (default `http://localhost:8000`) but its `.env.example` doesn't list it, so add it there. BMS has no portal variable yet: add `VITE_PORTAL_URL` to `.env.example` with the same local default (it is an address, never a secret).

### 3. Delete your account management pages

The portal does everything they do: create (including attaching an existing person), edit name, email and roles, deactivate, unlock, send a setup or reset code, see and end sessions, activity, delete, restore, and the deletion requests.

**VMMS:**
- Delete `src/pages/UserManagement/UserManagement.tsx` (614 lines), its route in `src/App.tsx` (lines 247 to 257) and the import (line 18).
- `src/lib/api/userService.ts` (re-exporting `vmmsApi.ts`) has one other caller: `src/pages/Maintenance Scheduling/CreateSchedule.tsx` calls `getUsers()` to pick people. Keep that helper for now. With S11 it should read people from your backend's directory copy (contract section 9) instead of `/auth/users`, which is for admins only and deprecated. Remove the other account helpers (`createUser`, `updateUser`, `updateUserRole`, `updateUserStatus`, `unlockUser`, `resetUserPassword`, `getLoginActivity`) once nothing calls them.

**BMS:**
- `src/pages/admin/UserManagement.tsx` (837 lines) does two jobs. The account half (calls in `src/lib/api/userService.ts` to `/auth/users*`) goes away. The crew half (drivers and helpers through `src/lib/api/crewService.ts`) is BMS work data, not sign in accounts, so **keep it**: move it to its own page (for example "Crew") before you delete the account half. Rule of thumb: anything about the work a person does stays in your system; anything about their account moves to the portal.
- Then remove the account route in `src/App.tsx` (lines 80 to 86) or point it at the crew page.

Your own profile pages stay: they use the person's routes (`/auth/profile*`, [account-deletion.md](account-deletion.md)), not the admin ones.

### 4. Skip temporary roles in pick lists

A suite admin with temporary access shows in your user lists and your directory feed like anyone holding that role. The directory now names those codes: `DirectoryUser.temporaryRoles` lists the codes in `roles` that come from a live temporary grant (empty for everyone else). Wherever a role makes someone pickable for work (VMMS mechanics on a schedule, BMS drivers and helpers on a dispatch), leave out the codes in `temporaryRoles`, so a suite admin looking around is never given a job. When the grant ends, a `roles_changed` change removes the role.

On the deprecated `/auth/users` list, the same people carry `temporaryUntil` (an ISO time). Nobody can edit that role; they end the grant from the portal instead (409 `TEMPORARY_ROLE` if they try).

### 5. The central permission matrix (optional, later)

You may keep checking roles in your own code. If you want role to permission rules that a suite admin edits centrally (VMMS said it plans to move to permission checks), this is how VRMS does it:

1. Your code still declares the permission keys and runs every check itself.
2. Add a `permissions` list (key, label, group, description, defaults per role, optional locked roles) to your catalog file `welinc-auth/prisma/catalog/<system>.ts` through a pull request; `npm run db:deploy` writes it.
3. Your backend's client row gets the `permissions.read` scope (`welinc-auth/prisma/seeds/clients.seed.ts`).
4. Your backend polls `GET /auth/permissions/<SYS>` about every 60 s with `If-None-Match`, replaces its cached copy on a 200, keeps the copy on a failure, and refuses a copy that grants nothing to anyone. Permissions never go in the token.

The VRMS job to copy is `welinc-backend-vrms/src/auth/permissions/sync/` (`permission-sync.job.ts` and `permission-sync.service.ts`). Suite admins edit the matrix in the portal's Permissions view, and your admins can read it there.

## What admins will notice

- Every admin, yours included, gets an emailed code at each portal sign in. Locally the seed addresses get no mail: set `ADMIN_SIGN_IN_CODE=false` in welinc-auth's `.env`, or leave `SMTP_*` blank and read the code from the auth log.
- Adding an admin role, and acting on another admin's account (email, codes, unlock, sessions), asks for your own password first.
- Your admins get an email whenever someone gains or loses admin in your system, a suite admin steps in with temporary access, or your matrix is edited.
- Nobody can change their own roles or admin standing.

## Test accounts

- `suite.admin@welinc.com` (`admin1234`), the suite admin: no system roles, so the portal shows the no systems screen with **Admin** in the top bar.
- Your system's admin accounts and the `multi.*` people in [seed-accounts.md](seed-accounts.md).
- Local mail is real when `SMTP_*` is set, so don't trigger codes to real addresses in tests.

## Checklist

- [ ] `ADMIN_CODE_REQUIRED` shows the portal link (step 1)
- [ ] BMS: no answer from `/auth/login` with a `status` leaves the person stuck (step 1)
- [ ] Menu item links to `<portal>/admin/people?system=<SYS>`, `VITE_PORTAL_URL` in `.env.example` (step 2)
- [ ] Account management pages and helpers deleted; BMS crew screens kept (step 3)
- [ ] Pick lists skip `temporaryRoles` (step 4)
