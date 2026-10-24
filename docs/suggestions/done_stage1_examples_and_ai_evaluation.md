# Completed Stage 1: Examples and AI evaluation

Stage 1 should turn examples into executable evidence for the Python language
and runtime, while keeping speculative syntax clearly labeled.

## Examples as specification

- State each example's initial frame, inputs, parameters, and expected output.
- Run supported examples in tests and use them as cross-backend conformance
  cases later.
- Clearly label proposal-only syntax that the current parser cannot compile.
- Include small conformance examples and larger workload sketches to reveal
  complexity and likely parallel domains.

## Evaluate AI authoring claims

Treat AI-assisted modeling as a hypothesis. The Stage 1 contract defines a
pre-registered evaluation protocol with bounded tasks, correctness criteria,
repair effort, and a fair host-language baseline. No experiment has been run,
so no advantage is claimed.

These activities are Stage 1 because they validate the language contract; they
do not require a GUI or GPU. Example fixtures and expected traces/manifests
are checked by the conformance tests.
