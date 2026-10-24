# Stage 2 suggestion: GUI authoring, runs, and inspection

Stage 2 adds a GUI on top of the stable Stage 1 language and Python runtime.
The GUI should expose the model's real semantics rather than inventing a
separate visual-only language.

## Authoring

- Provide an editor with syntax highlighting, completion, formatting,
  diagnostics, navigation, and documentation.
- Show state signals, inputs, temporal dependencies, population dimensions,
  iteration domains, and data flow.
- Keep `.bc` text first-class; visual tools should explain and assist with
  source rather than silently replacing or obscuring it.

## Run workflow

- Manage model files, input configurations, parameters, run settings, and
  outputs as one project.
- Launch runs and show progress, logs, errors, and resource use.
- Present manifests and replay information from the Stage 1 run contract.

## Inspection and debugging

- Plot selected scalar signals and show population/tensor slices across ticks.
- Support breakpoints, pause/resume, stepping, history inspection, and
  comparisons where the selected backend can provide them.
- Trace values back to rules and inputs when the runtime records this detail.
- Make observability limits explicit rather than promising unsupported
  instruction-level GPU debugging.

Stage 2 implementation should use the serial backend first; GPU-specific
workflow belongs to Stage 3.
