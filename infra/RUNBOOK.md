# Runbook

How to run, recover and shut down the hosted WeLinc suite. **Only staging is hosted** (VRMS spec 0008 AC-24); production exists as code only. Setup order and the scripts are in [README.md](README.md). Commands assume the Mac (`az` is `~/.local/bin/az`), run from the workspace root.

## Key facts

| What | Value |
|---|---|
| Subscription | the Azure free trial ($200 credit, 30 days from signup) |
| Credit end date | **Dec 18, 2026** (from the subscription's Overview, recorded Nov 20). The shutdown copy must happen before it |
| Resource groups | `rg-welinc-shared` (registry), `rg-welinc-staging` (everything else) |
| Database server | `psql-welinc-staging`, admin `welincadmin`, password in `infra/private/staging.json` (1Password) |
| Budget alerts | $50, $100, $150, $180 (Cost Management, Budgets) |
| Defense days | Nov 28, Dec 4, Dec 5 |

## The defense freeze

No merge to `development` in any repo (ours or the other groups') from 2 hours before each defense until it ends: every merge redeploys the demo. A fix in that window only on the lead's call, then check staging (`/health` on each route, one sign in). Never stop staging, apply, or rotate a secret in the window either.

## Opening the database to your laptop

The server only accepts Azure services. For `psql`, `pg_dump` or a restore check, open your IP for the session and close it after:

```bash
IP=$(curl -s https://api.ipify.org)
~/.local/bin/az postgres flexible-server firewall-rule create -g rg-welinc-staging \
  --server-name psql-welinc-staging --name laptop --start-ip-address $IP --end-ip-address $IP
# ... work ...
~/.local/bin/az postgres flexible-server firewall-rule delete -g rg-welinc-staging \
  --server-name psql-welinc-staging --name laptop --yes
```

`apply.sh` opens and closes its own rule. The local `psql` is 14; for `pg_dump` against the version 16 server use the container: `docker run --rm -e PGPASSWORD postgres:16 pg_dump ...`.

## Rollback

- **Normal:** revert the bad change with a pull request into `development`; the deploy ships the revert. Migrations only add, so older code runs on the newer database.
- **Faster, one app:** point it back at its previous image (the registry keeps the newest 15 tags of each):
  ```bash
  ~/.local/bin/az acr repository show-tags -n <registry> --repository vrms-backend --orderby time_desc --top 5
  ~/.local/bin/az containerapp update -n vrms-backend-staging -g rg-welinc-staging \
    --image <registry>.azurecr.io/vrms-backend:<previous sha>
  ```
  The next merge into `development` deploys over it, so revert the code too.

## Rotating secrets and keys

- **One setting on one app or job:** `bash infra/scripts/rotate-secret.sh staging <app or job>-staging <SETTING>`. It reads the value without echo and restarts the revision (a running revision keeps the old value until then). Put the same value in `infra/private/staging.json`, or the next apply sets the old one back.
- **welinc-auth's signing keys:** `npm run keys:rotate` in welinc-auth, following its `docs/keys.md` (add, wait, promote, wait, remove).
- **A client key** (`vrms`, `vmms`, `bms`, `bms-analytics`): `npm run keys:client` in welinc-auth, then the private half on that app and the public half on auth, both through `rotate-secret.sh`.

## Stopping staging (saves the credit)

Never in the defense window. Scale every app to zero and stop the database:

```bash
RG=rg-welinc-staging; AZ=~/.local/bin/az
for app in $($AZ containerapp list -g $RG --query "[].name" -o tsv); do
  $AZ containerapp update -n $app -g $RG --min-replicas 0 -o none; done
$AZ postgres flexible-server stop -g $RG -n psql-welinc-staging
```

Start again with `az postgres flexible-server start -g rg-welinc-staging -n psql-welinc-staging`, then `PATH="$HOME/.local/bin:$PATH" bash infra/scripts/apply.sh staging --domains` (it puts the replica rule back). Azure starts a stopped server by itself after 7 days.

## Applying staging

Always `bash infra/scripts/apply.sh staging --domains` (and `--what-if` first). Without `--domains` the gateway gets an empty custom domain list and `staging-api.welinc.app` goes down.

## The environment lock

`keep-cae-welinc-staging` (CanNotDelete) protects the Container Apps environment and everything under it. To delete a certificate or storage on it, lift the lock, delete, then put it back by hand:

```bash
~/.local/bin/az lock delete -g rg-welinc-staging -n keep-cae-welinc-staging \
  --resource-type Microsoft.App/managedEnvironments --resource cae-welinc-staging
~/.local/bin/az lock create -g rg-welinc-staging -n keep-cae-welinc-staging --lock-type CanNotDelete \
  --resource-type Microsoft.App/managedEnvironments --resource cae-welinc-staging \
  --notes "Staging's Container Apps environment: delete only on purpose"
```

## DNS and mail records

`welinc.app` is at Name.com. Print the staging records with `PATH="$HOME/.local/bin:$PATH" bash infra/scripts/dns-records.sh staging` (and `--check` to test them): CNAMEs for `staging-api`, `staging-portal`, `staging-vrms`, `staging-vmms`, `staging-bms`, plus the `asuid.staging-api` TXT. Brevo's records (its domain code TXT, the DKIM records and a DMARC TXT, no SPF) are listed in Brevo under Senders, domains & dedicated IPs, Domains, `welinc.app`.

## One time bootstrap (a new subscription)

1. Resource providers, resource groups and the budget: `apply.sh shared`, `apply.sh budget` (it registers `Microsoft.App`, `OperationalInsights`, `ContainerRegistry`, `DBforPostgreSQL`, `Web`, `Storage`).
2. `infra/private/staging.json` from 1Password, then `apply.sh staging` (pass 1, runs `db-init.sh`).
3. DNS records at Name.com, wait for `dns-records.sh staging --check`, then `apply.sh staging --domains`.
4. Entra app registrations: one deploy login per group plus the purge login, with GitHub federated credentials; fill `env/logins.json`, run `apply.sh shared` and `apply.sh staging` again, then `set-repo-variables.sh staging`.
5. Brevo: add `welinc.app`, its records, and the sender `WeLinc <noreply@welinc.app>`.
6. Branches: `main` in auth, backend-vrms, web-portal and web-vrms was fast forwarded to `development` by hand twice (Nov 19, and Nov 20 to carry the production guard). A new subscription needs neither: nothing deploys from `main` while production isn't hosted.
7. Push to `development` in each repo (deploys), then run the `auth-seed-staging` and `vrms-seed-staging` jobs once.

## Moving to another subscription

1. Take the copies in *Shutdown copy* below.
2. Bootstrap the new subscription (above), which recreates everything empty.
3. Restore each database: open the new server to your laptop, then `docker run --rm -i -e PGPASSWORD postgres:16 pg_restore -h <new server> -U welincadmin -d <db> --no-owner --role=<db>_owner < <db>.dump`.
4. Upload the blob container and the file share copies (`az storage blob upload-batch`, `az storage file upload-batch`).
5. Point the DNS records at the new addresses (`dns-records.sh staging` prints them), then `apply.sh staging --domains`.

## Bringing production up later

Production is code only because the trial refused its B1ms database server (`SkuNotAvailable`). To bring it up: get a server first (an Azure support request for B1ms in Southeast Asia, or AWS RDS `db.t4g.micro` in Singapore; never production's databases on staging's server). Then fill `infra/private/prod.json` from 1Password, `apply.sh prod` (twice: once before and once after the first deploys), add its DNS records, `apply.sh prod --domains`, `set-repo-variables.sh prod`, set `AZURE_CLIENT_ID_PROD` (which lifts the deploy guard), and promote `development` to `main` in each repo. The full steps are spec 0008 task 19.

## Shutdown copy (after Dec 5, before the credit ends)

1. Open the database to your laptop (above).
2. Dump every database:
   ```bash
   export PGPASSWORD=$(jq -r .postgresAdminPassword infra/private/staging.json)
   for db in auth vrms vmms bms_booking bms_dispatch bms_completion bms_analytics; do
     docker run --rm -e PGPASSWORD postgres:16 pg_dump -Fc \
       -h psql-welinc-staging.postgres.database.azure.com -U welincadmin -d $db > $db.dump; done
   ```
3. Copy the VRMS blob container and the auth file share with `az storage blob download-batch` and `az storage file download-batch`.
4. Keep the copies on your machine and one teammate's. Record the date here: ________
5. Close the firewall rule, then set `warmAll` to `false` in `infra/env/staging.parameters.json` and apply, or stop staging (above).

## Restore drill (VRMS spec 0008 AC-8, task 20)

Backups are automatic, kept 14 days. **Drill, 2026-11-20:**

- A point in time restore of `psql-welinc-staging` to 21:40:32 UTC into `psql-welinc-restore` was **refused** by Azure (`SkuNotAvailable`, the same B series block that stopped production). Azure removed the failed server by itself. So the managed restore can't be tested on this trial.
- Fallback, as the spec plans: `pg_dump -Fc` of `auth` and `vrms` from staging (Postgres 16 client), restored into a local `pgvector/pgvector:pg16` container with `pg_restore --no-owner --no-privileges`. No restore errors.
- Exact row counts of every table, staging against the copy: **`auth` 23 tables, 737 rows, all match; `vrms` 32 tables, 19,263 rows, all match.** (The counts query is in *Counting rows* below.)
- The dumps were deleted and the laptop firewall rule closed the same day.

If staging's server is ever lost on this trial, a point in time restore will likely be refused too: recover from the newest `pg_dump` copy instead (*Moving to another subscription*, step 3).

### Counting rows

```sql
select table_schema||'.'||table_name as t,
 (xpath('/row/c/text()', query_to_xml(format('select count(*) as c from %I.%I', table_schema, table_name), false, true, '')))[1]::text::bigint as n
from information_schema.tables
where table_schema not in ('pg_catalog','information_schema') and table_type='BASE TABLE' order by 1;
```

## Error monitoring: the Sentry org (VRMS spec 0025)

Set up by hand once, on 2026-11-17. Everything below lives in Sentry, not in this repo, so this is the record of how it was set.

### The org

- **Org:** `welinc` (https://welinc.sentry.io), region **United States**. The region can't be changed later; a new region means a new org and new DSNs everywhere.
- **Plan:** the GitHub Student Pack offer (50k errors a month for a year) if the claim went through, else the free Developer plan (5k errors, 1 seat, 1 cron monitor, 1 uptime monitor). The setup fits the free plan either way. Check under Settings → Subscription.
- **Owner:** Samuel. Groupmates join as members only once the student plan is active (the free plan has one seat).
- **GitHub:** the Sentry GitHub app is installed on `Capstone-WeLinc` with access to only `welinc-backend-vrms`, `welinc-web-vrms`, `welinc-auth` and `welinc-web-portal` (Settings → Integrations → GitHub). It gives suspect commits and links from stack frames to code.
- Save the login in 1Password.

### The four projects

| Project | App | Platform |
|---|---|---|
| `vrms-backend` | welinc-backend-vrms | NestJS |
| `vrms-web` | welinc-web-vrms | React |
| `welinc-auth` | welinc-auth | NestJS |
| `welinc-portal` | welinc-web-portal | React |

Each project tells environments apart by `environment` (only staging is hosted). To add one: Projects → Create Project, pick the platform, name it as above, and skip Sentry's install steps and its agent prompt (the SDKs are already set up in the code; the wizard would overwrite the privacy settings). A renamed project keeps its DSN.

Each project's DSN is under Project Settings → Client Keys (DSN). A DSN can only send events, so it isn't a secret, but keep a copy in 1Password with the others. Where each DSN goes is in spec 0025's value sourcing table.

### Privacy settings (org wide)

Settings → Security & Privacy (https://welinc.sentry.io/settings/security-and-privacy/), section **Data Scrubbing**. At the org level these switches read "Require…", and on means every project gets them.

- **Require Data Scrubber:** on
- **Require Using Default Scrubbers:** on
- **Prevent Storing of IP Addresses:** on
- **Global Sensitive Fields**, one per line:

```
code
otp
setupCode
reauthToken
refreshToken
accessToken
password
email
name
phone
city
region
```

`city` and `region` were added during the first live test, beyond spec 0025's list. Sentry works out a location from the address a report came from even with IP storage off, and it does so before the scrubbers run. These two lines (with `code`, which already catches `countryCode`) blank that location. The list also blanks harmless fields with the same names, such as a stack local called `name`; that is accepted.

Check after any change: send a test error (below) and open it. The user should show only an id, and `geo` should read `[Filtered]` throughout.

### Alert rules

One alert covers all four projects: **New or regressed issue (spec 0025)** (https://welinc.sentry.io/monitors/alerts/6357875/). It fires on a new issue and on a regression (a resolved issue comes back), in every environment, and emails the issue owners, falling back to the active members (you). The email names the environment.

Sentry also makes a "Send a notification for high priority issues" rule for each new project. Those are disabled so one problem sends one email. A project added later gets one too: disable it, and add the project to the alert above (Alerts → the alert → Edit → Connected projects).

### Monitors (the free plan's one cron and one uptime slot)

Both watch staging and live in the `vrms-backend` project. Neither has an alert of its own: a failure opens an outage issue, and the alert above emails it.

- **Cron, `vrms-directory-poll`** (https://welinc.sentry.io/crons/vrms-backend/vrms-directory-poll/): made by the backend's first check in (spec 0025 task 8), not by hand. Every 5 minutes, margin 5, max runtime 2. A miss or an `error` check in opens "Cron failure: vrms-directory-poll".
- **Uptime, VRMS health (staging)** (https://welinc.sentry.io/monitors/11012202/): created 2026-11-20 through the Sentry MCP server. `GET https://staging-api.welinc.app/vrms/health` every 60 s, timeout 10 s, down after 3 failed checks in a row, up after 1 good one, owner team `welinc`, environment `staging`, captures the response on failure. One call proves the gateway, the VRMS backend and its database.

A local backend must use `SENTRY_ENVIRONMENT=development` (or no DSN). With `staging` its check ins land on the staging monitor, and when it stops (a branch switch, the laptop sleeping) the monitor reports misses that aren't real (seen 2026-11-20, issue VRMS-BACKEND-7).

### Sending a test error

- **backend-vrms** (staging, or locally with `SENTRY_TEST_ROUTES=true`): `POST /vrms/debug/sentry-test` as a user with `settings.manage` answers 500 and creates one issue. Sentry drops an error identical to the last one from the same process, so a second identical call sends nothing until the app restarts.
- **web-vrms** (a build with `VITE_SENTRY_TEST_ROUTES=true`): open `/debug/sentry` as a user with `settings.manage` and press Crash this page. The crash screen's reference code matches the start of the event id.

## A person stops getting emails (suite spec 0009, AC-34)

Brevo adds an unsubscribe header to every email, and we can't remove it on our plan. When someone clicks **Unsubscribe** in Gmail, Brevo blocks that exact address, and from then on its sign in, setup and reset codes never arrive. Each plus tagged seed address in the team inbox (`welinc.demo+vrms.admin@gmail.com`, and so on) is its own entry, so one click blocks one seed account.

- **Check:** in Brevo, open Transactional, then the blocked contacts list. It shows each blocked address and why (unsubscribed, hard bounce, spam complaint, admin block).
- **Unblock:** remove the address from that list. Or call the API with a Brevo API key (a key with only this use is enough; keep it in 1Password, never in a repo):
  ```bash
  curl -X DELETE -H "api-key: $BREVO_API_KEY" \
    "https://api.brevo.com/v3/smtp/blockedContacts/welinc.demo%2Bvrms.admin%40gmail.com"
  ```
  Encode `+` as `%2B` and `@` as `%40`. It answers 204 when unblocked, 404 when the address wasn't blocked.
- **Before each defense** (Nov 28, Dec 4, Dec 5): check that the blocked list holds none of the team inbox addresses or your own.
- A spam complaint can block an address again; if the same address keeps coming back, mark the email "Not spam" in that inbox.
