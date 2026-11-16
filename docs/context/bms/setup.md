# BMS local setup

Use Node 24, npm and Docker Desktop. The workspace's shared instructions remain
in [move-bms.md](../../integration/move-bms.md). BMS's service ownership and ports
are in its [backend README](../../../welinc-backend-bms/README.md).

## This configured workspace

Local auth signing keys and the BMS client key have been generated with the
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
missing BMS secrets while retaining configured values. Analytics has its own
optional AI configuration. Compose supplies browser API/portal addresses and
all owned database URLs. Never place server secrets in `VITE_*` variables.

## Migrations and seeds after a pull

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

Run the commands in [verification.md](verification.md). Do not tick lead
acceptance from unit tests alone. Live VMMS parity and assignment checks,
VRMS-token rejection in the shared live checker, coordinated PR review and
written sign-off remain external gates listed in the
[integration checklist](integration-checklist.md).
