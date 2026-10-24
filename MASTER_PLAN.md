# BrainCode Master Plan

BrainCode is a temporal DSL for deterministic, synchronous state models.
Rules compute new frames from committed history, while population and tensor
forms express data-parallel work. The Python runtime is currently a serial
reference implementation. Hardware parallelism and “superspeed” are goals to
validate with measured workloads, not current performance claims.

## Stage 1 — Python foundation (complete)

Stabilize the language and compiler, establish the synchronous execution
contract, and provide tests, reproducible run manifests, validation, resource
limits, and a serial backend that later implementations can use as a
correctness reference.

## Stage 2 — VS Code workbench (in progress)

- **2a — Extension foundation:** prototype implemented in `vscode-extension/`.
  It registers `.bc`, provides syntax highlighting and snippets, and invokes
  the existing CLI for compile, inspect, run, and replay. Next validate it in
  the Extension Development Host and prepare packaging.
- **2b — Compiler-backed language support:** add diagnostics and editor
  intelligence by reusing compiler knowledge, without creating a competing
  parser.
- **2c — Run results and inspection:** organize run configurations, artifacts,
  and saved-result inspection; add visualizations or interactive debugging
  only when runtime capabilities justify them.

Start in VS Code rather than building a standalone GUI. Keep `.bc` text and the
compiler/runtime independent of the editor.

## Stage 3 — GPU execution (planned)

Select useful data-parallel workloads, implement a bounded GPU backend, and
compare it against the serial reference using conformance tests and benchmarks.
Report supported features, hardware, transfer and compilation costs, precision,
and measured speedups. Parallel semantics alone do not guarantee a faster
execution.

## Stage 4 — Hosted BrainCode API (proposed)

Offer versioned compile, run, status, result, and replay endpoints. Reuse the
compiler, manifests, and backend interface. A limited CPU-backed service may
precede broad GPU support, but submitted models must run in isolated workers
with authentication, strict resource and output limits, tenant separation, and
clear retention policies. Do not accept arbitrary Python host functions in
the hosted MVP.

## Cross-cutting proposals (not assigned to a stage)

- Add [paired Python reference implementations](docs/suggestions/python_reference_implementations.md)
  beside selected BrainCode examples to compare expression and semantics, not
  runtime speed.
- Refine the [Python API and NumPy interoperability](docs/suggestions/python_numpy_interoperability.md)
  while treating array interchange as distinct from a future accelerated
  NumPy backend.

## Product principles

- Keep BrainCode source syntax and runtime semantics authoritative; editor,
  GPU, and cloud services are clients or backends, not alternative languages.
- Preserve the serial runtime as the correctness reference.
- Make unsupported features, resource bounds, and backend differences
  explicit.
- Validate user value and performance with representative models before
  expanding scope or making speed claims.

See [`docs/05-concept-improvements.md`](./docs/05-concept-improvements.md),
the [staged suggestions](./docs/suggestions/README.md), and the
[long-term product roadmap](./docs/long-term-improvement-plan.md) for detail.
