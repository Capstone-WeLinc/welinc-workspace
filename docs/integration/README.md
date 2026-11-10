# Integration

Reference material the three systems share. Setting up and running the stack is in the workspace [README](../../README.md); the gateway is in [infra/gateway/](../../infra/gateway/README.md).

Big decisions become suite specs in `docs/specs/_root/` (the shared contract is [0001](../specs/_root/0001-shared-services-contract/index.md)). This folder holds the working material around them.

| File | What it is |
|---|---|
| [seed-accounts.md](seed-accounts.md) | Every seed login: the office accounts, multi system and broken state accounts, and how to reseed (spec 0006) |
| [web-login.md](web-login.md) | How a system's web app joins the shared web login: the session routes, the boot sequence, Switch system, sign out (spec 0007) |
| [shared-repo-changes.md](shared-repo-changes.md) | What changed in welinc-auth and welinc-web-portal this term, and what is planned |
