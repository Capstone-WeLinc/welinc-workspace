# Verify: Mobile app real account notifications, profile rework and availability

Checklist derived from [index.md](index.md). Tick only what was actually checked.

## Build

- [x] `npx tsc --noEmit` passes in `welinc-mobile-bms`.
- [ ] The repo has no CI or automated tests yet.

## Shared auth route

- [x] `GET /auth/profile/activity?category=ACCOUNT` with a `bms-mobile` token of a seeded driver, through the local gateway: accepted, answers `{ data, nextCursor }`.
- [x] An account made in the portal signs in on the app (`kind=MOBILE client=bms-mobile` in the auth log).

## Phone: notifications

- [ ] A new account's notifications show the same date and time as the portal's Recent activity.
- [ ] "An administrator created your account" shows "Administrator" and opens nothing when tapped.
- [ ] A password notification opens Profile at the Password card, outlined in gold for a few seconds, with "Back to notifications".
- [ ] A mobile number notification (change it in the portal) opens Profile at the mobile number field.
- [ ] Offline: the saved list stays.
- [ ] Seeder mode still shows the seeder notifications.
- [ ] An app that already had the old database opens without errors (upgrade to version 4).

## Phone: Set Availability

- [ ] A new account shows no days checked and "You haven't set your availability yet."
- [ ] Edit, pick days, Save Changes saves; saving with no days shows the error.
- [ ] Pull to refresh works.

## Phone: Profile

- [ ] Top card shows Email and Mobile number rows; no employee ID or join date.
- [ ] An account with no number shows "No mobile number on record".
- [ ] Personal details are locked until Edit; Cancel and Save lock them again.
- [ ] Mobile number: "+63" box, only digits can be typed, at most 10.
- [ ] Typing a first digit other than 9 shows "Enter a valid Philippine mobile number." right away.
- [ ] A short number shows the same error on Save; a valid number saves and shows in the portal.
- [ ] Update Password stays off until all three fields are filled and the new password matches.
- [ ] Log out is at the bottom in the deletion button's colors; "Log out?" dialog logs out.
- [ ] Pull to refresh picks up a change made in the portal.
