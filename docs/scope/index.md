# Scope: WeLinc suite

The WeLinc fleet suite is three systems (VRMS, VMMS, BMS) on shared services (auth, portal, gateway). Each system keeps its own scope in its own folder here; work that belongs to the whole suite goes in `_root/`.

| Workspace | Scope | Status |
|---|---|---|
| VRMS (Vehicle Repair Management System) | [vrms/index.md](vrms/index.md) | 8 existing, 23 done, 8 in-progress, 31 planned, 5 dropped |
| VMMS | not added yet | |
| BMS | not added yet | |
| Suite wide (`_root`): shared services | [_root/shared-services.md](_root/shared-services.md) | 7 done, 2 in-progress, 4 planned |

The shared services rework (auth, portal, gateway, and moving VMMS and BMS onto them) lives in [_root/shared-services.md](_root/shared-services.md) since 2026-11-07. VRMS feature 56 keeps the domain contracts between systems, and hosting (feature 26) stays in [vrms/platform.md](vrms/platform.md).
