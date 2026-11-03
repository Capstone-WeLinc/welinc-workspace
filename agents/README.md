# Per group AI setup

One folder per group: `vrms/`, and `vmms/` and `bms/` when those groups add theirs. Each holds that group's AI rules (`AGENTS.md`), skills (`skills/`), MCP servers (`mcp.json`), extra tool settings (`settings.json`) and any files its skills read (for example `skills-lock.json`, `test-preferences.json`). Every file is optional.

Nothing here loads on its own. Turn on your own group's setup with:

```bash
node scripts/use-agents.mjs <system>
```

It copies the folder into git ignored spots at the workspace root (`.claude/skills/`, `.mcp.json`, `.claude/settings.local.json`, and a `CLAUDE.local.md` that imports your `AGENTS.md`), so another group's AI never sees it. Run it again after a pull that changes your folder, then restart your AI tool.

Changed or added a skill locally? Run `node scripts/use-agents.mjs <system> --save`, then commit your folder.

If your AI tool reads its rules from somewhere else (for example `.cursor/rules/` or `GEMINI.md`), keep the source in your folder and point your tool at it locally. Don't put group rules in the root `AGENTS.md`: that file is shared by everyone.
