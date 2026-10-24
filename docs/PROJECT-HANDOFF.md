# BrainCode Project Handoff

Read this first when continuing BrainCode in a fresh chat. Load the
project-specific workflow in
[`../.github/skills/braincode-development/SKILL.md`](../.github/skills/braincode-development/SKILL.md)
when implementing or testing changes.

## Project and user context

- BrainCode is a custom temporal DSL for synchronous state models. Python is
  the compiler host and serial reference runtime, not the model source syntax.
- The user wants to turn the v0.2 prototype into a real product over time:
  GPU execution, GUI/IDE authoring, an interactive debugger, visualization,
  reproducible projects/runs, and eventually packaging and extensibility.
- Communicate and write project documentation in English.
- The user's request is to make useful improvements and test them, not to stop
  at plans. Be explicit about features that remain future work.

## Current repository state

- Remote: `https://github.com/0division/braincode`
- Branch: `v0.2`, based on `origin/main`
- Latest commit: `b927e5f` — `Complete BrainCode v0.2 TODOs`
- The latest feature work is **not committed**. Inspect `git status` before
  editing or staging; preserve unrelated changes.
- Git author identity is configured locally as `Daniel Mueller
  <mulacke@gmail.com>`.
- Do not push unless the user explicitly requests it.

Latest uncommitted changes cover:

- runtime validation in `braincode/runtime.py`;
- CLI run-config validation in `braincode/cli.py`;
- runtime and CLI tests in `tests/test_runtime_validation.py` and
  `tests/test_compiler.py`;
- pytest test extra in `pyproject.toml`;
- execution/runtime documentation and README updates;
- the corrected product-focused roadmap in
  `docs/long-term-improvement-plan.md`;
- ignores for generated pytest/package metadata.

## Verified current behavior

- All 15 checked-in examples run with small inputs. Their traces, expanded
  `.bcc`, `.bcc.json` IR, `summary.json`, `run.log`, and `run-summary.md` are
  generated under the ignored `output/` directory.
- `python -m pytest -q` passed: **37 tests, 75 subtests**.
- `python -m unittest discover -s tests -v` passed: **14 tests**.
- Pylance workspace diagnostics were empty.
- All example input files are kept beside their model sources as
  `*.bc.in.json`; the CLI accepts them with `--input-file`.
- The current runtime is serial and retains full frame history. There is no
  GPU backend, GUI, or interactive debugger yet.

## Useful commands

```powershell
python -m pip install -e ".[test]"
python -m pytest -q
python -m unittest discover -s tests -v
python -m braincode.example_runner --output output
```

Run every example before making wider changes and regenerate outputs again
after behavior changes. Confirm the final `output/summary.json` lists 15
examples and check the generated log and Markdown report.

## Suggested next engineering steps

1. Review existing changes and run tests before modifying the runtime.
2. Add input/state declarations and stronger static validation, with tests.
3. Improve error diagnostics with source locations and precise failure causes.
4. Define replay/run manifests and bounded history/checkpoint semantics.
5. Add a backend interface and benchmark before attempting CPU/GPU acceleration.
6. Prototype source-linked debugging/inspection for the serial runtime before
   choosing a GUI framework.
7. Update this handoff when verified test counts, branch/commit state, or
   implemented product features change.

For the product vision and sequencing, see
[`long-term-improvement-plan.md`](./long-term-improvement-plan.md). For
language/runtime facts, see
[`02-execution-model.md`](./02-execution-model.md) and
[`implementation-plan.md`](./implementation-plan.md).
