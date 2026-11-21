---
name: break-ui
description: Stress-check a VMMS screen or component with realistic worst-case fleet, maintenance, fuel, cost, and user data to find layout and interaction failures.
---

# VMMS UI stress check

Use when asked to stress-test a VMMS screen, find realistic UI edge cases, or see what breaks with difficult data. This is a diagnostic task, not an invitation to redesign the screen.

## Choose realistic data

- Inspect the screen, data types, validation, database limits, and API response shapes first. Use schema-backed values when limits exist; otherwise use believable long or unusual values and call out that they are unbounded.
- Choose cases that fit the feature: long vehicle make/model or garage names, plates, work-order descriptions, checklist labels, mechanic names, fuel quantities, currency values, dates, empty records, missing optional fields, large result counts, Unicode, and role-specific actions.
- Include zero and one item, boundary values, unavailable or stale records, and error states when they affect that screen. Do not invent invalid data that the real API rejects unless testing validation is the goal.

## Exercise and report

- Feed stress cases through the same fixture, mock, or API boundary used by ordinary data. Do not hard-code CSS or markup to manufacture a failure.
- Prefer a local test fixture, story, or development-only view. Do not add a debug toggle or ship stress data in the application without explicit request.
- Report each observed failure with the input, screen/state, impact, and a practical fix. Separate visual defects from product choices such as truncation versus wrapping.
- Do not change the component during diagnosis; make fixes only if the user asks. Keep the work in VMMS screens and flows, including VMMS-only paths in the shared mobile repository.
