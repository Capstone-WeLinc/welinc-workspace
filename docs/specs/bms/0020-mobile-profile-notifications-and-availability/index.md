# Mobile app: real account notifications, profile rework and availability

Status: on branch `feature/real-notifications-and-availability` in `welinc-mobile-bms` (into `development`), not yet in a pull request.

Decision history: [rationale.md](rationale.md). Review checklist: [verify.md](verify.md).

Touches `welinc-mobile-bms` only. No change to `welinc-backend-bms`, `welinc-web-bms`, shared auth, portal or the gateway. The app reads one shared auth route it wasn't using before (`GET /auth/profile/activity`), which already exists.

The profile changes follow the VRMS/VMMS mobile app (`welinc-mobile-vrms_vmms`), which was only read, never changed.

## 1. Notifications come from the account's real activity

**Before:** every account saw the seeder notifications, real sign-ins included. A new account showed "Your password was changed successfully" with a made-up date (11 days before the list loaded), which didn't match the portal.

**Now:**

- A real sign-in builds its notifications from the account's own activity in shared auth: `GET /auth/profile/activity?category=ACCOUNT&limit=50` (shared spec 0011, AC-11). Any user token may read its own events, the `bms-mobile` one included.
- `createdAt` is the server's time, so the date and time match the portal's Recent activity.
- If the server can't be reached, the list already saved on the phone stays.
- Seeder mode (`EXPO_PUBLIC_USE_SEEDER_AUTH="true"`) still uses the seeder notifications.
- Job order notifications (assignments, reminders) still need BMS backend routes for team members, as in spec 0010.

| Account event | Message (by the person) | Message (by an admin) | Tapping it opens |
|---|---|---|---|
| `CREATED` | Your account was created. | An administrator created your account. | Nothing |
| `PASSWORD_CHANGED` | Your password was changed successfully. | An administrator changed your password. | Profile → Password |
| `UPDATED` (`name`) | Your name was updated. | An administrator changed your name. | Profile → first and last name |
| `UPDATED` (`email`) | Your email address was updated. | An administrator changed your email address. | Profile → email |
| `UPDATED` (`contact`) | Your mobile number was updated. | An administrator changed your mobile number. | Profile → mobile number |
| `ROLE_CHANGED` | Your role was changed. | An administrator changed your role. | Nothing |
| `UNLOCKED`, `ACTIVATED`, `SESSIONS_ENDED`, `PICTURE_CHANGED` | Short message | Short message | Nothing |

Other event types (sign-ins, codes, sessions) are not shown.

### Opening the profile from a notification

- Tapping a name, email, mobile number or password notification opens the Profile tab, scrolls to that card and outlines the field in gold for about 6 seconds.
- A **Back to notifications** link appears at the top of Profile when it was opened this way.

### Who the notification is from

- Changes made by an admin show **Administrator** (initial "A"), not the admin's name.
- Shared spec 0011, AC-11 keeps the admin's name, id and email from the person on purpose. Showing the name would need a shared auth spec and a `welinc-auth` change, so it stays "Administrator" for now. The app already shows `actor.name` if shared auth ever sends it.

### Offline database

- New column `notifications.profileField` (`name`, `email`, `contact`, `password` or null): which profile field a notification opens.
- `DATABASE_VERSION` goes from 3 to 4. Migration 4 adds the column on phones that already have the table; new installs get it from `CREATE TABLE`.

## 2. Weekly availability isn't set for the person

**Before:** until a team member saved their own days, the app showed a hardcoded default (Monday to Friday for drivers, Monday to Saturday for helpers). A brand new account looked like it had already chosen its days.

**Now:**

- Everyone starts with no days picked. The card says "You haven't set your availability yet. Tap Edit to choose your days."
- Save Changes works on the first save. At least one day is still required.
- Availability is still saved on the phone only. The BMS backend has no weekly availability route yet.

## 3. Profile

| | Before | Now |
|---|---|---|
| Top card | Name, role, employee ID, email, mobile number, join date, Sign out button | Name, role, then **Email** and **Mobile number** rows. No employee ID or join date. An empty number reads "No mobile number on record" |
| Personal details | Always editable; Cancel / Save Changes once something changed | Locked until **Edit** is tapped, then Cancel / Save Changes. Saving or cancelling locks them again (as in VRMS/VMMS) |
| Mobile number | Free text, e.g. 0917 123 4567 | "+63" box with a phone icon, then 10 digits only (numbers only, shown as "912 345 6789"). A pasted 09… or +63… number is cut to its 10 digits |
| Mobile number error | "Enter a PH mobile number, e.g. 0917 123 4567" on save | "Enter a valid Philippine mobile number." as soon as the first digit isn't 9, and on save when the number is short |
| Update Password | On once anything was typed | Off until all three fields are filled and the new password matches the confirmation |
| Sign out | Outlined button in the top card | **Log out** button at the bottom of the page, same pink and red as Request account deletion. Dialog: "Log out?" |
| Pull to refresh | None | Reloads the profile from `GET /auth/me` (keeps the saved one when offline) |

Unchanged: the email stays read-only (changing it needs a code to the new address, not in the app yet), the password rules checklist, and the account deletion card. Request account deletion still only marks the request on the phone, as before.

## 4. Pull to refresh on every tab

| Tab | Before | Now |
|---|---|---|
| Home, Job Orders, Post Service Completion, Notifications | Had it | Unchanged |
| Set Availability | None | Reloads the saved availability and leave requests |
| Profile | None | Reloads the profile from the server |

## Files

| File | Change |
|---|---|
| `services/AccountNotificationsService.ts` | New: turns `/auth/profile/activity` events into notifications |
| `stores/notificationsStore.ts` | Real sign-in uses the account activity; seeder mode keeps the seeder list |
| `components/PhoneField.tsx` | New: "+63" mobile number field |
| `screens/ProfileScreen.tsx` | Top card, Edit lock, phone field, password button, Log out, pull to refresh, opening at a field |
| `screens/AvailabilityScreen.tsx` | "Not set yet" message, first save, pull to refresh |
| `stores/availabilityStore.ts`, `seeders/availability.ts` | No default days |
| `App.tsx`, `screens/NotificationsScreen.tsx` | Open Profile at a field from a notification |
| `database/tables.ts`, `database/database.ts`, `repositories/NotificationRepository.ts`, `types/bms.ts` | `notifications.profileField`, database version 4 |
| `services/AuthService.ts`, `stores/userStore.ts` | `refreshProfile` for pull to refresh |
| `components/FormField.tsx`, `components/BmsIcons.tsx`, `utils/phone.ts` | Gold highlight, phone icon, 10 digit helpers |
| `seeders/notifications.ts` | The seeder password notification opens the Password card |

## Deploy notes

- App only, so it doesn't depend on any backend or web merge.
- Phones that already have the app upgrade their local database to version 4 on the next start. Nothing is lost.
