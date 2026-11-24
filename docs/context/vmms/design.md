# VMMS design rules

VMMS-specific design notes for the web and shared mobile clients, based on the
current UI code as checked 2026-11-22. Keep detailed token values in each
client's stylesheets; the suite-level visual direction is in the workspace
[design.md](../../../design.md).

## Product surfaces

- Admin and Operations use the VMMS web SPA, primarily for fleet administration,
  scheduling, fuel, reports, and audit review.
- Mechanics and Chief Mechanics use the shared VRMS/VMMS mobile app for their
  assigned VMMS workflows. Keep VMMS changes inside VMMS screens and flows.
- Preserve the distinct roles and tasks on each surface; do not assume every
  VMMS feature belongs in both clients.

## Interaction principles

- Use the existing page headers, cards, forms, tables, dialogs, loading/error
  states, and API helpers rather than inventing parallel patterns.
- Keep operational changes explicit: show the selected vehicle/work order,
  identify validation failures, and confirm consequential actions using the
  existing UI conventions.
- Pair status color with a readable status label. Do not communicate
  authorization, errors, or work state by color alone.
- Preserve the existing visual tokens and component conventions. Avoid adding
  hard-coded palette colors to new UI when an existing token or shared
  component fits.
- Treat the UI as presentation only. Backend guards remain authoritative for
  roles, assignment, and data validation.

For a larger redesign or new interaction pattern, use the VMMS UI/design
workflow and update the applicable feature spec before broadening behavior.
