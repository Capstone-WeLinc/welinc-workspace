---
name: playwright
description: Write, run, and troubleshoot Playwright browser tests for VMMS web flows, including local development and acceptance checks.
---

# VMMS Playwright browser testing

Use this skill for real-browser tests of VMMS web journeys in `welinc-web-vmms`. It complements unit, component, API, and mobile testing; it does not replace them.

## Before testing

1. Check the target repository's `git status`, `AGENTS.md`, `README`, package scripts, and nearby test patterns. Preserve existing work.
2. Read the relevant VMMS scope item and governing spec or acceptance criteria. Confirm which user-visible behavior the test must prove.
3. Inspect the package manager, installed Playwright packages, config, fixtures, and existing E2E scripts. Reuse them rather than creating a parallel setup.
4. If Playwright or browser binaries are missing, report the prerequisite and ask before installing packages or downloading browsers. Do not add a dependency just to explore the UI.
5. Use only a local or isolated test environment by default. Never point tests at production. Do not read `.env` values, hardcode credentials, or commit authentication state, traces, screenshots, or videos that may contain tokens or personal data.

## Writing browser tests

- Put tests in the existing E2E directory and follow the repository's naming and config conventions. If no convention exists, use `e2e/<flow>.spec.ts`.
- Prefer `getByRole`, `getByLabel`, and other user-facing locators. Use CSS selectors or test IDs only when semantic locators are not practical.
- Assert observable user outcomes: navigation, visible content, form errors, loading/empty states, and permitted or denied actions. Do not couple tests to component internals or styling classes.
- Wait on Playwright conditions and assertions, not fixed sleeps. Avoid timing-dependent tests and real external services.
- Keep each test independent. Reuse established auth and data fixtures; create uniquely identifiable test records only through approved test helpers, and clean up records created by the test.
- Mock at external boundaries only when the test is meant to isolate the UI. For an end-to-end contract check, exercise the real local VMMS API. UI hiding is not proof of backend authorization.
- Cover relevant error, empty, and permission states as well as the primary path. Add mobile and desktop viewports when the acceptance criteria or responsive layout makes them relevant.
- For browser-created popups, wait for the popup event and assert its URL or content. Native OS dialogs, including print dialogs, are outside Playwright's browser control; test the browser-visible behavior and leave native printing or PDF output as a manual check.

## Development and verification loop

1. Start from the acceptance criteria and an existing example in the app. If a behavior or data source is undecided, route it through the VMMS architecture/spec workflow rather than encoding an assumption in a test.
2. Reproduce the flow in the local app, then add or update the smallest test that captures the expected behavior.
3. Start the app and dependencies using documented repository scripts. Confirm the configured base URL is the intended local or isolated environment before running tests.
4. Run the focused spec first, then the documented E2E suite when the focused check passes and broader coverage is warranted.
5. On failure, distinguish application defects from missing services, stale sessions, test data, or browser setup. Report the failing step and evidence; do not weaken a valid assertion to get a green run.
6. Keep test artifacts out of commits unless the repository intentionally tracks them. Do not claim a feature is complete based only on a passing browser test.

When developing or fixing a VMMS web flow, use this skill alongside `coding` and the `testing` skill. Follow the repository's own scripts and conventions; do not assume npm, a particular port, or a specific authentication fixture.
