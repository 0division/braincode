# BrainCode: Further Concept Improvements

This page indexes suggestions by the project's three development stages.
Stage 1 is Python-only, but it should establish semantics, tests, and
interfaces that make the GUI and GPU stages practical. This means preparing
for later stages now, not implementing their product features early. The
suggestions are proposals, not claims about implemented features.

## Stage 1 — Python foundation

1. [Language semantics, values, and diagnostics](./suggestions/stage1_language_semantics_values_diagnostics.md)
2. [Input/output pipe adapters](./suggestions/stage1_input_output_pipeadapters.md)
3. [Reproducibility, history, and resource limits](./suggestions/stage1_reproducibility_history_resources.md)
4. [Parallelism readiness](./suggestions/stage1_parallelism_readiness.md)
5. [Examples and AI evaluation](./suggestions/stage1_examples_and_ai_evaluation.md)

## Stage 2 — GUI

- [GUI authoring, runs, and inspection](./suggestions/stage2_gui_authoring_runs_inspection.md)

## Stage 3 — GPU

- [GPU backend, conformance, and performance](./suggestions/stage3_gpu_backend_conformance_performance.md)

## Open questions for the next design pass

1. Is BrainCode's core unit a scalar signal, an entity, or both?
2. Which population-scale example best represents the intended parallelism?
3. Should a model be self-contained, or depend on host-provided initial frames
   and inputs?
4. Which value types are essential for the first useful implementation?

Use Stage 1 to answer foundational questions and define contracts for later
stages. See the [staged suggestions index](./suggestions/README.md) and the
[long-term improvement plan](./long-term-improvement-plan.md) for sequencing.
