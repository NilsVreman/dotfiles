# Repository notes

- Before changing maintained Python code, tests, or tooling in this tree, read `sway/docs/coding-standards.md` (repository-relative path).
- Read `sway/docs/architecture.md` for recovery and session ordering, and `sway/DEVELOPING.md` for the development workflow.
- Keep the standalone recovery pair and deployed configuration self-contained.
  Preserve `sway/config`, `sway/rofi/`, and `sway/scripts/` as untracked references.
  Leave `sway/.private/` untouched unless separately authorized.

## Documentation

- Write one sentence per line in Markdown.
- Each fact has one home:
  - `README.md`: what users see — commands, flags, environment variables, output, refusals, exit codes, and the Python API.
  - `docs/architecture.md`: how it works inside.
  - `GLOSSARY.md`: terms only.
  - `docs/adr/`: why a choice was made.
    Fix only outdated facts in an ADR; to change its reasoning, write a new ADR that supersedes it.
- The README reads as a guide: each section starts with prose, followed by a short example and notes.
  Never add a bare code block or a list of flags without explanation.
- A change to a command or the public API updates `README.md` and `docs/architecture.md` in the same change.

## Agent skills

### Issue tracker

Track issues in GitHub Issues for `NilsVreman/dotfiles`.
Read root `docs/agents/issue-tracker.md` before reading or publishing tickets.

### Triage labels

Use the canonical GitHub labels described in root `docs/agents/triage-labels.md`.

### Domain docs

Single-context: root `GLOSSARY.md` and `docs/adr/`, created lazily.
See root `docs/agents/domain.md`.
