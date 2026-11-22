---
name: envclean
description: Audit and clean macOS storage, uninstalled app remnants, ordinary caches, developer dependencies, and local AI tool data. Use for System Data, disk space targets, broken login items, old Homebrew or npm files, AI caches, or diagnosing sustained CPU, memory, disk, and background activity on a Mac.
metadata:
  display-name: EnvClean
---

# EnvClean

Use macOS interfaces, the shell, or the application's own tools available in the host agent. The workflow is portable across agents. The included Python 3 helpers use only the standard library and do not require any agent integration.

## Match the request to the action

- **Inspect, diagnose, or estimate** means read-only. Report the best evidence, candidates, uncertainty, and expected impact. Save a local baseline when useful to compare growth, without collecting file contents.
- **Clean a named category or the preceding list** authorizes reversible, verified changes in that scope. Resolve routine choices, recheck stale findings, and process eligible items without asking about each one. Keep uncertain and still-used items with a concrete reason.
- **Switch a version and clean up** means test the replacement first, migrate callers, let active work finish, reload only affected services, verify, then clear the old copy when no caller remains. Preserve rollback material.
- **Free a target amount** means measure the named volume, rank candidates by actual benefit, reversibility, and rebuild cost, and stop when the measured goal is reached. A same-volume move to Trash preserves recovery and usually provides no immediate free-space gain. Get specific direction if reaching the target requires permanent deletion, offloading valuable data, clearing Trash, or removing a backup.
- Treat upgrades, permanent deletion, broad OS resets, stopping active work, and modifying remote or synced data as separate actions. Use OS-native authentication if needed. Keep credentials and content out of logs, command output, reports, and shared notes.

## Inspect the relevant surfaces

| Request | Read |
| --- | --- |
| macOS storage, ordinary caches, snapshots, backups, iCloud, lag or resource pressure | [System resources](references/system-resources.md) |
| Uninstalled app, leftover Login Items entry, helper or extension | [App remnants](references/app-remnants.md) |
| Homebrew, npm, pnpm, uv, Xcode, Docker / OrbStack, shared runtimes | [Developer resources](references/developer-resources.md) |
| Codex, TRAE, WorkBuddy, Grok, VS Code Copilot, Hermes, or a newly installed AI tool | [AI tools](references/ai-tools.md) |
| Reversible move, recovery, comparison with an earlier inventory | [Local helpers](references/local-helpers.md) |

Start from the user's symptom. Establish the affected volume, account, applications, projects, or services and inspect only the relevant areas. Confirm identity using an app bundle identifier, package metadata, a registered job or a known owner. Check active processes and open files as well as persistent references such as lockfiles, MCP configuration, launch jobs, and runtime registrations. A name, an old timestamp, a large directory, or a momentary lack of open files does not establish that an item is unused.

For each candidate record the owner, exact local path or native object identifier, approximate allocated size, evidence for removal or retention, rebuild cost, and recovery method. Separate unavailable or permission-limited results from verified absence. Prefer native management for application-owned state, cloud downloads, backup objects, and managed worktrees. Use targeted reversible moves for eligible filesystem items.

## Verify and close

Recheck original and recovery paths. Verify whatever the action affected, such as the relevant Settings list, CLI version, dependency tree, or read-only service call. For space requests, compare free bytes on the same volume and report candidate size, bytes moved, and measured change separately. Report retained items and what blocks their cleanup. Do not present estimates as measured gains.

If the user has a shared work log, record only relevant outcomes, verification and unresolved blockers. Store detailed paths and recovery manifests locally. Apply the user's own rules for shared-memory writes and network access.
