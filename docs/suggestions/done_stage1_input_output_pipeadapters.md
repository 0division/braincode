# Completed Stage 1: Input/output pipe adapters

Stage 1 should define and exercise the host boundary for stream processing.
This is Python work, not GUI or GPU implementation.

## Separate model computation from external interaction

Distinguish three categories:

1. **State signals** are calculated by the model and stored in committed
   frames.
2. **Inputs** are supplied by the host for a particular tick and recorded for
   replay.
3. **Actions** request external effects and may be dispatched only after a
   successful state commit.

Keep model expressions deterministic. Do not execute arbitrary host code from
conditions or expressions. Instead, allow the expression language to grow
through explicit syntax and carefully documented pure functions.

## Input adapters

Before a tick, host-side adapters can convert external streams into BrainCode
input frames. Candidate uses include:

- sensor normalization and calibration;
- packet decoding and unit conversion;
- filtering, resampling, and time-window extraction.

For Stage 1, define a small Python API and tests for adaptation order, invalid
input reporting, and replayable adapted inputs. Avoid committing to a GUI or a
specific streaming transport.

## Output adapters and triggers

After a tick commits, host-side output adapters can serialize state, write
files, publish messages, or convert model results to downstream formats.
Triggered actions should be explicit requests in the model result and should
not run if the transition fails.

Specify ordering and error behavior before exposing side effects. The Python
runtime should make these semantics testable; adapters that depend on GUI or
GPU services belong to those later stages.

## Implemented API

```python
runtime = Runtime(program)
runtime.register_input_adapter("camera", normalize_camera_frame)
runtime.register_output_adapter("logger", record_committed_frame)
runtime.register_trigger("alarm", send_alarm)
```

Input adapters transform matching named values before commit. Output adapters
observe a copied frame after commit; failures report that the state transition
already committed. Adapter ordering and failure behavior are covered by tests
and specified in [`../stage1-contract.md`](../stage1-contract.md). Model-level
actions and triggers remain intentionally unimplemented.
