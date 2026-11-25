# Activity logs redesign: rationale

Decision record for [index.md](index.md). The index is the build contract.

## Context

The Activity Logs page currently presents a general event table with a combined date/time column, an IP-address column, and generic search. The supplied design emphasizes the person, role, action, date and time, with a user search and role/action filters.

## Decisions

- Keep the existing `DateRangeFilter` and its wiring in `PageHeader`. The request explicitly preserves this control; only the rest of the page is redesigned.
- Add a work-action dropdown based on the actions present in the loaded work log, alongside the role dropdown. Use the existing filter component so keyboard and selection behavior stays consistent with the application.
- Split the date and time into separate columns and retain Manila timezone formatting.
- Keep the Accounts tab and its filters. The reference shows the BMS work log, but removing account audit access would change functionality beyond the visual redesign.
- Use the name and email text treatment from the reference and remove the decorative initials avatar and action dot from the table rows.
- Keep loading, retry, empty-state and pagination components and the existing work/account API calls.
- Do not change APIs or backend services; all requested filters can be applied to the work activity already loaded by the page.
