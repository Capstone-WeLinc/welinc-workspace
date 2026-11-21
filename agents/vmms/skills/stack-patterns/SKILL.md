---
name: stack-patterns
description: Apply stack-specific implementation patterns when changing VMMS NestJS and Prisma services, the React web client, or the Expo and React Native mobile client.
---

# VMMS stack patterns

Use the relevant section only after confirming the target repository's current versions, scripts, and local conventions. The VMMS stack has multiple apps and versions can differ between repositories.

## NestJS services

- Organize changes around the existing feature modules and keep controllers focused on transport concerns. Put business rules in services and use dependency injection through the established module graph.
- Validate and transform external input at the boundary using the repository's configured DTO and validation patterns. Authentication and authorization must be enforced with server-side guards or policies; UI hiding is not access control.
- Use NestJS exceptions and existing filters consistently. Avoid leaking stack traces, internal identifiers, tokens, or sensitive cost data in responses and logs.
- Avoid circular modules, duplicate providers, broad service responsibilities, and unbounded list endpoints. Follow existing pagination and response conventions.

## Prisma and persistence

- Read the current Prisma schema, generated-client setup, adapter wiring, migrations, and nearby query patterns before editing. Do not assume another VMMS service uses the same schema or database.
- Select only fields needed by the operation and response, especially for personal data and costs. Keep query predicates scoped to the caller's authorized system, role, and assignment.
- Use parameterized Prisma operations; never interpolate untrusted values into raw SQL. Use a transaction when multiple writes represent one indivisible business operation.
- Make schema changes through the repository's migration workflow and consider existing rows, defaults, nullability, uniqueness, and rollback implications. Do not run destructive database operations without explicit authorization.

## React web and mobile clients

- For the Vite web client, follow the installed React and router versions, existing state/data-fetching conventions, and Tailwind version actually present. Do not apply Next.js server-component advice to this client-only Vite app.
- For the shared Expo mobile app, confirm the VMMS path before editing and keep VRMS screens and behavior unchanged. Respect React Native primitives, navigation patterns, secure storage, and the existing offline queue/sync model.
- Keep server state and UI state responsibilities clear. Handle loading, empty, stale, error, validation, and permission-denied states instead of only the populated happy path.
- Preserve keyboard and screen-reader access on web and native controls. Use existing UI components and form patterns rather than adding dependencies without a requirement.

## Always

- Check the consuming callers when changing an API shape. Keep analytics as a derived view and use supported service APIs across system boundaries.
- Follow `coding` for feature workflow and `testing` when the user requests tests or verification. These stack notes do not authorize dependency changes, tests, deployment, or cross-repository contract changes.
