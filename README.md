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

- [Vision and scope](./docs/01-vision.md) — purpose, target applications, boundaries, and design goals
- [Execution model](./docs/02-execution-model.md) — tick semantics, updates, conditions, and determinism
- [Time, history, and replay](./docs/03-time-history-replay.md) — TVB, storage, inputs, and what “time travel” means
- [AI and discrete models](./docs/04-ai-and-discrete-models.md) — AI-assisted programming as a hypothesis and possible discrete models
- [Further concept improvements](./docs/05-concept-improvements.md) — additional design gaps, recommendations, and priorities
- [Language and compilation model](./docs/06-language-and-compilation.md) — custom BrainCode syntax, Python host functions, `.bcc` IR, and future backends
- [Example configuration](./docs/braincode.yaml.example) — illustrative afferent, BrainCode, and efferent language settings
- [Implementation status and roadmap](./docs/implementation-plan.md) — supported subset, limitations, and next milestones
- [Long-term improvement plan](./docs/long-term-improvement-plan.md) — phased path from the reference implementation to validated parallel backends

The `.bc` examples are collected in [`docs/examples/`](./docs/examples/README.md), including 2D/3D cellular automata, a full Unicode-code-point-to-UTF-8 mapper, and compute-heavy workload sketches. BrainCode has its own syntax; its expression evaluator supports a restricted Python-like expression form and registered pure functions.

## Quick start

Python 3.11 or later is required. From the project directory:

```powershell
python -m braincode compile docs/examples/counter.bc
python -m braincode run docs/examples/counter.bc --input-file docs/examples/counter.bc.in.json
python -m braincode run docs/examples/unicode-to-utf8-mapper.bc --input-file docs/examples/unicode-to-utf8-mapper.bc.in.json
python -m unittest discover -s tests -v
```

`compile` writes `counter.bcc` and `counter.bcc.json` by default. The `.bcc` file is BrainCode source with data-parallel loops unfolded into indexed rules; the `.bcc.json` file is the structured IR representation. The `run` command prints the full state history as JSON. The library API is also available:

To execute every checked-in example and save each compiled artifact and trace under `output/`, run the Bash script (Git Bash, WSL, or another Bash environment):

```bash
bash run_examples.sh
```

Each `.bc` example has a companion `.bc.in.json` file containing host-provided initial state, parameters, optional prior history, and the number of ticks to run. This keeps runtime data separate from model logic. The output folder contains an expanded `.bcc` and structured `.bcc.json` for every example, a `.output.json` execution trace for each, `summary.json`, a chronological `run.log`, and a readable `run-summary.md`. Examples use small inputs suitable for the serial Python reference runtime.

```python
from braincode import compile_file, run

program = compile_file("docs/examples/counter.bc")
trace = run(program, initial_state={"counter": 0}, ticks=5)
```

See the [implementation status and roadmap](./docs/implementation-plan.md) for the current supported subset and remaining work.
