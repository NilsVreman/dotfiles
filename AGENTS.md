# Repository notes

- For maintained Sway Python code and tests, read `sway/docs/coding-standards.md` before editing.
  Those standards apply only to `sway/`, not to other dotfiles.

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
Read `docs/agents/issue-tracker.md` before reading or publishing tickets.

### Triage labels

Use the five canonical triage labels.
Read `docs/agents/triage-labels.md` before triaging or changing issue labels.

### Domain docs

Single-context: root `GLOSSARY.md` and `docs/adr/`.
Read `docs/agents/domain.md` before exploring domain terminology or decisions.
