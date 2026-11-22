# Local AI tools

Discover the actual installation, including GUI app, editor extension, CLI, local container, or profile configuration. For new tools, start with bundle or package identity and the native storage or diagnostics interface. Establish directory ownership before using names found through search. Inspect metadata and references without reading conversations, exporting logs, or revealing configuration secrets.

Classify each item before cleanup:

- **Regenerable:** scoped renderer caches, obsolete installers, expired crash reports or rolled logs. Check active ownership and rebuild cost.
- **Shared runtime:** MCP packages, browser runtimes, interpreter environments, local model weights and indexes. Enumerate consumers across apps and profiles. Make any migration explicit, wait for active work, and prove the replacement through a read-only call before removing the old copy.
- **Persistent:** sessions, prompts, memory, workspace state, editor extensions, account/SSO state, patches, checkpoints, local repositories, worktrees, settings, backups and deliverables. List by size when useful. Require specific authorization before altering them, and prefer native controls. Logs may contain prompts, tool inputs, or credentials.

| Tool | What to verify |
| --- | --- |
| Codex | Distinguish app caches, skill/plugin caches, session data, artifacts, and Codex-managed worktrees. Check uncommitted edits, untracked files and unpushed commits before worktree archival. Use the owning tool for a managed worktree. |
| VS Code / Copilot | Check editor profile, extension installation, remote environments, local chat history and any synchronized history. `workspaceStorage`, `globalStorage` and extension data can hold persistent state. Use editor controls for extension or session management. |
| TRAE | Identify the installed edition and its data path. Treat `ModularData` and similar agent-state directories as persistent. TRAE documents that reset may remove chats, pending edits and rollback snapshots. |
| WorkBuddy | Identify the product and version from the installed app. Use its diagnostic interface to locate logs, and treat logs as potentially sensitive. Preserve projects and connected settings. |
| Grok / Grok Bot | Verify the particular local app, browser wrapper, extension, or CLI. Similar names alone do not establish common ownership. Keep browser profiles and chat data scoped to the application that owns them. |
| Hermes | Check user and bot profiles, gateway duties and active sessions, cron jobs, MCP commands, and shared runtime dependencies. Prefer supported, scoped reload or an idle graceful restart. Keep remote services, memory stores and sync queues outside a local cleanup request. |

Example acceptance case: two MCP client versions are cached locally while the NAS server runs its own version. Check server and client versions independently. Pin the intended local client only within the authorized configurations. Test the newer client, let the current tasks finish, reload the owner, confirm old process references are gone, move the old cache, then repeat the read-only test.

Primary references: [Codex worktrees](https://developers.openai.com/codex/app/worktrees), [VS Code chat sessions](https://code.visualstudio.com/docs/copilot/chat/chat-sessions), [TRAE troubleshooting](https://docs.trae.cn/ide_troubleshoot-general-issues), [Hermes dashboard and profiles](https://hermes-agent.nousresearch.com/docs/user-guide/features/web-dashboard).
