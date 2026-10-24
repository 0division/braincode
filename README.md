# BrainCode

> A temporal DSL for synchronous state models, historical queries, and inspectable execution.

BrainCode is a custom language for describing state transitions over discrete ticks. A Python host supplies initial state, parameters, and tick inputs; BrainCode rules calculate the next frame from committed history. Its population and tensor forms express data-parallel work, while the current reference backend executes serially and deterministically.

## Project status

**A first v0.2 compiler and Python reference runtime are implemented.** The compiler parses the current `.bc` examples and can emit both readable, expanded BrainCode (`.bcc`) and structured JSON IR (`.bcc.json`). Both artifacts can be loaded by the runtime. The runtime supports scalar history, conditional hold, populations/tensors, indexed updates, reductions, neighborhood reads, and explicitly registered host functions. All current examples are compiled and exercised at small dimensions by the test suite.

This is an initial reference implementation, not a hardware-parallel compiler. It does not yet provide CUDA/GPU execution, a complete static type checker, explicit input/parameter declarations in `.bc`, side-effecting actions, or bounded-history storage. The workload examples are not intended to run at their illustrative stress-test sizes on this serial backend.

The original idea is in [`BrainCode v0.1.md`](./BrainCode%20v0.1.md). The documents in [`docs/`](./docs/) describe the design, execution model, history, AI direction, and implementation.

The v0.2 label identifies an evolving draft implementation; the `.bcc` grammar and `.bcc.json` IR format may still change before a stable release.

The earlier consolidated [BrainCode v0.2.md](./BrainCode%20v0.2.md) remains as a draft. The modular documentation under `docs/` is the primary concept documentation to continue developing.

## Documentation

- [Project handoff](./docs/PROJECT-HANDOFF.md) — concise context and verification state for resuming work in a fresh chat
- [Vision and scope](./docs/01-vision.md) — purpose, target applications, boundaries, and design goals
- [Execution model](./docs/02-execution-model.md) — tick semantics, updates, conditions, and determinism
- [Time, history, and replay](./docs/03-time-history-replay.md) — TVB, storage, inputs, and what “time travel” means
- [AI and discrete models](./docs/04-ai-and-discrete-models.md) — AI-assisted programming as a hypothesis and possible discrete models
- [Further concept improvements](./docs/05-concept-improvements.md) — additional design gaps, recommendations, and priorities
- [Language and compilation model](./docs/06-language-and-compilation.md) — custom BrainCode syntax, Python host functions, `.bcc` IR, and future backends
- [Example configuration](./docs/braincode.yaml.example) — illustrative afferent, BrainCode, and efferent language settings
- [Implementation status and roadmap](./docs/implementation-plan.md) — supported subset, limitations, and next milestones
- [Long-term product roadmap](./docs/long-term-improvement-plan.md) — GPU execution, visual authoring, debugging, visualization, and productization

The `.bc` examples are collected in [`docs/examples/`](./docs/examples/README.md), including 2D/3D cellular automata, a full Unicode-code-point-to-UTF-8 mapper, and compute-heavy workload sketches. BrainCode has its own syntax; its expression evaluator supports a restricted Python-like expression form and registered pure functions.

## Quick start

Python 3.11 or later is required. From the project directory:

```powershell
python -m pip install -e ".[test]"
python -m braincode compile docs/examples/counter.bc
python -m braincode run docs/examples/counter.bc --input-file docs/examples/counter.bc.in.json
python -m braincode run docs/examples/unicode-to-utf8-mapper.bc --input-file docs/examples/unicode-to-utf8-mapper.bc.in.json
python -m pytest -v
```

`compile` writes `counter.bcc` and `counter.bcc.json` by default. The `.bcc` file is BrainCode source with data-parallel loops unfolded into indexed rules; the `.bcc.json` file is the structured IR representation. The `run` command prints the full state history as JSON. The library API is also available:

To execute every checked-in example and save each compiled artifact, trace, and per-run Markdown report under `docs/examples/output/`, run the Bash script (Git Bash, WSL, or another Bash environment):

```bash
bash run_examples.sh
```

Each `.bc` example has a companion `.bc.in.json` file containing host-provided initial state, parameters, optional prior history, and the number of ticks to run. This keeps runtime data separate from model logic. The output folder contains an expanded `.bcc`, structured `.bcc.json`, `.output.json` execution trace, and `.run.md` report for every example, plus `summary.json`, a chronological `run.log`, and a readable `run-summary.md`. Each `.run.md` records the resolved input data, BrainCode source, and full output trace. Examples use small inputs suitable for the serial Python reference runtime.

For a single CLI run, `--markdown-output PATH` writes the same detailed report. A run configuration may instead set `"md_output": true` to write it to `output/<source-name>.run.md` beside the source directory, or set `"md_output"` to an explicit output path.

The test suite combines pytest parameterized checks with standard-library
`unittest` cases. It covers compiler/runtime round trips, UTF-8 boundary values,
1D/2D/3D automata, run configuration handling, shape and index validation, and
atomic tick failures.

```python
from braincode import compile_file, run

program = compile_file("docs/examples/counter.bc")
trace = run(program, initial_state={"counter": 0}, ticks=5)
```

See the [implementation status and roadmap](./docs/implementation-plan.md) for the current supported subset and remaining work.
