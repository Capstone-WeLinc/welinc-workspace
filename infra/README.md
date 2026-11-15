# infra

The WeLinc suite's setup as code: the gateway image, the Azure resources for staging and production, and the scripts that apply them. The decision and every value's source are in [VRMS spec 0008](../docs/specs/vrms/0008-hosting-and-ci-cd/index.md).

## Files

| Path | What it holds |
|---|---|
| `gateway/` | The nginx gateway image (suite spec 0008), the same locally and hosted |
| `shared.bicep` | `rg-welinc-shared`: the one container registry, its weekly purge (keeps 15 tags per image), AcrPush for every deploy login |
| `subscription.bicep` | The budget alerts at $50, $100, $150 and $180 |
| `env.bicep` | One environment in `rg-welinc-<env>`: PostgreSQL with its seven databases, storage, logs, the Container Apps environment, every app and job of every group, the four Static Web Apps, custom domains, roles |
| `modules/` | The pieces `env.bicep` repeats: one Container App, one job, the platform, PostgreSQL, a Static Web App, the gateway certificate, the access rules |
| `env/<env>.parameters.json` | Settings per environment that are not secret: the domain, which groups are on, their extra settings |
| `env/logins.json` | The deploy logins' ids (not secrets), filled once the app registrations exist |
| `env/region.env` | The Azure region, picked after the quota check |
| `private.example.json` | The shape of `private/<env>.json`, the git ignored secrets file per environment |
| `db/init.sql` | The owner and app role per database, run once per database before its first migration |
| `scripts/` | `apply.sh`, `db-init.sh`, `dns-records.sh`, `set-repo-variables.sh`, `rotate-secret.sh`, `purge-images.sh` |

## Order for a new environment

You need `az` (logged in), `jq`, `psql`, `dig` and `gh`.

1. `infra/scripts/apply.sh shared`, then `apply.sh budget`.
2. Fill `infra/private/staging.json` from the example, then `apply.sh staging --what-if` to preview.
3. `apply.sh staging` (pass 1, default host names; it also runs `db-init.sh`).
4. `dns-records.sh staging`, add the records at the registrar, wait until `dns-records.sh staging --check` passes.
5. `apply.sh staging --domains` (pass 2: certificates and custom domains).
6. Fill `env/logins.json`, run `apply.sh shared` and `apply.sh staging` again (the roles), then `set-repo-variables.sh staging`.

Run `apply.sh <env>` again any time: it keeps each app's current image and changes only what differs.

## Things that bite

- **First image of an app.** A new app starts on Microsoft's placeholder image (port 80, no probes). After its first image is pushed, run `apply.sh <env>` once: it finds the newest pushed image and sets the real port and probes.
- **VMMS and BMS** are off (`enabledGroups: []`) until their S11 moves can deploy. Turning a group on creates its apps and jobs from contract 0001 sections 2 and 3; `groupApps` overrides a health path or adds settings, and their secrets go under `groups` in the private file.
- **A secret change** reaches a running app only after a restart. `rotate-secret.sh` does both; put the value in the private file too, or the next apply sets the old one back.
- **ACR Tasks** can be paused on free credit subscriptions. If `apply.sh shared` fails on the purge task, run it with `PURGE_TASK=false` and run `purge-images.sh` weekly.
