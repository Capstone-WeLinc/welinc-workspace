# Platform

Release, login security and the mechanic mobile app (Jira WL-E9, WL-E1, WL-E8). Back to [index](index.md).

## Release

Set up right after Slice 1 so every later slice demos from staging.

### 26. Hosting, CI/CD & environments · planned · needs a decision
WL-902 and WL-903. Staging and production with their own settings and databases, an automatic pipeline, and the go live. Decided so far: Vercel for frontends, Render for services (Jira not yet updated).
**Done when:** pushing to main deploys to staging, production deploys need approval, builds fail when tests fail, production has HTTPS and scheduled database backups, and a smoke test passes after deploy.
- [ ] Design it (spec): `/architect hosting & CI/CD`

### 27. Error monitoring · planned · needs a decision
Catch errors in production before users report them.
**Done when:** frontend and backend errors from staging and production reach one place with the release and user role attached, and no secrets or personal data are sent.
- [ ] Design it (spec): `/architect error monitoring`

### 52. Configurable settings & modules · planned · needs a decision · from spec 0007
Admin managed settings stored in the database instead of code constants, and VRMS modules that can be switched on or off (for example the AI features). Replaces `KNOWLEDGE_SETTINGS` from spec 0007 first.
**Done when:** an admin changes a threshold or turns a module off without a deploy, every change is audit logged, and code reads settings from one place.
- [ ] Design it (spec): `/architect configurable settings & modules`

## Slice 3: Login hardening

### 34. Admin OTP · planned · GA
WL-102. Admins confirm login with the same OTP mechanics use.
**Done when:** Admin pages are unreachable without a completed OTP step (checked on the server), codes expire after 5 minutes and work once, 5 wrong tries lock for 15 minutes, resend waits 60 seconds, and every OTP event is logged.
- [ ] Build it: `/develop admin OTP`

### 35. reCAPTCHA on login · planned · needs a decision · GA
WL-103. Block bots from guessing passwords.
**Done when:** the token is verified on the server before the password check, failures show a clear message, keys live only in environment variables per environment, and it works on a phone.
- [ ] Design it (spec): `/architect reCAPTCHA on login`

## Slice 7: Mechanic mobile app

After the web core loop. The responsive web stays the mechanic app until this ships.

### 48. Mechanic mobile app (React Native) · planned · needs a decision
WL-802. The mechanic side as a native app on the same API. Epic sized: split into smaller features once its spec exists.
**Done when:** a mechanic can log in with OTP, see their tickets, update status, upload photos and proof with the camera, get notifications and see history, from an installable build.
- [ ] Design it (spec): `/architect mechanic mobile app`

### 49. Offline save & sync · planned · needs a decision
WL-804. Mechanics keep working with no signal; changes sync when back online.
**Done when:** assigned tickets open offline, status changes, notes and photos queue locally with a pending count, sync is automatic, the conflict rule is recorded, and closing the app loses nothing.
- [ ] Design it (spec): `/architect offline save & sync`
