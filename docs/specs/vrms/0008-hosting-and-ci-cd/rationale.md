# 0008 rationale: Host on Azure with GitHub Actions for CI and CD

Build spec: [index.md](index.md)

## Context

> ⚠️ Premise note: the plan to "rotate between each of us" on credit rests on a rule nobody has confirmed. Azure for Students is one account per person, the offer page says nothing about sharing credit, and when credit runs out Microsoft disables the subscription and its products. The spec therefore uses one subscription that teammates join as members, recreatable by Bicep, instead of a system that depends on moving between accounts. Also, the scope still says "Vercel for frontends, Render for services" and "pushing to main deploys to staging". Azure replaces the first, and every service repo here merges into `development`, not `main`, so the spec uses `development`.

WeLinc VRMS has five repos of its own: two React apps, two NestJS services and a Python analytics service, plus a shared Postgres setup. Today everything runs from three docker compose files on a developer laptop, with an nginx gateway on port 3000 in front. There is no automated check on any repo, no workflow files, and no place other than a laptop where the system runs.

The deadline is deployment by the end of November 2026, about five weeks away. The team has free Azure credit (probably the $100 student type, not confirmed) and a GitHub organization on the Free plan with private repos. That plan cannot enforce branch protection, required checks, or required reviewers on deployments.

Production images already exist (`Dockerfile.prod` in four repos), but the NestJS ones expose port 3000 while the apps read `PORT`, they do not copy `prisma.config.ts` which Prisma 7 needs to run migrations, and they do not copy `tsconfig.json`, which the seed command needs. The frontends read their API address when built, so each environment needs its own build. The NestJS services have no health endpoint. Locally the gateway reflects any origin in its CORS answer.

Without a decision the team has no repeatable way to show a slice from anywhere but a laptop, and nothing stops a broken merge.

## Options considered

### Option 1: Static Web Apps, Container Apps and PostgreSQL Flexible Server

The two SPAs on Static Web Apps, the services and gateway on Container Apps, one shared managed PostgreSQL server, images in Azure Container Registry, Bicep for the setup, GitHub Actions for CI and CD.

**Pros**:
- Frontends are free and include HTTPS and a CDN.
- Container Apps runs the existing images, scales to zero and has a monthly free usage grant.
- Managed PostgreSQL gives backups and restore, which meets the "scheduled backups" goal without writing it.
- Bicep makes the setup recreatable in another subscription.

**Cons**:
- Many Azure parts for a student team to learn (registry, jobs, identity, Bicep).
- The database server is the biggest fixed cost and is shared by both environments.
- Production keeps three apps always running.

### Option 2: One Azure VM running docker compose

A single small virtual machine running the compose files, with HTTPS and backups set up by hand.

**Pros**:
- Closest to how the team runs things now, the fewest new concepts.
- Lowest listed price for a single machine.

**Cons**:
- The team owns the operating system, certificates, restarts, updates and database backups.
- Staging and production on one machine are not isolated, and the machine is a single point of failure.
- Hard to meet "production deploys need approval and a smoke test" without building that tooling.

### Option 3: App Service for Containers with PostgreSQL Flexible Server

The services on App Service plans instead of Container Apps, everything else the same.

**Pros**:
- A simple, well known model with deployment slots.

**Cons**:
- A paid plan is always on, so idle staging still uses credit.
- No scale to zero, and two environments mean two or more plans.

### Option 4: Keep the earlier plan, Vercel for frontends and Render for services

The plan recorded in the scope before the team had Azure credit.

**Pros**:
- Simple dashboards and fast first deploys.

**Cons**:
- Splits the system over several vendors and several sets of settings while the team already has Azure credit.
- The earlier plan was never confirmed in Jira (the scope says Jira was not updated), and the team has now decided on Azure.

## Rationale

Option 1 fits the forces in Context. The deadline is five weeks and the team is small, so the choice has to work with the images that already exist, and it does: Container Apps runs `Dockerfile.prod` as is, and Static Web Apps runs a plain Vite build for free. The credit is limited and its type is unconfirmed, so the design spends credit only where it must: scale to zero for staging, free frontends, one shared database server, and a budget alert. Managed PostgreSQL is worth its cost because the scope requires scheduled backups and a student team should not be writing backup tooling in the last weeks.

Option 2 is cheaper and simpler to start but fails the isolation, approval and backup goals, and its operating burden lands on the busiest weeks. Option 3 spends credit on idle capacity. Option 4 is dropped because the team chose Azure and consolidating on one vendor is simpler to explain and hand over.

The engineer chose each layer in the design walk and every pick matched the recommendation. Two calls were made here. Production runs three apps at minimum one replica, because the first login after a cold start of a NestJS service with Prisma is slow and a demo should not stall. Secrets are set by a script from a private file the subscription owner keeps, not by Bicep and not by the deploy workflows. GitHub Free cannot scope secrets to environments on private repos, and a Bicep re-apply would otherwise overwrite them with empty values. The production gate is a manual "Run workflow" on a separate `release` branch. GitHub Free has no environments for private repos, so Azure's login pass can only be limited per branch. Giving production its own branch means a push to `development` can never get production rights. Anyone with write access can still move `release`, and the spec says plainly that a second person is not enforced.

An independent review by another model found 13 places where the first draft named no source for a value, plus soundness gaps (uploads lost on restart, database connection limits, localhost origins in production, cold start smoke tests). All were fixed in the spec. One of its points was a gateway fix: inside Container Apps, internal ingress routes by Host header, so the nginx template must set Host to the upstream and cannot reuse the local config as is.

The engineer asked if seeding both environments is acceptable. Seed data is fake demo data, so it is fine at first deploy. The guard exists for later, when real tickets exist and a wrong command would delete them.

## References

**Project sources** (verifiable, in this repo):
- `docker-compose.shared.yml`, `docker-compose.vrms.yml`, `docker-compose.analytics.yml`, `welinc-auth/nginx.conf`: the services, ports and gateway routes that exist today.
- `Dockerfile.prod` in auth, backend-vrms, web-vrms and web-portal: the images this spec reuses and the gaps it fixes.
- `docs/scope/vrms/platform.md`, feature 26: the done criteria and the earlier Vercel and Render note.
- `AGENTS.md` (workspace root): `development` as the merge target, Node 24, no attribution lines on commits.

**Practices & standards**:
- Build once, deploy the same image to many environments (backends), rebuild per environment only where configuration is baked in (the SPAs).
- Additive database migrations so a rollback stays safe.
- Least privilege for CI: default read only token, scoped Azure roles.
- OpenID Connect federated credentials for GitHub Actions to Azure login, so no client secret is stored (Microsoft's recommended method; cited by name, link not verified).

**Links** (web verified):
- Azure for Students ($100, 12 months, no card, one account per person): https://azure.microsoft.com/en-us/free/students
- Azure free account ($200 credit, 30 days, card required): https://azure.microsoft.com/en-us/free
- Azure Static Web Apps quotas (Free plan: 100 GB bandwidth, 10 apps per subscription): https://learn.microsoft.com/en-us/azure/static-web-apps/quotas
- Azure Container Apps billing (monthly free grant, scale to zero charges nothing): https://learn.microsoft.com/en-us/azure/container-apps/billing
- Container Apps with GitHub Actions and a registry (registry auth needed even for GitHub's registry): https://learn.microsoft.com/en-us/azure/container-apps/github-actions
- PostgreSQL Flexible Server backup and restore (7 to 35 days, backups on by default): https://learn.microsoft.com/en-us/azure/postgresql/backup-restore/concepts-backup-restore
- Azure Container Registry tiers (Basic includes 10 GiB): https://learn.microsoft.com/en-us/azure/container-registry/container-registry-skus
- GitHub Actions billing (Free plan: 2,000 minutes a month): https://docs.github.com/en/billing/concepts/product-billing/github-actions
- GitHub environments (Free plan: environments only for public repos, so no required reviewers on private ones): https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments

Prices for the smallest PostgreSQL tier and Container Registry Basic were not confirmed (the pricing pages did not load); treat any cost figure as an estimate.
