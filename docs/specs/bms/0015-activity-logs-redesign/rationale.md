# Activity logs redesign: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

The Activity Logs page currently presents a general event table with a combined date/time column, an IP-address column, and generic search. The supplied design emphasizes the person, role, action, date and time, with a user search and role/action filters.

## Decisions

- Keep the existing `DateRangeFilter` and its wiring in `PageHeader`. The request explicitly preserves this control; only the rest of the page is redesigned.
- Add a work-action dropdown based on the actions present in the loaded work log, alongside the role dropdown. Use the existing filter component so keyboard and selection behavior stays consistent with the application.
- Split the date and time into separate columns and retain Manila timezone formatting.
- ~~Keep the Accounts tab and its filters.~~ First kept, because removing account audit access goes beyond a visual redesign. The team then decided the Accounts tab is no longer needed (see below).
- Use the name and email text treatment from the reference and remove the decorative initials avatar and action dot from the table rows.
- Keep loading, retry, empty-state and pagination components and the existing work/account API calls.
- Do not change APIs or backend services; all requested filters can be applied to the work activity already loaded by the page.
- Use only `PageHeader`'s own divider. Wrapping the header in a second `border-b` drew two dark lines under it; the reference shows one. The divider colour comes from `PageHeader` unchanged, so it matches the other pages.
- Renumbered from 0014 to 0015: spec bms/0014 (Approvals History details modal) was merged on `main` while this one was still local.
- **Accounts tab removed.** The team decided Admin no longer needs account sign-in activity on this page, so the page now matches the reference with no tabs. Everything only that tab used (the Auth activity calls, its filters and paging, `lib/account-activity.ts`) was removed rather than left unused.
