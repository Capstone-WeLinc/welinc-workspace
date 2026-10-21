# UI refresh

Every page, modal and prompt in web-vrms rebuilt on the design system (feature 6). Built UI first (`· Facade`): pages restyle on the data they already have, and screens for features not built yet show their final layout until the slice wires them. These need no spec of their own; `design.md` and the design system spec cover them. Back to [index](index.md).

## UI refresh

### 8. App shell & role badge · planned · Facade
Sidebar, header and page frame on the new tokens, with the user's name and role badge (WL-101).
**Done when:** the role badge comes from the token, shows when collapsed and on a 375px phone, and each role has its own badge color.
- [ ] Build it: `/develop app shell & role badge`

### 9. Login & profile pages · planned · Facade
Login, OTP, forgot password and profile restyled with clear errors and loading states.
**Done when:** each screen works at 375px and 1280px, errors are inline and readable, and buttons show progress.
- [ ] Build it: `/develop login & profile pages`

### 10. Dashboard · planned · Facade
Answers "what needs my attention?" first: open, overdue and waiting tickets up top.
**Done when:** stat tiles and lists use the design system, and empty, loading and error states render.
- [ ] Build it: `/develop dashboard refresh`

### 11. Repair list & detail · planned · Facade
Ticket list with clear status pills and filters; ticket detail laid out around its one next action.
**Done when:** status badges follow `design.md`, the list works as cards on a phone, and every modal and confirm prompt on these screens uses the shared dialog.
- [ ] Build it: `/develop repair list & detail refresh`

### 12. Repair form · planned · Facade
The new repair form in the stakeholder approved layout (WL-201), with pickers instead of typing.
**Done when:** the form matches the approved mockup, validation is inline, and it is usable with one thumb on a phone.
- [ ] Build it: `/develop repair form refresh`

### 13. History & audit log pages · planned · Facade
Filters, tables and detail views restyled.
**Done when:** both pages use the shared table, filters fit a phone, and empty states explain what to do.
- [ ] Build it: `/develop history & audit log refresh`

### 14. User management page · planned · Facade
User table and its create, edit, deactivate and reset modals.
**Done when:** every modal uses the shared dialog, destructive actions ask to confirm, and success and failure show a toast.
- [ ] Build it: `/develop user management refresh`

### 15. Knowledge base & analytics pages · planned · Facade
Knowledge articles and analytics charts on the new tokens.
**Done when:** charts use theme colors, and both pages read well on a phone and in their empty states.
- [ ] Build it: `/develop knowledge base & analytics refresh`
