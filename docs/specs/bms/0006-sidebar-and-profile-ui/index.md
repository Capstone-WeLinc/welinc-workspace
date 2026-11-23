# Sidebar and profile UI

Status: built, not yet committed. Branch `BMS/sidebar-and-profile-ui` in
`welinc-web-bms`, into `development`.

Three front-end changes, using the VMMS front end (`welinc-web-vmms`) as the
reference. Touches only `welinc-web-bms`. No backend change, no database
migrations, and no change to shared auth, portal or the suite gateway.
`welinc-web-vmms` was only read, never changed.

## 1. Sidebar follows the VMMS sidebar

File: `src/components/Sidebar.tsx`

### What it does
- **Look:** navy `#020849` with a `#111a62` edge and a soft shadow. The active
  link is a yellow `#f4c400` pill with dark text and a glow. Other links are
  `#9ba4db` and turn white on hover.
- **Width:** an 80px icon rail that widens to 280px on hover (was 256px). Labels
  fade and slide in as it opens. It still floats over the page, so the page
  never moves.
- **Header:** the logo in a yellow-edged square, "WeLinc Logistics" and
  "Booking Management (BMS)".
- **Sections:** small yellow uppercase headings with thin lines between them.
  - Only one section is open at a time. Opening one closes the other.
  - Opening and closing is animated.
  - When the page changes, the section holding that page opens on its own.
    Sections opened or closed by hand stay that way until the page changes.
  - On the narrow rail, a yellow dot marks a closed section that holds the
    current page.
- **Footer**, in this order: notifications, profile (initials in a rounded
  yellow square, name and role), Switch system, and Sign Out in red.

### Unchanged
- The menu entries and who sees them still come from `getNavItems(role)`.
- Links to other sites (such as User Accounts in the portal) still open in a new
  tab.
- Each role's profile page (`getRoleProfile`), the switch-system rule and sign
  out work as before.

### Removed
- The round highlight behind group icons and the different icon styles for
  Administrator, Customer Service and Operations. Every role now gets the same
  look.

## 2. Notification pop-up opens centred over the page

File: `src/components/shared/NotificationBell.tsx`

### Problem
The panel used to open beside the sidebar and was positioned from the
sidebar's edge. Inside the restyled sidebar, it could be clipped and not show
at all. The trigger was a blur effect on the sidebar footer: a blur makes the
browser position "fixed" children inside the footer instead of the window.

### What it does
- Clicking the bell opens the panel **centred over the page**, on a dimmed
  background. It is drawn on `<body>` (a React portal), so the sidebar can't
  clip it.
- Clicking the dimmed background or pressing Esc closes it.
- The sidebar footer no longer uses the blur.

### Unchanged
- The look of the bell button and the panel: coloured icons per notification
  type, "n new", **Mark all read**, "You're all caught up", and
  **View all n notifications**.
- How notifications are fetched, stored per account and role, and shown as
  toasts.

### Removed
- Positioning the panel from the sidebar's edge.
- Closing on any click outside the bell. The dimmed background handles this now.

## 3. Profile page is the VMMS profile page

Files: `src/components/ProfilePage.tsx`, and the three wrappers
`src/pages/admin/AdminProfile.tsx`, `src/pages/customerservice/CsProfile.tsx`,
`src/pages/operations/OperationsProfile.tsx`

### What it does
The page is a copy of the VMMS profile page
(`welinc-web-vmms/src/pages/Profile/Profile.tsx`), with the same sections, text
and styling:

- **Your details:** profile picture upload (PNG, JPEG, GIF or WebP, up to 5 MB),
  name, email (read-only) and phone, then **Save profile**.
- **Change password:** current and new password.
- **Sign-in activity** (Administrator only): a link to the portal's activity
  page, set to BMS (`/admin/activity?system=BMS`).
- **Delete account:** an optional reason and **Request account deletion**. The
  password typed in "Current password" confirms the request. A pending request
  shows **Cancel request**. A rejected one shows the admin's note.
- Results and errors show as one status line at the top of the page, not as
  toasts.

Adapted for BMS only where the two apps differ:
- It uses the BMS `api` client and `useApp()` user instead of the VMMS ones.
- "Administrator" is the BMS admin role name.
- The portal link uses `system=BMS`.

### Backend
None. Both systems already call the same shared `welinc-auth` endpoints through
the gateway:

| Call | Use |
|---|---|
| `GET /auth/me` | Load name, phone and picture |
| `PATCH /auth/profile` | Save name and phone |
| `POST /auth/profile/picture` | Upload the picture |
| `PATCH /auth/profile/password` | Change the password |
| `POST /auth/profile/verify-password` | Get the one-use token for deletion |
| `GET`, `POST`, `DELETE /auth/profile/deletion-request` | Read, file or cancel a deletion request |

The VMMS backend (`welinc-backend-vmms`) has no profile routes, so there was
nothing to copy.

### Removed (BMS-only features the VMMS page does not have)
- The side card with the avatar, role badge, email and phone.
- The Edit Details / Cancel mode. Fields are always editable.
- First and last name as separate fields. There is now one Name field.
- The fixed +63 phone field and its format check. Phone is free text.
- Changing the email address with a confirmation code. Email is read-only.
- Confirm New Password, and the in-page password rule check (8+ characters
  with upper case, lower case, a number and a symbol). **This weakens the
  password rule:** `welinc-auth`'s change-password endpoint only requires 6
  characters (`change-password.dto.ts`, `@MinLength(6)`). Its OTP reset uses the
  stronger rule. Fix it in `welinc-auth`, a shared repo whose changes go through
  a `_root` spec, or put the BMS check back on this page.
- The deletion confirmation popup.
- Recent account activity.
- The `roleLabel` prop. The wrappers now render `<ProfilePage />`.

## Tried and reverted

These were changed to the VMMS style, then put back to the original BMS version
on request. In the end, nothing changed:

- the page header (`src/components/pageheader/Pageheader.tsx`)
- the page numbers under tables (`src/components/ui/TablePagination.tsx`)

## Testing

- The web app type-checks (`tsc -b`) and lints clean.
- Unit tests pass (`npm test`, 20 tests).
- `tests-ui/shared-session.spec.ts`: the account-deletion test was updated for
  the new flow. It now fills "Current password" and clicks "Request account
  deletion". The test still checks that the one-use token and purpose are sent.
  The Playwright UI suite was not run.
- Not yet checked by hand in the browser.

## Local dev note

The Docker `web-bms` container serves the mounted source, but on Windows, file
changes don't always reach the container, so Vite doesn't reload. If an edit
doesn't show, run `docker restart welinc_bms_frontend`, then hard-refresh
(Ctrl + Shift + R). A permanent fix is `server.watch.usePolling` in
`vite.config.ts`. It is not part of this change.

## Deploy notes

- No backend or database changes, so it can merge on its own.
- Merging into `development` triggers the staging deploy.
