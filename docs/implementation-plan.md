# BrainCode: Implementation Status and Roadmap

## Current status

The workspace now contains a v0.2 compiler and a deterministic Python reference runtime. The compiler uses a BrainCode statement parser and a restricted, validated expression evaluator; it does not execute source through Python `eval`.

Implemented:

- `.bc` parsing for scalar assignments, temporal references, conditional updates, local `let` bindings, population/tensor declarations, boundaries, and `each ... parallel` blocks;
- arithmetic, comparisons, Boolean operators, conditional expressions, named function arguments, and single-clause generator expressions/reductions;
- expanded `.bcc` BrainCode source with population loops unfolded into indexed assignments;
- a versioned `.bcc.json` JSON IR with source locations and expression trees;
- deterministic tick execution with reads from committed history, atomic frame commits, and hold-by-copy behavior for untouched state;
- serial population/tensor execution, indexed reads/writes, boundary handling, neighbor counts, vector arithmetic, and reductions used by the examples;
- built-in pure functions and caller-provided named function registration;
- CLI operations for compile, inspect, expanded listing, and run;
- tests that compile every `.bc` example and execute each at small dimensions.

The Python backend is a correctness-oriented reference implementation. The `parallel` keyword defines the iteration domain and synchronous semantics; it does not launch parallel hardware work.

## Current limitations

- There is no CUDA, GPU, multiprocessing, or optimized CPU backend.
- Static type checking is incomplete; many state/input names and shapes are checked when a model runs.
- Scalar inputs and immutable parameters are supplied by the host rather than declared with dedicated `.bc` statements.
- Full frame history is retained in memory; long runs over large populations can consume substantial memory.
- Host-supplied functions are trusted capabilities. Callers must register only functions appropriate for their model and ensure state-rule functions are deterministic and side-effect-free.
- Actions, external side effects, checkpointing, replay packages, and bounded history are not implemented.
- Large workload values in example comments are complexity illustrations, not practical defaults for the serial backend.

## Core execution contract

- A model begins with a host-supplied current frame at tick `T`.
- While computing `T+1`, `:signal~1` reads the committed value at `T`, and `:signal~N` reads the frame `N-1` ticks earlier.
- Every rule in a transition reads the same committed history. Rules cannot see another rule's uncommitted result.
- The next frame starts as a copy of the current frame. Unassigned state therefore holds its prior value.
- A candidate frame is published only after all rules succeed. A failed tick leaves the committed history unchanged.
- Population rules are evaluated serially in the reference runtime, but all population elements read the same prior frame.

## Command-line use

```powershell
python -m braincode compile docs/examples/counter.bc
python -m braincode run docs/examples/unicode-to-utf8-mapper.bc --input-file docs/examples/unicode-to-utf8-mapper.bc.in.json
python -m braincode run docs/examples/counter.bc --input-file docs/examples/counter.bc.in.json
python -m braincode run docs/examples/counter.bc --initial-state "{\"counter\": 0}" --ticks 5
python -m unittest discover -s tests -v
```

`compile` writes sibling `.bcc` and `.bcc.json` files by default. `.bcc` remains BrainCode syntax, with every `each ... parallel` population rule unfolded into explicit indexed assignments. `.bcc.json` stores the machine-readable IR. Supply `--parameters` when symbolic population dimensions need values for expansion.

The Python API is available from `braincode.compile_file`, `braincode.Runtime`, and `braincode.run`. Host-provided arrays and scalars belong in `initial_state`; immutable dimensions and constants belong in `parameters`; future tick inputs can be passed through `input_frames`. Example run configurations are kept in sibling `.bc.in.json` files, outside BrainCode model logic.

The `run` command accepts `--input-file` with a JSON object containing
`initial_state`, `parameters`, optional `initial_history` and `inputs`, and
`ticks`. Explicit CLI options can override the corresponding configuration
values. See the [long-term improvement plan](./long-term-improvement-plan.md)
for the staged direction beyond v0.2.

## Next development milestones

1. **Strengthen validation:** complete type checking, declared input/parameter support, and more precise diagnostics for shape and history errors.
2. **Specify numeric and resource behavior:** define integer overflow, float policy, history budgets, and limits for reductions and population sizes.
3. **Improve run artifacts:** add serializable input logs, run metadata, and deterministic replay without repeating external effects.
4. **Optimize after conformance:** benchmark the reference interpreter, then add an optimized CPU or GPU backend while retaining the serial runtime as the semantic oracle.
5. **Evaluate AI authoring:** measure generated-program correctness and repair effort against fair host-language baselines.

The v0.2 compiler intentionally prioritizes clear semantics and runnable examples over a speed claim. Future changes should extend the documented and tested language subset without changing existing behavior silently.
