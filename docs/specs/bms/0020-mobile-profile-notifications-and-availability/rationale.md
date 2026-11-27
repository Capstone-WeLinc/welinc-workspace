# Rationale: Mobile app real account notifications, profile rework and availability

Decision record for [index.md](index.md). The index is the build contract.

## Context

While testing sign-in on a phone with an account made in the portal, three problems showed up: the notification date didn't match the portal, a brand new account already had Monday to Friday availability, and the profile screen differed from the VRMS/VMMS mobile app. They are kept in one spec because they come from one round of testing on the same app.

## 2026-11-27

- **Notification dates.** The wrong date came from seeder notifications being shown to real accounts, not from a time zone bug. Shared auth already records every account change with the server time and lets any user token read its own events (`GET /auth/profile/activity`, shared spec 0011). Using it makes the app match the portal without any backend change. The seeder list stays for seeder mode so testing without the backend still works.
- **Which events become notifications.** Only account changes a team member should hear about (account created, password, name, email, mobile number, role, unlock, activation, signed out everywhere, picture). Sign-ins, codes and sessions are left out: they'd flood the list and the portal already shows them.
- **Admin's name.** The user asked for the admin's name and initials on admin changes. Shared spec 0011, AC-11 deliberately keeps the admin's name from the person, and changing that needs a suite-wide spec and a `welinc-auth` pull request the other groups can see. The user chose to keep **Administrator** for now. The app reads `actor.name` if shared auth ever sends it, so no app change would be needed later.
- **Opening the profile from a notification.** The user asked that personal details and password notifications open Profile at the changed field, except "account created". The field is stored with the notification (`notifications.profileField`, database version 4) rather than worked out from the id, so it survives app restarts and stays readable in SQLite.
- **No default availability.** The user asked that team members set their own days. The hardcoded default (drivers Mon–Fri, helpers Mon–Sat) was removed for everyone, seeder accounts included, so the app never picks days for a person. An empty start with a short prompt makes "not set yet" visible.
- **Profile, compared with VRMS/VMMS.** The two profile screens were compared first (read only), then the user picked which behaviors to copy:
  - **Top card:** drop the employee ID and join date; show Email and Mobile number rows with "No mobile number on record" when empty, as VRMS/VMMS does.
  - **Edit lock:** fields locked until Edit is tapped, as VRMS/VMMS does, so details aren't changed by accident.
  - **Mobile number:** the user specified a "+63" box with 10 digits only, numbers only, and the error "Enter a valid Philippine mobile number." as soon as the first digit isn't 9. The 10 digits are the 11-digit 09… number without the 0. The number stays required, as it was in BMS.
  - **Update Password:** off until all three fields are filled and match, as VRMS/VMMS does. The live rules checklist and the "different from current" check from BMS stay.
  - **Log out:** moved to the bottom of the page like VRMS/VMMS, in the same colors as Request account deletion as the user asked, and renamed from Sign out.
- **Pull to refresh on every tab.** Set Availability and Profile were the only tabs without it. Profile reloads from `GET /auth/me`; Set Availability reloads what's on the phone until the BMS backend has availability and leave routes for team members.
