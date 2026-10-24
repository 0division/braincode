# BrainCode: Time, History, and Replay

## Time model

BrainCode describes discrete time. A run has a committed tick index `T`, starting at `0`. Each successful transition reads the committed frame at `T`, computes the next frame at `T+1`, and then advances the committed tick.

Proposed notation:

| Expression | Meaning |
| --- | --- |
| `~T` | Current committed/source tick |
| `signal~1` | Value of `signal` at the source tick `T` while computing `T+1` |
| `signal~N` | Value of `signal` at tick `T+1-N`, where `N > 0` |

Access to unavailable history requires a defined initialization or error policy. A runtime must not silently replace it with `0`.

The proposed BrainCode source spelling for a delayed read is `:signal~N`. Thus, while computing `T+1`, `:signal~1` reads `signal[T]`. The exact tokenization of the colon-prefixed signal name and delay operator must be defined by the custom BrainCode grammar.

## Time-Value Board (TVB)

The TVB is the conceptual model for storing frames over time:

| Tick | `counter` | `fib` | Input `sensor` |
| ---: | ---: | ---: | ---: |
| 0 | 0 | 0 | 12 |
| 1 | 1 | 1 | 13 |
| 2 | 2 | 1 | 11 |
| 3 | 3 | 2 | 14 |

A TVB row is a complete, committed state for one tick. A simple in-memory table is sufficient for the first prototype. Persistent storage, compression, or selective tracing can be considered later.

## History is more than a storage diagram

To evaluate `signal~N` efficiently, the runtime must know which tick each signal value belongs to. Storing the entire frame history is easy to understand and debug, but can consume substantial memory during long runs.

Possible long-term strategies:

- complete frames for debugging and short runs;
- a bounded ring buffer for models with a known maximum delay;
- checkpoints plus deterministic recomputation for long runs;
- selective tracing of only chosen signals.

These strategies should preserve the same observable semantics.

## What “time travel” might mean

The term should be divided into separate capabilities:

1. **Query history:** An expression reads an explicit past value. This is the core `:signal~N` feature.
2. **Inspect a past frame:** A tool displays the state at an earlier tick. Stored history is sufficient.
3. **Replay through a tick:** The runtime deterministically recomputes frames from the initial state and recorded inputs.
4. **Branch from a past tick:** A user changes inputs or the program and starts a new timeline from a checkpoint.
5. **Overwrite the past:** This stronger behavior affects later states and actions and is not automatically part of v0.2.

v0.2 should target capabilities 1 and 2. Replay (capability 3) is a realistic follow-up if inputs are fully recorded and signal calculations are deterministic. Branching and changing the past remain open questions.

## Inputs and reproducibility

External sensor values, user actions, random values, and host I/O must be recorded with tick association if a run is to be replayable. A rule that reads the current wall-clock time or a live sensor directly cannot be made reproducible by the TVB alone.

Recommendations:

- record inputs as events containing tick, name, and value;
- record a random seed or treat random values as an explicit input sequence;
- separate program output and other side effects from state computation;
- during replay, use recorded inputs rather than uncontrolled live sources.

## Replay and side effects

Computed states can be reconstructed; external side effects such as sending email or overwriting files cannot reliably be “rewound.” Therefore, replay should suppress actions by default or redirect them to a dry-run mode.

A future action mechanism needs at least:

- unique event IDs or idempotency rules;
- a clear commit boundary;
- a distinction between simulation and action execution;
- diagnostics when a replay would trigger actions.

## Limits of the TVB promise

The TVB is a model for traceable state, not automatically a database system, universal debugger, or complete undo system. Memory use, external inputs, non-deterministic host functions, and irreversible actions each require explicit handling.
