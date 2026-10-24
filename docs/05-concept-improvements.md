# BrainCode: Further Concept Improvements

This page tracks work by the project's four development stages and separate
cross-cutting proposals. Stage 1 is the Python foundation: its work is
complete and documented, while the VS Code workbench, GPU execution, and cloud
API remain later-stage product work. Completion does not imply full static
type inference, model-level actions, a process-wide memory quota, or empirical
AI evaluation; those limitations are called out in the completed documents.

## Stage 1 — Python foundation (completed)

1. [Language semantics, values, and diagnostics](./suggestions/done_stage1_language_semantics_values_diagnostics.md)
2. [Input/output pipe adapters](./suggestions/done_stage1_input_output_pipeadapters.md)
3. [Reproducibility, history, and resource limits](./suggestions/done_stage1_reproducibility_history_resources.md)
4. [Parallelism readiness](./suggestions/done_stage1_parallelism_readiness.md)
5. [Examples and AI evaluation](./suggestions/done_stage1_examples_and_ai_evaluation.md)

## Stage 2 — VS Code workbench

- [VS Code workbench overview](./suggestions/stage2_gui_authoring_runs_inspection.md)
- [2a — VS Code extension foundation](./suggestions/stage2a_vscode_extension_foundation.md)
- [2b — Compiler-backed language support](./suggestions/stage2b_compiler_language_support.md)
- [2c — Run results and inspection](./suggestions/stage2c_run_results_inspection.md)

## Stage 3 — GPU

- [GPU backend, conformance, and performance](./suggestions/stage3_gpu_backend_conformance_performance.md)

## Stage 4 — Cloud API

- [Hosted BrainCode API](./suggestions/stage4_cloud_api_service.md)

## Cross-cutting proposals (not assigned to a stage)

- [Paired Python reference implementations](./suggestions/python_reference_implementations.md)
- [Python API and NumPy interoperability](./suggestions/python_numpy_interoperability.md)

## Stage 1 decisions

1. The language supports both scalar temporal signals and declared
   population/tensor state.
2. Cellular automata and stencil examples are representative regular
   population workloads; matrix multiplication and all-pairs models cover
   different computational patterns.
3. Model source stays separate from host-provided initial state, parameters,
   and tick-indexed inputs; replay manifests package the run configuration.
4. Declared values support `Bool`, `Int32`, `Int64`, `Float32`, and `Float64`.

See the [Stage 1 contract](./stage1-contract.md), the
[staged suggestions index](./suggestions/README.md), and the
[long-term improvement plan](./long-term-improvement-plan.md) for sequencing.
