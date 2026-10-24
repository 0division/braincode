# Stage 1 suggestion: Reproducibility, history, and resource limits

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

Implement these in the Python runtime only after their semantics and defaults
are documented. Keep the storage interface replaceable for later tools and
backends.
