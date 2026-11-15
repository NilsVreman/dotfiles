# Pre-refactor recovery fixtures

These records were captured by running the scripts from commit `fed405f0482f6b0857fee3e0232e41258f9cf320` against disposable homes and controlled external commands before implementing #73.
No private snapshots or real session records were read.

`deployment-v1.json` contains the deployed journal, snapshot graph, and harmless payload texts for a prior symlink and its referent.
`session-v1.json` contains the ownership record produced by a successful isolated session startup.
Temporary path prefixes became `@ROOT@`, the timestamp became `legacy-snapshot`, and the journal's filesystem device/inode became placeholders.
Tests substitute their sandbox paths and current configuration-directory identity and recompute the manifest digest after relocation.
All other field names, values, payload hashes, and unit texts remain the pre-refactor records.
