# BrainCode Long-Term Improvement Plan

This roadmap develops BrainCode from the v0.2 reference implementation into a
well-specified, reliable language with interchangeable execution backends. The
serial Python runtime remains the semantic reference; optimizations must match
its tested behavior rather than silently changing the language.

## Guiding principles

1. Specify behavior before optimizing it.
2. Keep model rules, host-provided input data, and compiled artifacts separate.
3. Preserve deterministic, synchronous tick semantics across every backend.
4. Make failures, resource limits, and execution provenance observable.
5. Treat performance claims as measured results against reproducible baselines.

## Phase 1 — Stabilize the v0.2 language contract

- Publish a compact grammar and define identifier, literal, precedence, and
  expression-call rules.
- Specify temporal indexing, initialization, boundary behavior, hold behavior,
  simultaneous writes, reductions, and failure atomicity.
- Define integer, floating-point, Boolean, null, and collection semantics.
- Specify `.bcc` expanded-source compatibility and versioning of `.bcc.json`.
- Improve diagnostics with source spans and actionable error messages.

**Exit criteria:** each documented behavior has a conformance test; the same
test vectors produce identical traces after source and compiled-artifact loads.

## Phase 2 — Make programs and runs self-describing

- Add explicit declarations for state, inputs, parameters, and their types and
  shapes, while retaining host configuration as a supported execution boundary.
- Validate input keys, dimensions, historical depth, and tick-input schedules
  before beginning execution.
- Define a stable `.bc.in.json` schema for example and production run settings.
- Record source and input hashes, compiler/runtime versions, parameters, and
  execution settings in a run manifest.
- Support replay from a saved input package without relying on ambient files or
  mutable host callbacks.

**Exit criteria:** a saved run package can reproduce its trace in a clean
environment, with missing or incompatible inputs reported before execution.

## Phase 3 — Control memory and failure behavior

- Add configurable history retention and document how temporal reads interact
  with retained frames.
- Introduce checkpoints and resume, including version compatibility checks.
- Define cancellation and resource budgets for ticks, population sizes,
  allocations, and reductions.
- Ensure interrupted or failed ticks remain atomic and report the last
  successfully committed tick.
- Keep external side effects outside rules; if actions are later introduced,
  specify transactional or idempotency guarantees first.

**Exit criteria:** bounded-memory runs, checkpoint/resume, and cancellation
preserve trace equivalence with uninterrupted serial execution.

## Phase 4 — Improve the reference runtime and conformance suite

- Add property-based tests for expression evaluation, history access, and
  tensor indexing.
- Build reusable fixtures covering scalar, grid, stencil, reduction, and
  invalid-input cases.
- Profile representative workloads before changing runtime data structures.
- Optimize the serial runtime only when benchmarks show a measurable benefit
  and conformance remains unchanged.

**Exit criteria:** reproducible correctness and performance baselines run in
continuous integration; optimization results include machine and workload
details.

## Phase 5 — Add parallel execution backends

- Establish a backend interface and keep scheduling details out of language
  semantics.
- Prototype an optimized CPU backend first, then evaluate GPU/CUDA or other
  accelerators against concrete workloads.
- Specify deterministic reduction behavior and floating-point tolerance before
  allowing backend-specific reassociation.
- Add differential tests that compare each backend to the serial reference.
- Benchmark throughput, memory use, compilation overhead, and data transfer
  cost separately.

**Exit criteria:** supported programs produce documented equivalent results
across the serial and parallel backends, with transparent fallback and
capability reporting.

## Phase 6 — Evaluate usability and AI-assisted authoring

- Add editor support for syntax highlighting, diagnostics, formatting, and
  navigation only after the grammar is stable enough to support tooling.
- Measure authoring effort and correctness on representative tasks.
- Compare AI-assisted BrainCode workflows with equivalent host-language
  baselines using reproducible tasks and human review.
- Document where the temporal/data-parallel model is clearer or safer, and
  where it adds unnecessary complexity.

**Exit criteria:** usability claims are based on recorded task outcomes, not
only illustrative examples.

## Near-term priorities

1. Finish the language grammar and runtime validation contract.
2. Add run manifests and deterministic replay inputs.
3. Build conformance/property tests around the serial runtime.
4. Establish benchmark baselines before backend optimization.
5. Use those baselines to decide whether CPU or GPU parallelism is the next
   implementation target.
