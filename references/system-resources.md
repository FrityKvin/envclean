# macOS storage and resource pressure

## Establish the volume and the symptom

- For a full disk, measure the volume that holds the target files with `df -k <path>`. Use `diskutil info <path>` and `diskutil apfs list` to identify the volume and container. The System Settings storage categories can help prioritize but can lag behind changes. Avoid adding overlapping directory totals or treating APFS shared space, clones, sparse files, and purgeable storage as guaranteed reclaimable bytes.
- Inventory broad categories first. Compare the same roots across dated lightweight baselines to find recurring growth. Use `du -sk` on selected paths without following symbolic links. Treat access errors and timeouts as partial results. Skip cloud content that would have to be downloaded to measure it.
- If free space does not improve, check the relevant Trash, other APFS volumes sharing the container, snapshots, and files that were unlinked but remain open (`lsof +L1`, filter the output locally). Verify permissions and volume identity. Closing an owning process can release open files and can also interrupt work, so identify the process first.

## Ordinary caches and large local copies

- Use exact cache subdirectories with a known owner. Candidates include regenerable app or browser rendering caches, downloaded installers, and old crash reports or rotated logs when no investigation depends on them. Check whether the owning app is active. Prefer its built-in cache controls when effective. Sample names, sizes and timestamps, not diagnostic log contents. Browser profiles, cookies, extensions, offline site data and sign-ins can be stored alongside caches and require separate treatment.
- Inspect Trash as an estimate and report it separately. Preserve existing contents and cleanup recovery sets. Emptying Trash or deleting particular entries requires explicit scope.
- Inspect Time Machine local snapshots with `tmutil listlocalsnapshots <mountpoint>` and APFS snapshots in Disk Utility. Local snapshots normally age out or are reclaimed as space is needed. Establish the owner and recovery implications before considering removal. Avoid treating all snapshots as Time Machine objects.
- For local iPhone or iPad backups, use Finder's Manage Backups to identify devices and dates and to archive or remove a specifically authorized backup. Do not infer ownership from hashed directory names.
- For synced iCloud Drive content, confirm completed sync and use Finder's **Remove Download** when the intent is to remove only the local copy. For other providers use their supported online-only operation. Keep offline work, unsynced copies, and libraries protected until their purpose is clear.
- Use the OS or owner application for managed system resources. Avoid blanket removal of system caches, swap, snapshots, databases, user libraries, or `/private/var` content.

## Lag, energy, and background activity

Use Activity Monitor or short terminal samples to compare CPU, memory pressure, swap, disk I/O and, if relevant, energy. Sample across the reported symptom and distinguish a brief spike from persistent pressure. Attribute helper processes to the owning app, service, or user task. High cached RAM with normal pressure is ordinarily a poor cleanup target. Avoid force-purging RAM or touching swap files. Stopping or restarting a service calls for a defined scope and an idle-state check. Re-sample after an authorized change.

Primary references: [Manage Mac storage](https://support.apple.com/en-us/102624), [Time Machine local snapshots](https://support.apple.com/en-us/102154), [Activity Monitor](https://support.apple.com/guide/activity-monitor/welcome/mac), [Manage iPhone and iPad backups](https://support.apple.com/en-us/108809), [iCloud Drive on Mac](https://support.apple.com/guide/mac-help/store-files-in-icloud-drive-mchle5a61431/mac).
