# BrainCode Stage 1 Contract

Stage 1 is the Python language and reference-runtime foundation. It does not
implement a GUI, debugger UI, GPU, or parallel hardware backend. The serial
runtime and this conformance contract are the reference for later backends.

## Language and values

BrainCode transitions read only committed history. While computing tick `T+1`,
`:signal~1` reads tick `T`; delay `N` reads tick `T+1-N`. A transition builds a
candidate frame and publishes it atomically after all rules and validation
succeed. Untouched values hold their previous value. Missing historical values
and undefined state signals are runtime errors. Same-tick dependencies and
implicit rule ordering are not supported.

`state :name of Type` declares a state value that must be present in the host's
initial state. `input :name of Type` declares a host-owned, read-only value
that can be supplied in the initial frame or in tick-indexed input frames.
Inputs not replaced on a tick retain the last committed value. Legacy programs
may continue to use implicit scalar state; declaring values enables type and
read-only validation without requiring an immediate migration of existing
examples.

Supported declared types are `Bool`, `Int32`, `Int64`, `Float32`, and
`Float64`. Integer types reject booleans and values outside their signed range;
they do not wrap. Boolean values must be actual booleans. Floating values must
be finite. `Float32` input values and assigned values are rounded to IEEE-754
binary32 when stored; `Float64` uses Python's IEEE-754 binary64 representation.
Expressions are evaluated by the reference backend using Python integer and
binary64 arithmetic, with the declared type enforced at storage boundaries.
Thus a Float32 expression is rounded on assignment, not after each operation.
Undeclared legacy values retain the existing JSON/Python-compatible behavior.
Division is true division, `//` is floor division, and reductions consume their
iterable in its given order using a left fold for `sum`.

The expression parser accepts only the documented structured subset. It does
not execute arbitrary Python source. Registered host functions are trusted
capabilities; functions used in a state expression must be deterministic and
side-effect-free.

## Host adapters and effects

An input adapter is registered for a named input:

```python
runtime.register_input_adapter("temperature", normalize_temperature)
```

Before a supplied input frame is committed (including the run's initial input
frame), registered adapters are called in registration order for matching
input keys. The adapter receives a copy of the value and returns its
replacement. An adapter exception aborts before state is changed.

An output adapter receives `(committed_tick, copied_frame)` after a successful
commit:

```python
runtime.register_output_adapter("logger", record_frame)
```

Adapters are called in registration order. An output adapter failure raises
`BrainCodeAdapterError` and explicitly reports that the tick is already
committed; external effects cannot be rolled back. No model-level action or
trigger syntax is implemented in Stage 1.

## History and limits

Full frame history remains the default. Optional `history_window=N` retains
only the newest `N` frames and requires `N` to be at least the largest delay
used by the program. In window mode, `run()` returns the retained window, not a
full trace. The absolute `tick` counter remains monotonic.

Optional runtime budgets are unlimited unless set:

- `max_ticks`: maximum number of transitions for the lifetime of the runtime;
- `max_population_elements`: maximum total element count across declared
  populations and tensors;
- `max_frame_bytes`: maximum compact-JSON UTF-8 size of any retained or
  candidate frame.

Configured limits fail explicitly before an oversized transition is
committed. These are deterministic safeguards, not a general Python-process
memory quota.

## Reproducibility and backend contract

Run manifests use `format: "braincode-run"` and a versioned schema. They record
the source and SHA-256, language/runtime/IR versions, backend, initial frame/history,
parameters, tick inputs, runtime limits, host adapter/function names, and
recorded output frames. `replay_run_manifest()` validates the manifest and
source hash, requires named host capabilities to be supplied again, replays
without output adapters, and checks the result against the recorded trace.
Host callback implementations are not serialized; their code/version must be
managed by the caller.

`ExecutionBackend` and `RuntimeSession` define the Python extension boundary.
`PythonSerialBackend` is the only implementation. It reports serial population
evaluation; the `parallel` keyword does not promise parallel hardware.

Rules read the same committed frame, and indexed population iterations follow
the stable coordinate order produced by the serial reference. Duplicate
resolved writes fail instead of depending on traversal order. Reductions retain
source iteration order; a future backend must preserve this order or document
and test a deliberate numerical relaxation.

## Conformance, performance, and AI evaluation

The checked-in input fixtures, traces, run manifests, and boundary tests form
the runnable conformance corpus. `python -m pytest -q` exercises the language
and replayed example traces. Regenerate committed artifacts with
`python -m braincode.example_runner`.

Run `python -m braincode.benchmark --sizes 32 64 --ticks 3 --repeats 2 --output docs/benchmarks/serial-baseline.json`
to reproduce the checked-in 1D state-update and 2D stencil serial elapsed-time
and traced-memory measurements alongside deterministic final-frame hashes.
The defaults are smaller for a quick smoke run. Measurements are
machine-specific evidence, not performance guarantees or GPU comparisons.

AI authoring remains an unverified hypothesis. A fair evaluation should
pre-register the same bounded modeling tasks for BrainCode and a host-language
baseline; freeze prompt/context and time budgets; score executable conformance
against hidden and boundary tests; record first-pass correctness, repair time,
number of edits, and human review effort; and publish failed attempts as well
as successes. This protocol defines a future evaluation and does not claim an
AI advantage or report results that have not been measured.
