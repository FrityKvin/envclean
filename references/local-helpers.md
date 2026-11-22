# Local helpers

Both scripts require macOS and Python 3.9 or later. Run the commands from the EnvClean folder or use the absolute script paths. They use no external APIs, agent-specific features, or Python packages.

## Storage and growth

```sh
python3 scripts/inventory.py
python3 scripts/inventory.py --volume "$HOME" --path "$HOME/Library/Caches" > /path/to/local-baseline.json
python3 scripts/inventory.py --volume "$HOME" --path "$HOME/Library/Caches" --previous /path/to/local-baseline.json
```

The default inventory covers common cache, backup, developer, model and package roots. It reports allocated size, partial or unavailable measurements, and volume-available bytes. Specify exact local paths with repeated `--path` flags. Baselines compare completed observations of the same paths and compare available bytes only with a matching volume anchor and device. Several default paths overlap, so do not sum them. Avoid measuring cloud placeholders or synced trees recursively. Keep baseline JSON local, since it contains paths.

## Reversible moves

Create a small JSON file from items already reviewed and within the user's scope. An example using placeholder paths:

```json
[
  {"path": "Library/Caches/example.app/Cache", "kind": "cache"},
  {"path": ".local/bin/retired-example", "kind": "broken-link"},
  {"path": "Code/old-example/node_modules", "kind": "dependency-tree"}
]
```

Use canonical paths relative to the current user's home. Supported kinds are `cache`, `app-remnant`, `broken-link`, and `dependency-tree`. Files must be in one of the helper's supported user-owned locations. `app-remnant` is reserved for specifically identified uninstalled apps or their own orphaned launch plists. A dependency tree must have its adjacent manifest and lockfile, or contain only broken stubs or nothing. Workspace trees with a lockfile elsewhere require separate verification by the agent. Broad roots, synced folders, native system objects, mounted volumes, and targets outside the user's home should be handled through their owner and user scope. The helper will skip uncertain paths and reports partial results with a nonzero exit.

```sh
python3 scripts/reversible_cleanup.py plan /path/to/reviewed.json
python3 scripts/reversible_cleanup.py apply /path/to/reviewed.json
python3 scripts/reversible_cleanup.py restore '/path/printed/by/apply/recovery.jsonl' --item 'Library/Caches/example.app/Cache'
```

`plan` never creates recovery files or moves data. Use `apply` after authorization. The helper checks exact path types, ownership, same-volume operation, overlap, and visible open-file and process references. It cannot establish app ownership, sync safety or whether an idle process will need a path later. The agent performs those checks first. Run without `sudo`. Where OS protection blocks a move, use the native management interface or report the protected item.

Each batch lands in a separate folder under the user's `.Trash`. Keep its path and journal together. The journal is written before each move, so recovery can identify items even if the helper was interrupted. Restore the entire batch by omitting `--item`, or repeat `--item` for selected items. Restore refuses to overwrite a file or directory recreated at the original location and requires original parent directories to exist. Review conflicts individually. A Trash move remains reversible until the item is permanently removed, and does not guarantee an immediate gain in available space.
