# Account screens on welinc-auth

Profile, activity, admin and deletion: what your app calls on welinc-auth. Every route goes through the gateway at `/auth` with the signed in person's own token (a service token gets 403 `WRONG_TOKEN_USE`). Exact inputs and errors: `http://localhost:3000/auth/docs`.

## Admin pages live in the portal

Account management lives in one place: the portal's admin section (`<portal>/admin`). A system admin there sees only their own system's people and gives only their own system's roles. Above them sit 1 to 3 **suite admins**, who manage every account but hold no system role, so they see none of your data. A suite admin who needs to look inside your system gives themselves one of your roles for 1 to 8 hours with a written reason, and your admins get an email.

Your app's "Users" menu item opens the portal in a new tab: `<VITE_PORTAL_URL>/admin/people?system=<SYS>`. Other deep links: `/admin/people/<id>?system=<SYS>` (one person) and `/admin/people/new?system=<SYS>` (add someone). Work data about a person (crew, mechanics) stays in your system; their account lives in the portal.

### The admin code answer

Every admin confirms each portal sign in with an emailed code. Until they do, any admin call (`/auth/activity`, sessions, deletion requests) answers **403 `ADMIN_CODE_REQUIRED`**. Show "Confirm your sign in in the portal" with a link to `<portal>/admin`; once the code is entered there, the same tokens work again with no new sign in.

Handle it once, in the code every request passes through (VMMS: `apiRequest` in `src/lib/api/httpClient.ts`; BMS: the response interceptor in `src/lib/api.ts`).

### Temporary roles in pick lists

A suite admin with temporary access looks like anyone holding that role. The directory names those codes: `DirectoryUser.temporaryRoles` lists the codes in `roles` that come from a live temporary grant (empty for everyone else). Wherever a role makes someone pickable for work (VMMS mechanics on a schedule, BMS drivers and helpers on a dispatch), leave out the codes in `temporaryRoles`, so a suite admin looking around is never given a job. When the grant ends, a `roles_changed` change removes the role.

### The central permission matrix (optional)

You may keep checking roles in your own code. If you want role to permission rules that a suite admin edits in the portal, do it the way VRMS does:

1. Your code still declares the permission keys and runs every check itself.
2. Add a `permissions` list (key, label, group, description, defaults per role, optional locked roles) to `welinc-auth/prisma/catalog/<system>.ts` through a pull request.
3. Your backend's client row gets the `permissions.read` scope (`welinc-auth/prisma/seeds/clients.seed.ts`).
4. Your backend polls `GET /auth/permissions/<SYS>` about every 60 s with `If-None-Match`, replaces its copy on a 200, keeps it on a failure, and refuses a copy that grants nothing to anyone. Permissions never go in the token.

The job to copy is `welinc-backend-vrms/src/auth/permissions/sync/`.

### What admins will notice

- An emailed code at each portal sign in. Locally, set `ADMIN_SIGN_IN_CODE=false` in welinc-auth's `.env`, or leave `SMTP_*` blank and read the code from the auth log.
- Adding an admin role, or acting on another admin's account, asks for their own password first.
- An email whenever someone gains or loses admin in their system, a suite admin steps in with temporary access, or the matrix is edited.
- Nobody can change their own roles or admin standing.

## Activity

welinc-auth records every sign in, session, emailed code and account change in one log. Your backend never reads it for itself; your web app calls it with the person's token.

| Route | Who | What it answers |
|---|---|---|
| `GET /auth/profile/activity` | anyone signed in | Their own events from every system |
| `GET /auth/activity` | your system's admin | Your system's feed: your system's events for anyone (former members too), plus account wide events of your current members. 60 calls a minute per admin |
| `GET /auth/activity/catalog` | anyone, no token | English labels for every category, type and reason. Cache it 5 minutes (it sends `Cache-Control` and an `ETag`). Never hard code labels |

**Paging.** Every list answers `{ data, nextCursor }`, newest first. Pass `nextCursor` back as `cursor`; `null` means the end. `limit` is 1 to 100 (default 50). There are no totals or page numbers, so a "Showing N of M" footer or numbered pages become a Show more button.

**Filters.** `category` and `type` take comma lists (at most 20 values). `from` and `to` are `YYYY-MM-DD` Manila days, both inclusive. The feed also takes `userId`, `q` (2 or more characters of name or email) and `address` (one exact IP). Bad values answer 400 `VALIDATION_FAILED`; a cursor you didn't get from these routes answers 400 `INVALID_CURSOR`.

### One event

```json
{
  "id": "…", "category": "SIGN_IN", "type": "SIGN_IN_FAILED", "reason": "WRONG_PASSWORD",
  "system": null, "sessionId": null, "client": null,
  "field": null, "oldValue": null, "newValue": null, "attemptsLeft": 3,
  "address": "112.198.0.1", "localNetwork": false,
  "device": "Chrome on Windows", "userAgent": "Mozilla/5.0 …",
  "country": "PH", "network": "Globe Telecom",
  "createdAt": "2026-11-12T01:19:53.301Z",
  "actor": { "kind": "SYSTEM" }
}
```

- `category` is `SIGN_IN`, `SESSION`, `CODE` or `ACCOUNT`; the catalog lists every `type`.
- `system` is the system the event belongs to; `null` means account wide.
- `actor.kind` is `SELF`, `ADMIN` or `SYSTEM` (nobody, such as an idle timeout). On the feed the actor also has `id` and `name`, and each event has `user: { id, name, email }`. On the person's own route an admin shows only as "An admin": use the catalog's `labelAdmin`.
- `country` and `network` are filled only when hosted. Locally every row is `localNetwork: true` (show "Local network"). Wherever you show a place, credit "IP data by DB-IP" linking to `https://db-ip.com`.

## Account deletion

1. The person types their password again. `POST /auth/profile/verify-password` answers a reauth token: 5 minutes, one use, same session only.
2. They send the request with it. Their account keeps working while it waits.
3. Any admin of a system they hold a role in approves or rejects it in the portal. A reject needs a note the person sees.
4. Approval closes the account at once: deleted, every session ended.
5. After 30 days (`ACCOUNT_ERASURE_GRACE_DAYS`) welinc-auth erases their name, email, phone and picture. Until then an admin can restore it; a restored account comes back turned off.

| Step | Call | Answer | Errors to handle |
|---|---|---|---|
| Recheck the password | `POST /auth/profile/verify-password` `{ password, purpose: "ACCOUNT_DELETION" }` | 200 `{ reauthToken, expiresAt }` | 400 `WRONG_PASSWORD` with `attemptsLeft`; 403 `ACCOUNT_LOCKED` (the 5th wrong try, same counter as sign in); 429 `RATE_LIMITED` |
| Ask for deletion | `POST /auth/profile/deletion-request` `{ reauthToken, reason? }` (up to 500 characters) | 201, the request with `status: "PENDING"` | 403 `REAUTH_REQUIRED` (recheck again); 409 `DELETION_PENDING`; 409 `LAST_ADMIN` |
| Show the state | `GET /auth/profile/deletion-request` | `{ request }`, the latest or `null` | none |
| Cancel | `DELETE /auth/profile/deletion-request` | 204 | none |

`request` is `{ id, status, reason, requestedAt, decidedAt, decisionNote, eraseAfter }`. Show `PENDING` with a Cancel button and `REJECTED` with `decisionNote` and an Ask again button; after `CANCELLED` or `RESTORED` the person may ask again.

The email change (`POST /auth/profile/email`) and password change (`PATCH /auth/profile/password`) answer a wrong current password the same way: 400 `WRONG_PASSWORD` with `attemptsLeft`, then 403 `ACCOUNT_LOCKED`.

Admins approve, reject and restore in the portal, so your app builds no admin deletion screens.

## After an erasure

The directory (`/auth/directory/*`) marks an erased person with `DirectoryUser.erased: true`, sent as one `updated` change; key on the flags (`deleted`, `isActive`, `erased`), never on the change type. Wherever you copied a name or email for that user id, rewrite it: names become `Deleted user` and emails `deleted-<id>@erased.invalid`. VRMS does it in `welinc-backend-vrms/src/modules/vrms/directory/erasure-rewrite.ts`. 

## Test accounts

- `suite.admin@welinc.com` (`admin1234`): the suite admin. No system roles, so the portal shows the no systems screen with **Admin** in the top bar.
- Your system's admins and the `multi.*` people: [seed-accounts.md](seed-accounts.md).
- Local mail is real when `SMTP_*` is set, so don't trigger codes, resets or deletion emails to real addresses in tests.
