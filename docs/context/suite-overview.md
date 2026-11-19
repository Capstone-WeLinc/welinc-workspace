# Suite overview

The WeLinc fleet suite (Capstone 2) is three systems built by three groups for WeLinc Logistics, on a few shared services. This file is the suite level picture; each system's own background, roles, glossary and requirements live in its folder (VRMS: [vrms/](vrms/)).

## The systems

| System | What it does | Owner |
|---|---|---|
| VRMS | Vehicle Repair Management System: log, assign, track, verify and cost truck repairs | VRMS group |
| VMMS | Vehicle Maintenance Management System: planned, preventive maintenance | VMMS group |
| BMS | Booking Management System: bookings, trips and job orders | BMS group |

## Shared services

| Service | Repo | What it does | Port |
|---|---|---|---|
| Auth | `welinc-auth` | Login, OTP, password reset and users for every system; issues the JWT with a role per system | 3001 |
| Portal | `welinc-web-portal` | The one sign in page; sends each user to their system | 8000 |
| Gateway | Nginx, built from `infra/gateway/` in this workspace (spec 0008) | One front door that routes each path to its service | 3000 |

They run from `docker-compose.shared.yml`, which also creates the `welinc-network` Docker network every system joins.

## Where it runs

| Where | Addresses | Data |
|---|---|---|
| Your machine | `http://localhost:3000` (gateway), `:8000` (portal), each system's own port | The full seed |
| Staging (the only hosted environment) | `https://staging-api.welinc.app` (gateway), `staging-portal`, `staging-vrms`, `staging-vmms`, `staging-bms`.welinc.app | The full seed |

Everything runs on Azure (VRMS spec 0008; group guide [hosting.md](../integration/hosting.md)). A push to `development` deploys staging. Nobody touches `main`.

## How the systems fit together

- **Microservices between systems.** Each system has its own containers, its own database and its own deployment, and they talk to each other only over APIs (through the gateway).
- **A modular monolith inside each system.** One backend per system, split into modules by feature.
- **One login.** Every system trusts the same auth service and checks its own role in the token on its own server. No system reads another system's database.

## Where things are decided

- Each system's own product decisions live in its folder (`docs/scope/<system>/`, `docs/specs/<system>/`).
- Anything the systems share (auth roles, gateway routes, vehicle status, notifications, the mobile app) is agreed together and recorded in [docs/integration/](../integration/) and in suite specs under `docs/specs/_root/`.
