# BrainCode Project Handoff

Read this first when continuing BrainCode work in a fresh chat. Load the
project-specific workflow in
[`../.github/skills/braincode-development/SKILL.md`](../.github/skills/braincode-development/SKILL.md)
when implementing or testing changes.

## Project and user context

- BrainCode is a custom temporal DSL for synchronous state models. Python is
  the compiler host and serial reference runtime, not the model source syntax.
- The user's product direction includes GPU execution, integrated IDE
  authoring, an interactive debugger, visualization, reproducible
  projects/runs, a hosted cloud API, and eventual packaging and extensibility.
  Start by validating authoring and run workflows in a VS Code extension
  rather than a standalone GUI.
- Communicate and write project documentation in English.
- Make useful improvements and test them. Clearly distinguish shipped
  capabilities from future work.

## Current repository state

- Remote: `https://github.com/0division/braincode`
- Branch: `v0.2`; Stage 1 changes are pushed to `origin/v0.2`.
- Stage 1 foundation is complete: language/value validation, host adapters,
  reproducible manifests and replay, optional history and resource limits,
  backend/session contracts, conformance coverage, serial benchmarks, docs,
  and committed example run artifacts.
- The five Stage 1 suggestion documents are renamed `done_stage1_...` and
  indexed as complete. Stages 2, 3, and 4 remain planned.
- A Stage 2a VS Code extension prototype is in `vscode-extension/`. It
  registers `.bc`, supplies basic syntax/snippets, and invokes the CLI for
  compile, inspect, run, and replay. The extension host has not yet been
  manually exercised or packaged for distribution.

## Verified current behavior

- All 16 checked-in examples run with small inputs. Their traces, expanded
  `.bcc`, `.bcc.json` IR, per-example `.run.md` reports, run manifests,
  `summary.json`, `run.log`, and `run-summary.md` are committed under
  `docs/examples/output/`.
- `python -m pytest -q` passed: **60 tests, 94 subtests**.
- `python -m unittest discover -s tests -v` passed: **22 tests**.
- Extension manifest/resource tests are in `tests/test_vscode_extension.py`;
  run them with `python -m pytest -q tests/test_vscode_extension.py`.
- The checked-in machine-specific serial reference measurements are in
  [`benchmarks/serial-baseline.json`](./benchmarks/serial-baseline.json).
  The benchmark command defaults to small workloads for a quick smoke run.
- Example inputs are kept beside their model sources as `*.bc.in.json`; the
  CLI accepts them with `--input-file`.
- Execution is serial, with optional bounded history. There is no GPU backend,
  standalone GUI, or interactive debugger yet. Stage 1 also does not provide
  full static inference, model-level triggers/actions, or a process-wide
  memory quota.

## Useful commands

```powershell
python -m pip install -e ".[test]"
python -m pytest -q
python -m unittest discover -s tests -v
python -m braincode.example_runner --output docs/examples/output
python -m braincode.benchmark
```

After changing runtime behavior, regenerate the committed example outputs and
confirm `docs/examples/output/summary.json` lists 16 examples and the expected
traces, reports, manifests, and compile artifacts.

To reproduce the committed benchmark measurements:

```powershell
python -m braincode.benchmark --sizes 32 64 --ticks 3 --repeats 2 --output docs/benchmarks/serial-baseline.json
```

## Suggested next engineering steps

1. Exercise the Stage 2a extension in an Extension Development Host, fix
   workflow issues, and validate packaging before distribution.
2. Add source-linked debugging and inspection when runtime execution details
   can support them reliably.
3. Continue static analysis and portability work, including clearer inference
   diagnostics and portable host-capability/version provenance.
4. Prototype useful GPU workloads only against the serial runtime's
   conformance corpus; measure and document any numerical relaxation.
5. Specify a hosted API and isolated-worker threat/resource model before
   implementing cloud execution; an initial CPU-backed preview need not await
   broad GPU coverage.
6. Evaluate AI-assisted modeling against a pre-registered host-language
   baseline and publish failures as well as successes.

For the product vision and sequencing, see
[`long-term-improvement-plan.md`](./long-term-improvement-plan.md). For
language/runtime facts, see [`stage1-contract.md`](./stage1-contract.md),
[`02-execution-model.md`](./02-execution-model.md), and
[`implementation-plan.md`](./implementation-plan.md).
