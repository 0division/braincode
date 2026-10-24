# TODO — Stage 2 overview: VS Code workbench

Use a VS Code extension as BrainCode's first integrated authoring and run
environment instead of starting with a standalone GUI. VS Code provides the
editor and workspace; BrainCode remains responsible for its language
semantics, compiler, and runtime. The extension should call those existing
components rather than reimplementing them.

Keep `.bc` text and the Python serial runtime first-class. Use the workspace
and existing `.bc.in.json`, run-manifest, and output files as the initial
project workflow. Avoid introducing a new project format or custom UI before
there is a demonstrated need.

Stage 2 is best treated as several related but separately deliverable
suggestions:

- **2a — [VS Code extension foundation](./work_stage2a_vscode_extension_foundation.md):**
  register `.bc` files and invoke the existing CLI from editor commands.
- **2b — [Compiler-backed language support](./todo_stage2b_compiler_language_support.md):**
  add diagnostics and editor intelligence without duplicating BrainCode
  parsing or semantics in the extension.
- **2c — [Run results and inspection](./todo_stage2c_run_results_inspection.md):**
  organize run configurations and artifacts first; add richer inspection
  only when supported by runtime capabilities.

Build and validate these capabilities incrementally against the checked-in
examples. Do not promise live progress, breakpoints, pause/resume, stepping,
or GPU-specific debugging until the runtime and selected backend actually
support them. Reassess a standalone application only if user needs outgrow
the VS Code workflow. GPU execution remains Stage 3 or later.
