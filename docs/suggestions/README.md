# Staged Suggestions

These documents track completed Stage 1 foundation work and planned later
stages:

1. **Stage 1 — Python foundation:** implement and validate the language,
   reference runtime, reproducibility, and contracts needed by later stages.
   Stage 1 may define and test GUI/GPU-facing interfaces, but it does not
   implement the GUI or GPU backend.
2. **Stage 2 — VS Code workbench:** build an extension for BrainCode authoring,
   runs, and result inspection on top of the stable Python foundation. Reassess
   a standalone GUI after validating the workflow with users.
3. **Stage 3 — GPU:** implement accelerated execution for useful supported
   workloads and validate it against the Python reference runtime.

## Stage 1 — Python foundation (completed)

- [Language semantics, values, and diagnostics](./done_stage1_language_semantics_values_diagnostics.md)
- [Input/output pipe adapters](./done_stage1_input_output_pipeadapters.md)
- [Reproducibility, history, and resource limits](./done_stage1_reproducibility_history_resources.md)
- [Parallelism readiness](./done_stage1_parallelism_readiness.md)
- [Examples and AI evaluation](./done_stage1_examples_and_ai_evaluation.md)

## Stage 2 — VS Code workbench

- [VS Code authoring, runs, and inspection](./stage2_gui_authoring_runs_inspection.md)

## Stage 3 — GPU

- [GPU backend, conformance, and performance](./stage3_gpu_backend_conformance_performance.md)

The Stage 1 work deliberately prepares for later capabilities without
presenting them as already implemented. See the
[stage overview and priority index](../05-concept-improvements.md) and the
[product roadmap](../long-term-improvement-plan.md).
