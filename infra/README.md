# infra

The WeLinc suite's setup as code: the gateway image, the Azure resources for staging and production, and the scripts that apply them. The decision and every value's source are in [VRMS spec 0008](../docs/specs/vrms/0008-hosting-and-ci-cd/index.md).

## Files

| Path | What it holds |
|---|---|
| `gateway/` | The nginx gateway image (suite spec 0008), the same locally and hosted |
| `shared.bicep` | `rg-welinc-shared`: the one container registry, its weekly purge (keeps 15 tags per image; on the trial a workspace workflow does it), AcrPush for every deploy login, Reader and AcrDelete for the purge login |
| `subscription.bicep` | The budget alerts at $50, $100, $150 and $180 |
| `env.bicep` | One environment in `rg-welinc-<env>`: PostgreSQL with its seven databases, storage, every app and job of every group (each name ending in `-staging` or `-prod`), the four Static Web Apps, custom domains, roles. Staging also makes the one Container Apps environment and its logs; production joins it |
| `modules/` | The pieces `env.bicep` repeats: one Container App, one job, the platform, PostgreSQL, a Static Web App, the gateway certificate, the environment storage, production's joiner role and delete locks (`env-guard.bicep`), the access rules |
| `env/<env>.parameters.json` | Settings per environment that are not secret: the domain, which groups are on, their extra settings |
| `env/logins.json` | The deploy logins' ids (not secrets), filled once the app registrations exist |
| `env/region.env` | The Azure region, picked after the quota check |
| `private.example.json` | The shape of `private/<env>.json`, the git ignored secrets file per environment |
| `db/init.sql` | The owner and app role per database, run once per database before its first migration |
| `scripts/` | `apply.sh`, `db-init.sh`, `dns-records.sh`, `set-repo-variables.sh`, `rotate-secret.sh`, `purge-images.sh`; `scripts/check-names.mjs` at the workspace root checks every name fits 32 characters (workspace CI) |

## Order for a new environment

You need `az` (logged in), `jq`, `psql`, `dig` and `gh`.

Staging first: it makes the Container Apps environment production runs in.

1. `infra/scripts/apply.sh shared`, then `apply.sh budget`.
2. Fill `infra/private/staging.json` from the example, then `apply.sh staging --what-if` to preview.
3. `apply.sh staging` (pass 1, default host names; it also runs `db-init.sh`).
4. `dns-records.sh staging`, add the records at the registrar, wait until `dns-records.sh staging --check` passes.
5. `apply.sh staging --domains` (pass 2: certificates and custom domains).
6. Fill `env/logins.json`, run `apply.sh shared` and `apply.sh staging` again (the roles), then `set-repo-variables.sh staging`.
7. Production: the same steps with `prod`. `apply.sh prod` stops if `cae-welinc-staging` doesn't exist. Its pass 1 starts every app on the placeholder; run `apply.sh prod` again after the first production deploys (the next section).

Run `apply.sh <env>` again any time: it keeps each app's current image and changes only what differs.

## Things that bite

- **First image of an app.** A new app starts on Microsoft's placeholder image (port 80, no probes), so its first deploy fails at the revision wait. On staging, run `apply.sh staging` once after its first image is pushed: it finds the newest pushed image and sets the real port and probes. On production, `apply.sh prod` never takes a registry image (production runs only what its own deploys set): run the first production deploys, then `apply.sh prod` (it reads the image each deploy set and fixes the port), then rerun those deploys.
- **VMMS and BMS** are off (`enabledGroups: []`) until their S11 moves can deploy. Turning a group on creates its apps and jobs from contract 0001 sections 2 and 3; `groupApps` overrides a health path or adds settings, and their secrets go under `groups` in the private file.
- **A secret change** reaches a running app only after a restart. `rotate-secret.sh` does both; put the value in the private file too, or the next apply sets the old one back.
- **One Container Apps environment in the whole subscription** on the trial (`MaxNumberOfGlobalEnvironmentsInSubExceeded`), so production's apps run in staging's `cae-welinc-staging`, in the same region (`PROD_LOCATION` in `env/region.env` must equal `LOCATION`; `apply.sh` checks). See *Shared environment* below.
- **ACR Tasks** can be paused on free credit subscriptions. If `apply.sh shared` fails on the purge task, run it with `PURGE_TASK=false` (the default in `env/region.env` on the trial); `.github/workflows/purge-images.yml` then runs `purge-images.sh` every Sunday.

## Shared environment (spec 0008 AC-23)

- **Names.** Every app and job is `<base name>-staging` or `<base name>-prod` (`auth-service-prod`, `vrms-migrate-staging`), and so are the environment storage (`auth-uploads-<env>`) and the gateway certificate (`cert-api-<env>`). No bare name exists. Image repositories keep the base names (`auth-service`, `vrms-backend-seed`), so production deploys the image staging built. Commands that name an app or job (`az containerapp …`, `az rest` on a job, `rotate-secret.sh`) take the full name.
- **Group settings that name another app** (a BMS service calling `bms-booking`) go in each environment's `groupApps` in `env/<env>.parameters.json` with that environment's ending: `https://bms-booking-staging.internal.<domain>` in staging's file, `https://bms-booking-prod.internal.<domain>` in production's. The `groupApps` keys stay the base names.
- **Where production's parts live.** Its apps, jobs, databases, storage accounts and pull identity are in `rg-welinc-prod`. Its environment storage, certificate, the `WeLinc environment joiner` role and the delete locks are in `rg-welinc-staging`, on the environment. Rotating production's files account key means running `apply.sh prod` again (the environment storage reads the key at apply time).
- **Never delete `rg-welinc-staging` or `cae-welinc-staging` while production runs.** Stopping staging means scaling staging's apps to zero and stopping its PostgreSQL server, nothing else (the runbook). Production's apply puts `CanNotDelete` locks on the environment, `cert-api-prod` and `auth-uploads-prod`.
- **The environment lock covers what's under it.** A lock on `cae-welinc-staging` also stops deleting any certificate or storage on it, staging's included. To delete one of staging's (the old `cert-api` and `auth-uploads` in task 18a steps 5 and 6), lift the lock, delete, and put it back by running `apply.sh prod` again:

  ```bash
  az lock delete -g rg-welinc-staging -n keep-cae-welinc-staging \
    --resource-type Microsoft.App/managedEnvironments --resource cae-welinc-staging
  ```
- **Logs.** Both environments' logs go to `log-welinc-staging` (logs are set per Container Apps environment). Filter by `ContainerAppName_s`, for example `ContainerAppConsoleLogs_CL | where ContainerAppName_s == "auth-service-prod"`.
- **A change to the environment hits both.** Only `apply.sh staging`, run by you, changes it; no workflow does.
