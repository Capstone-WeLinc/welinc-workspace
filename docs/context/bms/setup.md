# BMS local setup

Use Node 24, npm and Docker Desktop. The workspace's shared instructions remain
in [move-bms.md](../../integration/move-bms.md). BMS's service ownership and ports
are in its [backend README](../../../welinc-backend-bms/README.md).

## This configured workspace

Local auth signing keys and distinct BMS/analytics client keys have been generated with the
shared service's shipped key commands. Shared auth and BMS migrations and seeds
have applied. Environment values are private; do not print or paste them.

Start the shared stack first, then BMS, from `welinc-workspace`:

```sh
docker compose -f docker-compose.shared.yml up -d
docker compose -f docker-compose.bms.yml up -d
```

Use `--build` after changing dependencies or Dockerfiles. Bind-mounted source
watching may miss Windows filesystem events; restart the affected BMS service
if it still serves an older route after an edit.

- Sign in: <http://localhost:8000>
- BMS app: <http://localhost:8003>
- BMS readiness: <http://localhost:3000/bms/health>
- Local seed identities: [suite seed guide](../../integration/seed-accounts.md)

The office web client admits Admin, Customer Support and Operations through
shared auth. Driver/helper accounts are reserved for the mobile client. VMMS
being unavailable does not prevent BMS login. Its vehicle-dependent screens
will report fleet unavailability until VMMS serves the fleet API.

## Fresh clone / lead handoff

For actual Git repositories, follow the shared guide in Git Bash on Windows:

```sh
sh scripts/setup.sh bms
```

BMS's root npm postinstall creates missing internal/tracking secrets without
printing values. The shared setup generates/registers the BMS client key,
starts the shared stack first, builds BMS, applies each service's migrations
and runs its repeatable seed. The current local source copies deliberately
have no Git metadata, so the shared clone/branch/PR workflow was not run over
them. This workspace was configured using the equivalent shipped key,
Compose, migration and seed commands.

The backend root `.env.example` documents shared names and optional booking
integrations. Run `npm --prefix welinc-backend-bms run prepare:local` to prepare
missing BMS secrets while retaining configured values. Analytics has its own `bms-analytics` client/key and optional AI configuration
in its own environment. It does not inherit the root BMS environment. Compose supplies browser API/portal addresses and
all owned database URLs. Never place server secrets in `VITE_*` variables.

## Migrations and seeds after a pull

Bring existing BMS environment files up to date without replacing configured
values. This command appends missing names and prints names only:

```sh
node scripts/sync-env.mjs welinc-backend-bms welinc-backend-bms-analytics-ai welinc-web-bms
```

Groq's server-side `GROQ_API_KEY` and optional fallback `GROQ_MODEL` belong in
`welinc-backend-bms-analytics-ai/.env`. Google/SMTP server settings belong in
`welinc-backend-bms/.env`; the browser Maps key belongs in
`welinc-web-bms/.env` as `VITE_GOOGLE_MAPS_API_KEY`. After changing environment
files, recreate the affected Compose services with `up -d --force-recreate` so
the container environment is refreshed.

From the workspace, apply migrations and run seeds for each owning service:

```sh
docker compose -f docker-compose.bms.yml exec -T bms-booking npx prisma migrate deploy
docker compose -f docker-compose.bms.yml exec -T bms-booking npm run seed
docker compose -f docker-compose.bms.yml exec -T bms-dispatch npx prisma migrate deploy
docker compose -f docker-compose.bms.yml exec -T bms-dispatch npm run seed
docker compose -f docker-compose.bms.yml exec -T bms-completion npx prisma migrate deploy
docker compose -f docker-compose.bms.yml exec -T bms-completion npm run seed
docker compose -f docker-compose.bms.yml exec -T bms-analytics npx prisma migrate deploy
docker compose -f docker-compose.bms.yml exec -T bms-analytics npm run seed
```

BMS uses fresh owned volumes on host database ports 5434 through 5437. Seeds
preserve existing records and edited crew profiles. Do not reset or delete
unrelated Docker volumes. The projection retries until its owned schema and
source services are ready; readiness is 503 until its first successful cycle.

## Verification and delivery

Run the commands in [verification.md](verification.md). The lead's updated
17 November checklist reports login 16/16, fleet 5/5 and a clean scan on the
coordinated PR branches. That is lead-reported evidence; it does not mean the
local VMMS checkout has the endpoint or that new hosting changes are deployed.
Official hosting PR checks, private provider keys, Azure deployment and written
sign-off remain with the leads. See [hosting-handoff.md](hosting-handoff.md).

## Full default demo

After the migrations and baseline commands above, with the actual VMMS fleet
API and shared auth/directory running:

```sh
npm --prefix welinc-backend-bms run seed
```

This creates 150 demo scenarios, linked operational/payment records and the
analytics projection without creating accounts or vehicles. It preserves edits
and resumes interrupted runs. If VMMS is unavailable, baselines can still seed,
but operational demo creation stops with a clear fleet prerequisite error.
Every seed refuses production unless a staging job has `SEED_ALLOW=staging`.
For hosted owner-job order and manifest handling, use the hosting handoff.
