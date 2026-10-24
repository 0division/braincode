---
name: braincode-development
description: "Use when working on the BrainCode DSL, compiler, serial runtime, examples, tests, product roadmap, GPU backend, GUI, debugger, or when resuming BrainCode work in a fresh chat."
---

# BrainCode Development

Use this project workflow when changing BrainCode or resuming work from a
handoff.

## Before changing code

1. Read [`../../../docs/PROJECT-HANDOFF.md`](../../../docs/PROJECT-HANDOFF.md)
   for verified project and worktree context.
2. Inspect `git status`, relevant source/tests, and the documentation that
   describes the behavior. Do not overwrite or discard existing work.
3. Treat behavior as a hypothesis until a test or runtime check verifies it.
4. BrainCode `.bc` is its own DSL. Do not rewrite model source as Python.

## Implementing

1. Prefer the smallest complete improvement supported by the current code.
   Do not claim GPU, GUI, debugger, or product features are implemented unless
   they actually exist and have been exercised.
2. Add a regression test for each behavior change. Use pytest for new
   parameterized test coverage; retain standard-library unittest compatibility
   where the existing suite expects it.
3. Keep execution deterministic and synchronous: rules read committed history,
   writes commit atomically, and validation failures must not publish partial
   frames.
4. Update directly related documentation and examples.
5. Keep generated example artifacts under `output/`; the folder is ignored by
   Git and should not be staged by default.

## Verification

Run the narrow relevant test first, then the full checks when practical:

```powershell
python -m pip install -e ".[test]"
python -m pytest -q
python -m unittest discover -s tests -v
python -m braincode.example_runner --output output
```

After example execution, verify all 15 configured examples have traces and
that `output/run.log` and `output/run-summary.md` were written. Run
`git diff --check` and inspect `git status` before finishing.

## Handoff and Git

- Update [`../../../docs/PROJECT-HANDOFF.md`](../../../docs/PROJECT-HANDOFF.md)
  when tests, implementation status, or next steps materially change.
- Current branch is `v0.2`; do not push without explicit user approval.
- Do not commit unless requested. If creating a commit, include:
  `Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>`.
