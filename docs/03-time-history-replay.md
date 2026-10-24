# BrainCode: Time, History, and Replay

## Time model

BrainCode describes discrete time. A run has a committed tick index `T`, starting at `0`. Each successful transition reads the committed frame at `T`, computes the next frame at `T+1`, and then advances the committed tick.

Implemented delayed-read notation:

| Expression | Meaning |
| --- | --- |
| `~T` | Current committed/source tick |
| `signal~1` | Value of `signal` at the source tick `T` while computing `T+1` |
| `signal~N` | Value of `signal` at tick `T+1-N`, where `N > 0` |

Access to unavailable history raises a runtime error. The runtime never
silently replaces it with `0`.

The BrainCode source spelling for a delayed read is `:signal~N`. Thus, while
computing `T+1`, `:signal~1` reads `signal[T]`. The custom BrainCode parser
recognizes the colon-prefixed signal and delay operator.

## Time-Value Board (TVB)

The TVB is the conceptual model for storing frames over time:

| Tick | `counter` | `fib` | Input `sensor` |
| ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 12 |
| 1 | 1 | 1 | 13 |
| 2 | 2 | 1 | 11 |
| 3 | 3 | 2 | 14 |

A TVB row is a complete, committed state for one tick. The Python runtime retains complete in-memory frame history by default.
Versioned run manifests persist source, configuration, tick inputs, and output
traces as JSON for reproducibility.

## History is more than a storage diagram

To evaluate `signal~N` efficiently, the runtime must know which tick each signal value belongs to. Storing the entire frame history is easy to understand and debug, but can consume substantial memory during long runs.

Available and possible strategies:

- complete frames for debugging and short runs (the default);
- an opt-in bounded retained-history window for models with a known maximum
  delay;
- checkpoints plus deterministic recomputation for long runs;
- selective tracing of only chosen signals.

Window mode requires a size at least as large as the model's largest temporal
delay. `Runtime.run()` returns the retained frames in window mode. General
checkpoints and selective tracing remain future work.

## What “time travel” might mean

The term should be divided into separate capabilities:

1. **Query history:** An expression reads an explicit past value. This is the core `:signal~N` feature.
2. **Inspect a past frame:** A host can inspect retained runtime history or a saved trace.
3. **Replay through a tick:** `replay_run_manifest()` deterministically recomputes frames from the recorded source/configuration/input sequence and verifies the saved trace.
4. **Branch from a past tick:** A user changes inputs or the program and starts a new timeline from a checkpoint.
5. **Overwrite the past:** This stronger behavior affects later states and actions and is not automatically part of v0.2.

Stage 1 implements capabilities 1 and 3 for the serial backend and supports
capability 2 through retained runtime history and saved traces. Branching and
changing the past remain open questions.

## Inputs and reproducibility

External sensor values must be supplied as tick-indexed inputs for a run to be
replayable. A rule cannot read wall-clock time or a live sensor directly.
Versioned manifests record the input sequence and source hash. Host callback
implementations are resupplied by the caller and must be deterministic.

Recommendations:

- record inputs in frame-indexed arrays containing name/value pairs;
- record a random seed or treat random values as an explicit input sequence;
- separate program output and other side effects from state computation;
- during replay, use recorded inputs rather than uncontrolled live sources.

## Replay and side effects

Computed states can be reconstructed; external side effects cannot reliably be
“rewound.” Replay does not execute output adapters. BrainCode model actions
are not implemented.

A future action mechanism needs at least:

- unique event IDs or idempotency rules;
- a clear commit boundary;
- a distinction between simulation and action execution;
- diagnostics when a replay would trigger actions.

## Limits of the TVB promise

The TVB is a model for traceable state, not automatically a database system, universal debugger, or complete undo system. Memory use, external inputs, non-deterministic host functions, and irreversible actions each require explicit handling.
