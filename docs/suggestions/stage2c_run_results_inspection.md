# Stage 2c suggestion: run results and inspection

Make saved BrainCode runs easy to find and understand in the VS Code
workbench. Start with the existing CLI, run configurations, traces, Markdown
reports, and replay manifests; add custom visualizations only when real usage
shows that opening these artifacts is insufficient.

## Initial workflow

- Select or edit a `.bc.in.json` configuration and launch a run through the
  existing CLI.
- Show standard output, errors, and completion status without hiding CLI
  details.
- Provide convenient access to the resulting trace, run report, and
  reproducibility manifest in the workspace.
- Support replay of saved manifests where required host functions and input
  adapters are available.

## Future inspection

- Add time-series plots and population/tensor views if representative models
  demonstrate a need beyond the saved artifacts.
- Make sampling, slicing, and size limits explicit for large frames.
- Link inspected values to source rules and inputs only when runtime records
  enough provenance to explain them reliably.
- Treat live progress, breakpoints, pause/resume, stepping, and step-back as
  separate runtime capabilities; saved-frame inspection does not provide
  interactive debugging by itself.
- State backend limitations clearly. GPU execution and GPU-specific
  inspection belong to Stage 3 or later.
