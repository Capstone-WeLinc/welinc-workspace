# 0013. Rationale: analytics and AI into backend-vrms

Back to [index.md](index.md).

## Context

`welinc-backend-vrms-analytics-ai` is a Python FastAPI service that does two jobs for VRMS:
- **Analytics:** 8 endpoints over a DuckDB copy of the VRMS data, cached in Redis.
- **AI triage:** Gemini for the diagnosis text, a separate pgvector Postgres for similar issues, and MongoDB for the interaction log.

A thread copies the VRMS data into those stores every 30 seconds. backend-vrms calls it once (`autoEmbedIssues`). web-vrms calls `/ai/diagnose`, `/ai/feedback`, `/ai/stats` and the 8 `/analytics/*` routes through the gateway. (basis: welinc-backend-vrms-analytics-ai `AGENTS.md`; the code)

What the code actually does, which differs from the intent:
- **Similar issues are noise.** The sync writes **random vectors** seeded by a category word and a hash of the text (`sync_service.py`). The search embeds the question with real Gemini embeddings. The two sit in different vector spaces, so "similar past repairs" is meaningless.
- **Stats are invented when data is missing.** `/ai/stats` returns hardcoded numbers (18 interactions, 94.4% satisfied) whenever Mongo is empty or down.
- **The diagnosis guesses when Gemini fails.** A keyword guesser produces a confident looking answer.
- **The page swaps in fake data.** The web Analytics page shows sample data when any call returns nothing, so exports can carry fake data.
- **Cancelled tickets count as spend**, and months follow UTC.
- **There are no checks.** The service checks no JWT and allows every CORS origin.

Forces:
- **Hosting:** spec 0008 hosts on Azure Container Apps and does not deploy this service, so staging and production have no analytics or AI at all.
- **Fragility:** spec 0010's schema change broke the service until a patch, and spec 0012 had to teach it to read VRMS settings. Every VRMS change now costs a second repo.
- **Team:** the team writes NestJS and Prisma daily; Python is used only here.
- **Deadline:** deployed by the end of November 2026, about four weeks out, with Slice 1 still ahead.
- **Data size:** three garages, thousands of tickets a year at most.

## Options considered

### Option 1: Fix the Python service in place and deploy it

Keep the service, fix the vectors and fallbacks, add JWT checks, and add it plus Redis, Mongo and a second Postgres to Azure.

**Pros**:
- No rewrite of working analytics SQL.
- Python's AI ecosystem stays available.

**Cons**:
- Five more things to host and pay for on student credit, and a second language to maintain.
- The sync keeps lagging, and the service breaks on every VRMS schema change.
- It needs its own permission checks, which would duplicate spec 0011.

### Option 2: Rebuild inside backend-vrms on the VRMS database (chosen)

Port the analytics to live SQL and the AI to a Nest module with an `AiProvider` adapter; use pgvector and two Postgres tables in the VRMS database; delete the rest.

**Pros**:
- One service and one database; analytics and AI reach Azure with no new infrastructure.
- Spec 0011 permissions and spec 0012 module switches apply for free.
- No sync, so numbers are always current.

**Cons**:
- The analytics SQL and AI code must be rewritten in TypeScript.
- Analytics load lands on the live database.
- Prisma 7 has no vector type, so vector access is raw SQL.

### Option 3: Analytics now, AI later

Move only analytics into backend-vrms now; leave AI in Python until feature 47 rebuilds it.

**Pros**:
- The smallest piece of work; it fixes the analytics page on Azure soonest.

**Cons**:
- AI stays undeployed and keeps its broken vectors and three extra stores until feature 47.
- The Python repo lives on, with its settings read and schema coupling.

### Option 4: Port and also build the new AI ideas

Do Option 2 plus grounding, triage while typing, search by meaning, note cleanup, drafted entries and duplicate warnings.

**Pros**:
- One pass through the AI code.

**Cons**:
- It roughly doubles the work and absorbs feature 47, which risks the November deadline.

## Rationale

Option 2 removes the root cause rather than the symptoms. Most of the defects listed in Context come from the copy and sync design and from a second service living outside the permission system. Option 1 keeps both, and adds five hosted components the student credit can't easily carry (basis: spec 0008 hosting). Option 3 fixes analytics but leaves AI undeployed and still broken. Option 4 is right in direction but wrong in timing with Slice 1 still ahead. (basis: strangler pattern; monolith first for a small team)

Within Option 2:
- **Live SQL with no cache:** each query scans at most thousands of rows. A cache would add staleness and invalidation for no measured gain. (basis: measure before you optimise)
- **pgvector in the VRMS database:** it keeps vectors next to their issues, and Azure Database for PostgreSQL allows the `vector` extension. Skipping the vector index sidesteps the HNSW crash reports, since an exact scan is instant at this size.
- **Postgres tables replace MongoDB:** a few hundred diagnosis documents fit `jsonb` columns that are backed up with the tickets and join to them. (basis: relational data in a relational store)

Provider: **Gemini behind `AiProvider`**. It is the only option that is free at capstone volume, offers embeddings and generation in one account, and enforces JSON output against a schema. Azure OpenAI keeps data inside the tenant and is never used for training, but community reports say Azure for Students subscriptions cannot deploy OpenAI models, and it would spend the hosting credit. Claude needs a second provider (Voyage) for embeddings. Ollama has no realistic GPU home on Container Apps by November. The adapter keeps feature 47 free to switch. The free tier's data use is the accepted cost; a paid key removes it with no code change.

Models, checked 2026-10-30 against the project's Rate Limit page and live calls: the full Flash models (3 Flash, 3.6, 3.8) allow only 20 requests a day free, which three garages would use up in minutes, so the diagnosis uses `gemini-3.5-flash-lite` (500 a day) and returned valid schema constrained JSON. Embeddings use `gemini-embedding-2`: its own 1K a day bucket, 8192 token input, 768 values already length 1, and it is the model the docs describe as multilingual (useful for Taglish). `gemini-embedding-001` is the fallback. Gemma 4 (14.4K a day) was not chosen because its JSON output reliability is untested.

Failure handling: an honest 503 beats today's keyword guesser, because a confident wrong diagnosis on a truck is worse than none. A word matching fallback for similar repairs was rejected: it is a second search path built only for outages.

## Evidence: metric definitions carried over

| Python endpoint | Old source | Port change |
|---|---|---|
| `cost-trends`, `vehicle-kpis`, `summary`, `issue-frequency` | DuckDB mart built by `duckdb_refresh.py` from all tickets | live SQL; cancelled tickets excluded; Manila months |
| `status-breakdown`, `garage-costs`, `aging`, `velocity` | direct psycopg2 queries on VRMS | same SQL in Nest; `garage-costs` excludes cancelled; Manila months for `velocity` |
| `/ai/stats` | Mongo aggregate, hardcoded on empty | SQL aggregate, zeros on empty |
| `/ai/logs`, `/ai/knowledge/articles`, `/ai/embed-issue` | Mongo, Postgres, pgvector | dropped (no web caller; embedding moves inside backend-vrms) |

## References

**Project sources**:
- welinc-backend-vrms-analytics-ai `AGENTS.md` and code (`sync_service.py`, `ai_service.py`, `analytics_service.py`, `duckdb_refresh.py`)
- Spec 0007 (knowledge base, the `autoEmbedIssues` follow up), spec 0008 (hosting, analytics not deployed), spec 0010 (data model v2), spec 0011 (permission matrix, cost nulling), spec 0012 (module switches, the feature 3 follow up)
- welinc-backend-vrms `package.json` (Prisma 7.8, `@nestjs/schedule` already installed)
- Scope feature 3 notes in `docs/scope/foundations.md`

**Practices & standards**:
- Strangler pattern for replacing a live system
- Monolith first for a small team; no premature services
- Measure before you optimise (no cache without a measured slow query)
- Deny by default, enforced on the server (OWASP authorization)

**Links** (web verified 2026-10-30):
- Gemini API pricing (free tier, data use per tier): https://ai.google.dev/gemini-api/docs/pricing
- Gemini embeddings (`gemini-embedding-001`, `output_dimensionality`, task types): https://ai.google.dev/gemini-api/docs/embeddings
- Gemini structured output: https://ai.google.dev/gemini-api/docs/structured-output
- Gemini SDK libraries (`@google/genai`, legacy SDK deprecated): https://ai.google.dev/gemini-api/docs/libraries
- Azure Database for PostgreSQL, allow extensions: https://learn.microsoft.com/en-us/azure/postgresql/extensions/how-to-allow-extensions
- Azure Database for PostgreSQL release notes (pgvector 0.8.0): https://learn.microsoft.com/en-us/azure/postgresql/release-notes/release-notes
- Azure OpenAI data privacy: https://learn.microsoft.com/en-us/azure/foundry/responsible-ai/openai/data-privacy
- Azure OpenAI on Azure for Students (community Q&A, not official): https://learn.microsoft.com/en-us/answers/questions/2183197/azure-openai-with-azure-for-students
