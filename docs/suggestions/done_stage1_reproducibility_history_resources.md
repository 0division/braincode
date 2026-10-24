# Completed Stage 1: Reproducibility, history, and resource limits

Stage 1 should establish the run and storage contracts in Python. Stage 2 can
then present them in a GUI, and Stage 3 can implement compatible device-side
storage or execution.

## Reproducible runs

- Record source, parameters, initial state/history, and tick inputs in a
  versioned run manifest.
- Make identical program/configuration/input sequences produce identical
  reference-runtime frames.
- Separate state evaluation from external effects so replay does not repeat
  side effects.
- Test artifact round trips and report exactly which information is needed to
  reproduce a run.

## History and resource behavior

Full frame history is useful for a reference runtime and debugging but can
consume unbounded memory. Define:

- retained-history and full-trace modes;
- how delays constrain the minimum history window;
- optional tick, memory, model-size, and evaluation budgets;
- explicit errors when configured limits are exceeded.

Stage 1 implements versioned source-hashed run manifests and deterministic
replay with output verification; caller-supplied host capabilities are
required again for replay. Full-history mode remains the default. An optional
delay-aware window and deterministic tick, declared-population-element, and
serialized-frame-size limits are available. A process-wide memory budget and
general checkpoint/resume remain future work. See
[`../stage1-contract.md`](../stage1-contract.md).
