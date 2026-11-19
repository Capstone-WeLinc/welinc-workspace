# BMS folder layout

Keep each repository directly inside `welinc-workspace`, alongside shared
services. The former `CAPSTONE-bms-webhook` folder contained multiple BMS apps;
its applications now occupy the three canonical BMS folders below. The user
has deleted `bms-legacy`; no legacy checkout is used by the running stack.

```text
CAPSTONE-bms/
└── welinc-workspace/
    ├── docs/context/bms/
    ├── docs/specs/bms/
    ├── infra/                         # shared gateway configuration
    ├── scripts/                       # shared setup and acceptance checks
    ├── docker-compose.shared.yml
    ├── docker-compose.bms.yml          # BMS-owned stack
    ├── welinc-auth/                    # shared auth; reference/runtime dependency
    ├── welinc-web-portal/              # shared SSO portal
    ├── welinc-backend-vrms/            # read-only integration reference
    ├── welinc-web-vrms/                # read-only integration reference
    ├── welinc-backend-vmms/            # VMMS-owned fleet provider
    ├── welinc-backend-bms/
    │   ├── bms-gateway/
    │   ├── bms-booking-service/
    │   ├── bms-dispatch-service/
    │   ├── bms-completion-service/
    │   ├── bms-analytics-projection/
    │   └── scripts/                   # BMS-only local preparation and smoke check
    ├── welinc-backend-bms-analytics-ai/
    └── welinc-web-bms/
```

The BMS code folders are local source copies without repository metadata, as
previously requested. They have not been initialized as new repositories.
The lead must arrange repository delivery and review before the coordinated
hard switch; the source copies alone are not completed pull requests.

BMS code changes belong only in its three source folders. BMS workspace work
belongs in `docker-compose.bms.yml` and BMS-owned documentation folders. Shared
auth, portal, gateway configuration and other groups' source stay owned by their
respective maintainers. Local setup may create ignored environment, key and
dependency files using the supplied setup tools.

Use the [BMS setup guide](setup.md) and [integration checklist](integration-checklist.md).
The old root launchers and old auth bridge are no longer startup dependencies.
