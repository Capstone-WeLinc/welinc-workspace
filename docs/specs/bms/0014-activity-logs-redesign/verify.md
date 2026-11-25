# Verify: Activity logs redesign

Checklist derived from [index.md](index.md). Items are pending review in the running app.

## Web

- [ ] Activity Logs title, subtitle and divider match the reference layout.
- [ ] Header date-range filter is unchanged and still filters work activity by Manila calendar date.
- [ ] BMS work controls show user search, **All Roles** and **All Actions**; each filter narrows the rows correctly.
- [ ] Table columns appear in this order: User, Role, Action Performed, Date, Time.
- [ ] User name and email are shown together; date and time are separate and use Manila formatting.
- [ ] Accounts tab remains available with its category/event filters and account activity.
- [ ] Loading, empty, error/retry and pagination states still render correctly.
- [ ] Layout remains usable at narrow and wide viewport sizes.

## Scope

- [ ] No backend or API files changed.
- [ ] The three spec files are present in this folder.
