# 0013. Analytics and AI move into backend-vrms; the Python service retires

**Date**: 2026-10-30
**Status**: Accepted

## Summary

The analytics charts and the AI diagnosis move out of the separate Python service and into welinc-backend-vrms, which then owns them. Analytics reads the live VRMS database directly. The AI uses Gemini through one small adapter (a thin wrapper so the provider can be swapped later), stores real embeddings (numbers that capture what an issue means) in the same database with pgvector, and keeps each diagnosis in a Postgres table. The separate analytics database, MongoDB, Redis, DuckDB and the 30 second sync all go away, and the fake numbers the old service and page showed are removed. This is a move, not a redesign: the page and the AI panel look the same, and the new AI ideas wait for feature 47.

## Requirements

**User stories**:
- As an Admin, I want the Analytics page to show real, current numbers on staging and production, so that what I export and present is true.
- As a mechanic, I want the AI diagnosis to find past repairs that really are similar, and to show me the last diagnosis when I reopen a ticket, so that I don't pay for the same answer twice.
- As anyone, I want an honest "AI is unavailable" when Gemini is down, so that I never act on a made up answer.
- As the system owner, I want one service and one database to run and host, so that Azure stays cheap and there is less to break.

**Acceptance criteria**:

*Boundary and stores*
- **AC-1**: welinc-backend-vrms owns analytics and AI in two new modules, `src/modules/analytics/` and `src/modules/ai/`. The only store is the VRMS PostgreSQL database. The separate analytics PostgreSQL, MongoDB, Redis, DuckDB and the 30 second sync are not used by anything.
- **AC-2**: One migration (after spec 0012's) runs `CREATE EXTENSION IF NOT EXISTS vector` and creates `issue_embeddings`, `ai_diagnoses` and `ai_diagnosis_feedback` exactly as in *Data model sketch*. The extension is plain SQL in the migration (no `postgresqlExtensions` preview feature), and `prisma migrate diff` shows no drift afterwards. The local `vrms-db` image becomes `pgvector/pgvector:pg16` (same major version, so existing volumes keep working). On Azure, the flexible server's `azure.extensions` parameter must include `VECTOR` before the migration job runs; no Bicep exists yet, so this is handed to spec 0008's build (see Follow-up).

*Analytics*
- **AC-3**: Eight endpoints answer under `/vrms/analytics`: `summary`, `cost-trends`, `vehicle-kpis`, `issue-frequency`, `status-breakdown`, `garage-costs`, `aging`, `velocity`. Each returns the same field names and envelope the web app's `analyticsApi.ts` types expect today (lists as `{ data: [...] }`, `summary` as an object). Every number is read live from the VRMS tables through one `AnalyticsService` (`$queryRaw`), with no cache and no copy.
- **AC-4**: Each metric follows *Metric rules* below. A cancelled ticket never counts toward spend or repair counts. Months are calendar months in `Asia/Manila`; months with no tickets are left out. Every count is cast `::int` and every money or average value `ROUND(..., 2)::float8` in SQL, so no `BigInt` or `Decimal` reaches the JSON.
- **AC-5**: Every analytics route needs `analytics.view` (module `analytics`). The peso fields (`total_spend`, `cumulative_spend`, `total_parts_cost`, `avg_repair_cost`, `avg_cost_per_repair`) come back `null` unless the caller also holds `ticket.costs.view`, the same rule as ticket costs (spec 0011, AC-11). The controller passes `request.ability` to the service, and one `maskCosts()` function nulls the fields. When costs are masked, `garage-costs` sorts by garage name and `vehicle-kpis` by repairs then plate, so the order never leaks spend.
- **AC-6**: The Analytics page calls `/vrms/analytics/*` and `/vrms/ai/stats`. The sample data (`SAMPLE_VEHICLES`, `SAMPLE_TRENDS`, `SAMPLE_ISSUES`, `orSample` and the catch fallback in `useAnalyticsData.ts`) is deleted. A section whose call fails shows the shared error state with Retry. A section with no rows shows the shared empty state. CSV and PDF export are disabled while any section is loading or failed, so an export never holds missing or made up data. When peso fields are `null`, money columns and series are hidden with the note "Costs are hidden for your role".

*AI diagnosis*
- **AC-7**: `POST /vrms/ai/tickets/:ticketId/diagnoses` (empty body) runs a diagnosis. The caller needs `ai.use` and must be able to read the ticket (`accessibleBy`, so a Mechanic only on their own tickets). A ticket that is `CLOSED` or `CANCELLED` answers 409 `{ code: 'TICKET_CLOSED' }`. The server builds every input from the ticket itself, never from the request: the symptom is the ticket's issue descriptions joined with `. `, plus the vehicle plate and model. Checks run in this order: guard (permission and module), ticket readable (404), ticket closed (409 `TICKET_CLOSED`), hourly limit (429), busy (409 `AI_BUSY`). Ticket access reuses `readableTickets(ability)`, moved out of `repairs.service.ts` into a shared export, not rewritten.
- **AC-8**: The diagnosis follows *Diagnosis pipeline* below: embed the symptom, find up to 5 similar issues, read the vehicle's last 5 tickets, ask Gemini for a JSON answer that matches a fixed schema, price the parts from `repair_parts`, and score the confidence. `est_cost_php` on each part is `null` unless the caller holds `ticket.costs.view`.
- **AC-9**: Each successful run writes one `ai_diagnoses` row and returns it. `GET /vrms/ai/tickets/:ticketId/diagnoses/latest` returns the newest row for that ticket, or `{ data: null }` if none. Both return the stored snapshot (similar cases and vehicle history as the AI saw them, never recomputed) through one `presentDiagnosis(row, ability)` function, which also nulls part prices. The panel calls neither endpoint without `ai.use`. The repair detail panel loads the latest on open and shows it with "Ran <relative time>", plus a **Run again** button while the ticket is open. A closed or cancelled ticket shows its latest diagnosis read only, with no run button. This replaces spec 0004 AC-22's "Run AI review" on closed tickets.
- **AC-10**: When Gemini fails (network error, the 20 second timeout, any 4xx or 5xx including a bad key, a safety block, a reply that fails validation, or an embedding of the wrong length or count), the request answers 503 `{ code: 'AI_UNAVAILABLE', message: 'AI is unavailable right now. Try again in a moment.' }` and nothing is stored. There is no rule based fallback. The panel shows the message and a Try again button. No other page or action depends on AI.
- **AC-11**: Limits. A second run on a ticket while one is in progress answers 409 `{ code: 'AI_BUSY' }` (a transaction scoped Postgres advisory lock on the ticket id, so it holds across replicas). A user's 21st run within a rolling hour answers 429 `{ code: 'AI_RATE_LIMITED', retryAfterSeconds }`, counted from their `ai_diagnoses` rows; `retryAfterSeconds` is rounded up, at least 1. Failed runs store nothing and do not count. Two parallel runs by one user on different tickets may slip one past the limit; accepted.
- **AC-12**: `PUT /vrms/ai/diagnoses/:id/feedback` with `{ helpful: boolean, rating?: 1..5, comment?: string ≤ 500 }` stores or replaces the caller's one feedback row for that diagnosis. The caller needs `ai.use` and read access to the diagnosis's ticket; feedback is allowed on closed tickets. `helpful` and `rating` are not cross checked. The panel's buttons work as today.
- **AC-13**: `GET /vrms/ai/stats` (needs `analytics.view`, so the guard answers for the analytics module; the service itself throws 403 `MODULE_DISABLED` with `module: 'ai'` when AI is off, since the route key isn't in the AI module) returns `total_interactions`, `models_used` and `satisfaction` computed from the two tables. With no rows it returns zeros and an empty `models_used`, never invented numbers.

*Embeddings*
- **AC-14**: After a ticket is created (the only code path that writes issue text today), backend-vrms embeds its issues in the background: `EmbeddingService.embedIssuesInBackground(issueIds)` is called after the create returns, as a floating promise that catches and logs every error and is never awaited. It uses task type `RETRIEVAL_DOCUMENT`, `outputDimensionality: 768`, normalized to length 1 in code, on the description with its leading `[<category>] ` prefix removed (the text `create()` writes is `[<category>] <rootCause>: <description>`). Any future edit path is covered by the catch up job's `text_hash` check. It upserts `issue_embeddings` with the model name and the SHA 256 `text_hash`. A failure logs a warning and never fails or slows the save. This replaces `autoEmbedIssues` and `AI_SERVICE_URL`.
- **AC-15**: A catch up job runs every 10 minutes (`@nestjs/schedule`, with `ScheduleModule.forRoot()` registered in `AppModule`) on one replica at a time: each pass runs inside one interactive transaction that takes `pg_try_advisory_xact_lock` (released on commit; a replica that doesn't get it skips). While `module.ai` is on, it embeds up to 50 issues, oldest first, created within the last `ai.embed_catchup_days` that have no embedding, a different `model`, or a different `text_hash`. It stops the run at the first provider error.
- **AC-16**: `npm run ai:embed-all` embeds every missing or stale issue regardless of age, 50 at a time, logging progress. On a provider error it retries once after 2 seconds, then stops and exits non zero. It is safe to run again.
- **AC-17**: AI off (`module.ai`, spec 0012): no embedding on save, the catch up job skips, and every `/vrms/ai/*` route answers 403 `MODULE_DISABLED` (its key `ai.use` belongs to module `ai`). `ai.use` is now enforced on the server, and its catalog description drops "the AI service itself is not yet locked by role".
- **AC-18**: The settings catalog (spec 0012) gains `ai.embed_catchup_days`: kind `value`, group `AI`, type `int`, default 30, range 1 to 365, unit `days`, module `ai`.

*Retirement*
- **AC-19**: After web-vrms points at the new endpoints, nothing runs the Python service:
  - `docker-compose.analytics.yml` is deleted.
  - `scripts/clone-all.sh` stops cloning `welinc-backend-vrms-analytics-ai`.
  - The `/ai` and `/analytics` locations are removed from `welinc-auth/nginx.conf` (a shared repo, so tell the other groups through feature 55).
  - backend-vrms `.env.example` drops `AI_SERVICE_URL` and adds `GEMINI_API_KEY`, `GEMINI_MODEL` and `GEMINI_EMBED_MODEL`.
  - The repo is archived on GitHub with a README line pointing here.
  - Spec 0012's Python `app_settings` read (`module_flags.py`) goes with the service.
- **AC-20**: With no `GEMINI_API_KEY`, backend-vrms starts normally and logs one warning. AI runs answer 503 `AI_UNAVAILABLE`, embedding is skipped, and analytics works.

*Close out*
- **AC-21**: Unit tests cover the metric rules (cancelled tickets excluded, Manila month buckets, cost nulling) and the diagnosis service on a fake `AiProvider` (success, timeout, bad JSON, `AI_BUSY`, `AI_RATE_LIMITED`, `TICKET_CLOSED`). They also cover the embedding hash and model staleness check, and the catch up selection. The spec 0011 route table test stays green with the new routes. Lint, build and test pass in backend-vrms; lint, typecheck, build and test pass in web-vrms.

## Decision

**Chosen option**: Option 2: rebuild analytics and AI inside backend-vrms on the VRMS database, then retire the Python service.

Analytics becomes live SQL over the VRMS tables, the AI becomes a Nest module that calls Gemini through an `AiProvider` adapter, and pgvector plus two Postgres tables replace every other store.

**Implementation skills**: `nestjs-best-practices` (`kadajett/agent-nestjs-skills`, `.claude/skills/nestjs-best-practices/`) · `prisma-client-api` (`prisma/skills`, `.claude/skills/prisma-client-api/`) · `prisma-cli` (`prisma/skills`, `.claude/skills/prisma-cli/`) · `vercel-react-best-practices` (`.claude/skills/vercel-react-best-practices/`) for the analytics hook and the AI panel · `docker-patterns` (`.claude/skills/docker-patterns/`, ask first) for the compose changes

## Rationale

Reasoning and options: see [rationale.md](rationale.md).

## Feature design

**Data model sketch** (one migration):

| Entity | Field | Type | Notes |
|---|---|---|---|
| `IssueEmbedding` (`issue_embeddings`) | `issueId` PK, FK → `repair_issues.id` | uuid | 1:1, `onDelete: Cascade` |
| | `embedding` | `Unsupported("vector(768)")` | read and written only with raw SQL; no vector index (a full scan is instant at this size, and it avoids the HNSW crashes reported on Azure pgvector 0.8.0) |
| | `model` | varchar(60) | e.g. `gemini-embedding-2`; differs from `GEMINI_EMBED_MODEL` means stale |
| | `textHash` | char(64) | SHA 256 hex of the embedded text; differs means stale |
| | `createdAt`, `updatedAt` | timestamptz(6) | |
| `AiDiagnosis` (`ai_diagnoses`) | `id` PK | uuid | |
| | `repairTicketId` FK → `repair_tickets.id` | uuid | N:1, `onDelete: Cascade`; index `(repairTicketId, createdAt desc)` |
| | `requestedByUserId` | uuid | welinc-auth id, no FK; index `(requestedByUserId, createdAt)` for the hourly limit |
| | `input` | jsonb | `{ symptom, issues[], vehiclePlate, vehicleModel, vehicleHistory[{ ticketId, repairNumber, status, closedAt, issues[] }] }` |
| | `similar` | jsonb | `[{ issueId, ticketId, repairNumber, description, similarity }]` |
| | `result` | jsonb | `{ summary, predictedCategory, predictedPriority, estimatedHours, probableCauses[], recommendedParts[{ partName, estCostPhp }], safetyNote }`; prices always stored, nulled on read without `ticket.costs.view` |
| | `model` | varchar(60) | the generation model used |
| | `confidence` | varchar(10) | `High`, `Moderate` or `Low` |
| | `latencyMs` | int | |
| | `createdAt` | timestamptz(6) | |
| `AiDiagnosisFeedback` (`ai_diagnosis_feedback`) | `id` PK | uuid | |
| | `diagnosisId` FK → `ai_diagnoses.id` | uuid | N:1, `onDelete: Cascade`; unique `(diagnosisId, userId)` |
| | `userId` | uuid | welinc-auth id, no FK |
| | `helpful` | boolean | |
| | `rating` | smallint, nullable | 1 to 5, checked in the DTO |
| | `comment` | text, nullable | up to 500 characters |
| | `createdAt`, `updatedAt` | timestamptz(6) | |

Diagnoses are kept until their ticket is deleted. No other table changes. The three tables are not CASL subjects; access goes only through the ticket check. Prisma 7 can't create rows in a model with a required `Unsupported` column, so `issue_embeddings` is written with raw `INSERT ... ON CONFLICT (issue_id) DO UPDATE`, binding the vector as text cast `$1::vector` (`'[0.1,...]'`). Its other columns can still be read and deleted through Prisma.

**Metric rules** (AC-4; "spend" is `COALESCE(total_cost, 0)`; "counted" means `repair_status <> 'CANCELLED'`):

| Endpoint | Rule |
|---|---|
| `summary` | `total_spend` and `total_repairs` over counted tickets; `total_vehicles` = distinct vehicles with a counted ticket; `avg_cost_per_repair` = spend ÷ repairs (0 when no repairs) |
| `cost-trends` | per Manila month of `created_at`, counted tickets: `month` (`YYYY-MM`), `repair_count`, `total_spend`, running `cumulative_spend`; oldest first |
| `vehicle-kpis` | per vehicle, counted tickets: `vehicle_plate`, `vehicle_model`, `total_repairs`, `total_parts_cost` (spend), `avg_repair_cost` (spend ÷ repairs), `latest_repair_date` (newest `created_at`, `YYYY-MM-DD` in Manila); top 10 by repairs then spend |
| `issue-frequency` | issues on counted tickets, grouped by the description as stored; `description`, `occurrence_count`; top 10 |
| `status-breakdown` | every ticket, per `repair_status`: `status`, `count` |
| `garage-costs` | per garage name, counted tickets: `garage`, `repair_count`, `total_spend`; by spend desc |
| `aging` | tickets not `CLOSED` or `CANCELLED`, by age since `created_at`: buckets `< 24h`, `24-72h`, `> 72h` (all three always present) |
| `velocity` | every ticket, per Manila month of `created_at`: `date` (`Mon YYYY`, English month names whatever the server locale, e.g. built from a fixed name list), `count`; oldest first |

**Diagnosis pipeline** (AC-8):
1. Embed the symptom with `RETRIEVAL_QUERY`, 768 dimensions, normalized.
2. Similar issues: `1 - (embedding <=> $query)` over `issue_embeddings` where `model` equals the current embed model, excluding this ticket's issues and cancelled tickets; keep similarity ≥ 0.60, top 5. Each shows its description and repair number only (no costs).
3. Vehicle history: the vehicle's last 5 tickets other than this one, newest `closed_at` first (nulls last), with status and issue descriptions.
4. Gemini `generateContent` with `GEMINI_MODEL`, JSON output against the result schema, the prompt carrying the symptom, issues, vehicle, history and similar cases (today's prompt, minus the "do not include pricing" workaround). The Gemini schema is written by hand in Gemini's own schema format (`Type.OBJECT` from `@google/genai`). The reply is validated again in code with a class-validator DTO (`plainToInstance` then `validate`), since Gemini doesn't enforce lengths:
   - `summary` and `safetyNote` up to 500 characters
   - `probableCauses` 1 to 6 items
   - `recommendedParts` up to 8
   - `estimatedHours` above 0 and up to 200

   A failed check is `AI_UNAVAILABLE`. `predictedCategory` should be an active `IssueCategory` name or `General`; any other name is coerced to `General`. `predictedPriority` must be one of `RepairPriority`, else `AI_UNAVAILABLE`.
5. Part prices: for each part, `AVG(unit_cost)` from `repair_parts` whose `description ILIKE '%' || partName || '%'` on counted tickets, rounded to 2 places, `null` when none.
6. Confidence (today's rule): 3 points for a live answer, +2 for at least 3 similar cases (+1 for 1 or 2), +1 for any vehicle history, +2 for average similarity ≥ 0.80 (+1 for ≥ 0.65). A score of 6 or more is `High`, 3 to 5 `Moderate`, below 3 `Low`.

**AiProvider** (`src/modules/ai/ai-provider.ts`): `embed(texts: string[], task: 'RETRIEVAL_DOCUMENT' | 'RETRIEVAL_QUERY'): Promise<number[][]>` and `generateJson<T>(prompt: string, schema: object): Promise<T>`. `GeminiProvider` uses `@google/genai` (not the deprecated `@google/generative-ai`). Timeouts: 20 seconds to generate, 10 seconds to embed. Up to 50 texts per embed call (100 hit the free tier's per minute limit, see Migration plan risks); each text goes in its own content object, because `gemini-embedding-2` reads a plain string array as parts of one content and returns a single combined vector (checked 2026-10-31). A reply whose vector count or length (768) differs from the request is a provider error.

**Run transaction** (AC-11): the run goes inside `prisma.$transaction(fn, { timeout: 30000, maxWait: 5000 })`:
1. `tx.$queryRaw` runs `SELECT pg_try_advisory_xact_lock(hashtextextended(${ticketId}, 0))`. False means `AI_BUSY`.
2. The hourly count runs.
3. Gemini is called inside the transaction.
4. The `ai_diagnoses` row is written on the same `tx`.

This holds one pooled connection for up to about 20 seconds, which the limits keep rare. `FakeAiProvider` serves the tests. Nothing outside `src/modules/ai/` imports `@google/genai`.

**API surface** (all backend-vrms, behind the global guards of spec 0011):

| Endpoint | Method | Key inputs | Key outputs | Auth | Key errors |
|---|---|---|---|---|---|
| `/vrms/analytics/summary` | GET | | `{ total_spend, total_repairs, total_vehicles, avg_cost_per_repair }` | `analytics.view` | 403 |
| `/vrms/analytics/{cost-trends, vehicle-kpis, issue-frequency, status-breakdown, garage-costs, aging, velocity}` | GET | | `{ data: [...] }`, fields per *Metric rules* | `analytics.view` | 403 |
| `/vrms/ai/tickets/:ticketId/diagnoses` | POST | none | the diagnosis (below) | `ai.use` + ticket readable | 404, 409 `TICKET_CLOSED`, 409 `AI_BUSY`, 429 `AI_RATE_LIMITED`, 503 `AI_UNAVAILABLE` |
| `/vrms/ai/tickets/:ticketId/diagnoses/latest` | GET | | `{ data: diagnosis \| null }` | `ai.use` + ticket readable | 404 |
| `/vrms/ai/diagnoses/:id/feedback` | PUT | `helpful` (req), `rating?`, `comment?` | `{ helpful, rating, comment, updatedAt }` | `ai.use` + ticket readable | 400, 404 |
| `/vrms/ai/stats` | GET | | `{ total_interactions, models_used: { [model]: count }, satisfaction: { avg_rating, helpful_count, total_feedback, satisfaction_rate } }` | `analytics.view`, module `ai` | 403 |

A diagnosis is `{ id, ticketId, createdAt, model, confidence, latencyMs, symptom, similar[{ issueId, ticketId, repairNumber, description, similarity }], vehicleHistory[{ ticketId, repairNumber, status, closedAt, issues[] }], result }`, camelCase. The web `aiApi.ts` types are rewritten to this shape. The panel derives what `context_lineage` showed: matches = `similar.length`, average similarity = the mean of `similarity` (0 to 1), history count = `vehicleHistory.length`. The "used live AI" row is deleted, since it is always true now. The panel shows `result.estimatedHours` where it showed `estimated_sla_hours`. A route key belongs to an off module → 403 `MODULE_DISABLED` (spec 0012, AC-11). A ticket the caller can't read → 404, as ticket reads do today.

**Value sourcing**:

| Action | Value produced / displayed | Source |
|---|---|---|
| Any analytics read | month boundaries | `created_at AT TIME ZONE 'Asia/Manila'`, a fixed constant (WeLinc runs in one country) |
| Any analytics read | whether peso fields are shown | caller's ability: `ticket.costs.view` |
| `garage-costs` | garage name | `garages.name` through `repair_tickets.garage_id` |
| `vehicle-kpis` | plate, model | `vehicles.plate_number`, `vehicles.model` |
| Run diagnosis | symptom, issues | the ticket's `repair_issues.description`, `[System] ` prefix removed |
| Run diagnosis | plate, model | the ticket's vehicle |
| Run diagnosis | similar issues | `issue_embeddings` with the current `model`, joined to `repair_issues` and `repair_tickets` |
| Run diagnosis | vehicle history | `repair_tickets` with the same `vehicle_id` |
| Run diagnosis | allowed categories | active `issue_categories.name` plus `General` |
| Run diagnosis | part prices | `AVG(repair_parts.unit_cost)` by name match |
| Run diagnosis | requester | `req.user.sub` |
| Run diagnosis | hourly count | `COUNT(*)` of `ai_diagnoses` for the requester where `created_at > now() - interval '1 hour'` |
| Run diagnosis | `retryAfterSeconds` | the oldest counted row's `created_at` + 1 hour − now |
| Run diagnosis | model name | `GEMINI_MODEL` |
| Panel | "Ran <time>" | `ai_diagnoses.created_at` |
| Embed | text and hash | `repair_issues.description` with its leading `[<category>] ` removed; SHA 256 of that text |
| Run diagnosis | vehicle history items | `repair_tickets` (same vehicle) and their `repair_issues`, stored in `input.vehicleHistory` |
| Latest diagnosis | similar cases, history | the stored `similar` and `input.vehicleHistory` (a frozen snapshot) |
| Embed | model | `GEMINI_EMBED_MODEL` (default `gemini-embedding-2`) |
| Catch up | window | `ai.embed_catchup_days` from `SettingsService` |
| Catch up, embed on save | AI on or off | `module.ai` from `SettingsService` |
| AI stats | totals, models, satisfaction | `ai_diagnoses` and `ai_diagnosis_feedback` aggregates; `satisfaction_rate` = helpful ÷ feedback × 100, 1 decimal, 0 when no feedback |

**Key invariants**:
- The VRMS database is the only store; nothing copies its data elsewhere.
- No endpoint returns invented numbers. An empty result is empty, and a failure is an error.
- Similarity only compares vectors made by the same model.
- An `issue_embeddings` row always matches its issue's current text, or the catch up job will replace it.
- A diagnosis row exists only for a run that succeeded; a failed run leaves nothing.
- Every AI input is read from the database, never trusted from the request body.
- Only `src/modules/ai/` talks to the AI provider.

**Security model**:
- Analytics: `analytics.view` opens it; money needs `ticket.costs.view` as well.
- AI: `ai.use` plus read access to the ticket, now enforced on the server (it was web only, spec 0012). Similar cases show other tickets' issue descriptions and repair numbers but never costs or people; this matches today and the knowledge base's visibility.
- `GEMINI_API_KEY` lives in backend-vrms env and Azure Container Apps secrets only, never in a `VITE_*` variable.
- On the Gemini free tier, Google may use prompts and replies to improve its products. Prompts carry issue text, plates and vehicle models, no names or contact details. Before real production use, switch the key to a paid tier (which excludes that use); no code change.
- The Python service's unauthenticated `/ai` and `/analytics` routes, and its allow all CORS, disappear with it.

**Configuration required**:
- `GEMINI_API_KEY`: Gemini API key (backend-vrms; empty means AI unavailable, AC-20)
- `GEMINI_MODEL`: generation model, default `gemini-3.5-flash-lite`. It was chosen for its free tier room (15 requests a minute, 500 a day, against 20 a day for the full Flash models). Checked against the project's Rate Limit page and a live JSON call on 2026-10-30.
- `GEMINI_EMBED_MODEL`: embedding model, default `gemini-embedding-2`. A live call on 2026-10-30 confirmed it returns 768 values for `RETRIEVAL_DOCUMENT` (already length 1) and takes up to 8192 input tokens. `gemini-embedding-001` also returns 768 but unnormalized, so the code normalizes either way.
- Free tier limits are per Google project and shared by every user: embeddings 100 a minute and 1K a day, `gemini-3.5-flash-lite` as above. Spec this feature for one project; raise the limits by enabling billing on it.
- The key starts with `AQ.`; keep the whole value, a missing first letter makes Google answer "API key not valid".
- Removed: `AI_SERVICE_URL`

**Critical test scenarios**:
- Happy path: a Mechanic opens their open ticket, runs a diagnosis, sees causes and similar repairs, rates it; reopening shows the same diagnosis. Verifies **AC-7**, **AC-8**, **AC-9**, **AC-12**.
- Analytics truth: with one cancelled ticket of ₱10,000 seeded, `summary.total_spend` excludes it; a ticket created 2026-10-31 23:30 Manila time lands in October. Verifies **AC-3**, **AC-4**.
- Costs hidden: an Admin granted `analytics.view` but not `ticket.costs.view` gets `null` peso fields and sees the "Costs are hidden" note; part prices in a diagnosis are `null`. Verifies **AC-5**, **AC-6**, **AC-8**.
- Failure: the fake provider times out, so the response is 503 `AI_UNAVAILABLE`, no row is written, and the panel shows Try again; the analytics page with one failed call shows that section's error state and export disabled. Verifies **AC-6**, **AC-10**.
- Limits: two parallel runs on one ticket give one success and one `AI_BUSY`; a 21st run in an hour gives 429. Verifies **AC-11**.
- Embeddings: creating a ticket embeds its issues without slowing the save; a row whose `text_hash` no longer matches, or a changed `GEMINI_EMBED_MODEL`, makes the catch up job re-embed, and similarity ignores old rows meanwhile. Verifies **AC-14**, **AC-15**.
- Auth and modules: a Mechanic on another mechanic's ticket gets 404; with AI off, `POST .../diagnoses` gets 403 `MODULE_DISABLED` and saving a ticket makes no provider call. Verifies **AC-7**, **AC-17**.
- No key: unset `GEMINI_API_KEY`, and the app starts, analytics loads, and a run answers 503. Verifies **AC-20**.

## Build plan

Tracer Bullet: one analytics chart and one AI run end to end first, then widen, then retire the old service last, only once nothing calls it.

1. **Thin thread**:
   - The migration (vector extension and the three tables), with the `vrms-db` image switched to `pgvector/pgvector:pg16`.
   - `AnalyticsModule` with `summary` and the cost nulling, and the web `getAnalyticsSummary` pointed at `/vrms/analytics/summary` with its error and empty states.
   - `AiModule` with `AiProvider`, `GeminiProvider` and `FakeAiProvider`, embed on save, and `POST` diagnoses with steps 1 to 4 of the pipeline, storing the row.
   - The AI panel calling it.
   - Satisfies **AC-1**, **AC-2**, **AC-3** (summary), **AC-5**, **AC-7**, **AC-9** (run), **AC-14**, **AC-20**.
2. **All analytics, no sample data**: the other seven endpoints with the metric rules, every web call moved, the sample data and fallback deleted, per section error and empty states, export disabled while incomplete, the hidden costs note. Satisfies **AC-3**, **AC-4**, **AC-5**, **AC-6**.
3. **Complete the AI**:
   - Part prices and confidence.
   - The latest endpoint, the panel showing the latest with Run again, and read only on closed tickets.
   - Errors and limits (`AI_UNAVAILABLE`, `AI_BUSY`, `AI_RATE_LIMITED`, `TICKET_CLOSED`).
   - Feedback, AI stats from the tables, `ai.use` enforced on the server, the module switch on every AI path.
   - Satisfies **AC-8** to **AC-13**, **AC-17**.
4. **Embedding upkeep**: the `ai.embed_catchup_days` setting, the catch up job with its lock, and `npm run ai:embed-all` (run once on each environment after deploy). Satisfies **AC-15**, **AC-16**, **AC-18**.
5. **Retire the Python service**:
   - Delete `docker-compose.analytics.yml`, update `scripts/clone-all.sh` and backend-vrms `.env.example`.
   - Remove the gateway routes in `welinc-auth/nginx.conf` (its own PR, noted on feature 55's list).
   - Hand the `azure.extensions` setting to spec 0008's Bicep work.
   - Archive the repo after the backend and web PRs merge.
   - Satisfies **AC-19**, **AC-2** (Azure note).
6. **Close out**: unit tests and the route table test, then lint, typecheck, build and test in backend-vrms and web-vrms. Satisfies **AC-21**.

## Migration plan

**Strategy**: strangler, small scale. The new endpoints go live beside the old service; web-vrms switches per section; the old service is removed only when nothing calls it.
**Phases**:
1. Build steps 1 to 4 in backend-vrms and web-vrms. The Python stack can keep running locally meanwhile; nothing reads from it once the web app has switched.
2. Run `npm run ai:embed-all` locally and on staging (the old vectors are fake and are not copied).
3. Step 5 removes the Python stack. Old Mongo logs, DuckDB and vectors are dropped, not migrated: the logs are test data and the vectors are invalid.
**Rollback**: revert the web-vrms PR to point back at `/ai` and `/analytics` and run `docker compose -f docker-compose.analytics.yml up` from the previous commit. This only works before step 5, and only because PR 5 patched the old service for the v2 schema; its similar cases stay broken. Archive the repo last.
**Risks**: the free embedding quota is 1K requests a day per project (confirmed in AI Studio, not zero). A batch of texts counts one request per text (checked 2026-10-31: a batch of 100 hit the per minute 429, a batch of 50 passed), so `ai:embed-all` sends 50 at a time with a pause between batches, and may need several days of the daily quota or a paid key once. The old Python sync filled the old embedding model's daily limit in August, which a one time embed per issue avoids. Also, staging needs `vector` allowed before the migration job runs.

## Consequences

**Positive**:
- One service and one database to run; four stores and a sync thread are gone, and analytics finally works on Azure.
- Similar repairs become real: today's vectors are random numbers keyed on a category word, compared with real Gemini query vectors.
- No made up numbers anywhere: the page, `/ai/stats` and the keyword fallback all stop inventing data.
- Analytics and AI ride the spec 0011 permissions and the spec 0012 module switches with no special cases.
- Feature 47 starts from a clean `AiProvider`, stored diagnoses and stored feedback.

**Negative / tradeoffs**:
- Analytics queries run on the live database; a heavy future report could slow ticket work. This is fine at three garages, but measure before adding reports in feature 45.
- AI now runs inside backend-vrms, so a hang in the provider client could tie up API workers; the timeouts and the busy lock are what prevent that.
- The free Gemini tier may use prompts for Google's products, and its quota is small (500 diagnoses a day, shared by everyone) and can change without notice. `gemini-3.5-flash-lite` is also a lighter model than the full Flash line, so try it on a few real tickets before the demo.
- Diagnosing closed tickets ("Run AI review") goes away.
- `Unsupported` vector columns need raw SQL, and Prisma Studio can't show `issue_embeddings`.
- Two numbers change meaning: cancelled tickets leave spend and counts, and months follow Manila time instead of UTC.
- A run holds a database connection for up to about 20 seconds while Gemini answers.
- If the deadline slips, the first cut is the catch up job and `ai.embed_catchup_days` (AC-15, AC-18). Embedding at create time plus `ai:embed-all` still work without them. If Container Apps ever scales to zero, the job doesn't fire anyway.

**Neutral**:
- The Python repo is archived, not deleted; its history stays readable.
- The web app's AI types change shape; only `AiDiagnosisSection` and the AI stats block use them.
- `analytics.view`'s catalog comment ("until feature 3 moves analytics into this API") is resolved and removed.

## Follow-up

- [ ] Feature 47: grounding on the knowledge base, triage while typing, search by meaning, note cleanup, drafted entries, duplicate warnings, and the AI panel and feedback redesign. Declare `module.ai` `requires: ['module.knowledge']` when grounding lands (spec 0012 follow up).
- [ ] Feature 55: tell the other groups that VRMS removes `/ai` and `/analytics` from `welinc-auth/nginx.conf`.
- [ ] Before go live: decide a retention limit for `ai_diagnoses` if WeLinc asks for one, and move `GEMINI_API_KEY` to a paid tier (also lifts the 500 a day and 1K a day limits).
- [x] Check that the embedding models support 768 values (done 2026-10-30: both `gemini-embedding-001` and `gemini-embedding-2` do).
- [ ] Spec 0004: note that AC-22's AI review on closed tickets is replaced by this spec's AC-9. Confirm in Jira that dropping it is fine (Jira wins).
- [ ] Spec 0008's Bicep: set the flexible server configuration `azure.extensions` to include `VECTOR` (`Microsoft.DBforPostgreSQL/flexibleServers/configurations`), applied before the migration job runs.
- [ ] Spec 0007: its follow up "removes `autoEmbedIssues` and the Python `/ai/knowledge/articles`" is covered here; tick it when this ships.
- [ ] Spec 0008: the "Not deployed" row for analytics-ai, the unrouted `/ai` and `/analytics`, and its analytics page follow up are resolved by this spec; update them when this ships.
- [ ] Spec 0012: tick the feature 3 follow up (incremental embedding, `ai.embed_catchup_days`, Python `app_settings` read removed) when this ships.
- [ ] `/sync` after the build: root `AGENTS.md` stack table (analytics-ai retired, `/ai` and `/analytics` gone from the gateway), backend-vrms `AGENTS.md` (analytics and AI modules, `AiProvider`, raw SQL for vectors, the catch up job).
