# Stage 2 suggestion: VS Code authoring, runs, and inspection

Use a VS Code extension as BrainCode's first integrated authoring and run
workbench instead of starting with a standalone GUI. VS Code supplies an
editor, workspace, command palette, terminal, and extension APIs; BrainCode
continues to own its language semantics, compiler, and runtime. The extension
is a client of those tools, not a second interpreter or a new source of truth.

Keep `.bc` text and the existing Python serial runtime first-class. Treat each
VS Code workspace as the initial project container, using existing `.bc`,
`.bc.in.json`, run-manifest, and output files where practical. Do not require a
new project format before the workflow proves it is needed.

## Initial extension scope

- Register `.bc` as a BrainCode language and provide syntax highlighting,
  comments, brackets, and useful snippets.
- Add commands to compile, inspect, run, and replay a model through the
  existing BrainCode CLI. Let the user select or edit a `.bc.in.json` run
  configuration; show command output, diagnostics, and failures without
  hiding the underlying CLI details.
- Present generated traces, Markdown reports, and replay manifests as normal
  workspace files, with convenient commands to open the relevant artifacts.
- Use VS Code tasks, terminals, and output channels for the first run workflow
  rather than building custom process management or a webview-heavy UI.

## Language features and inspection

- Add completion, navigation, formatting, and source diagnostics only by
  reusing compiler knowledge. Prefer a small language server or structured CLI
  interface once the compiler exposes the required stable APIs; do not
  independently parse BrainCode in the extension.
- Make the current serial execution and its limitations explicit. A completed
  run can be inspected through its frames and manifests; live progress,
  breakpoints, pause/resume, and stepping require runtime support and are not
  implied by a Run command.
- Consider plots or tensor/grid webviews after real examples show that opening
  generated files is insufficient and the runtime can provide the needed
  observations.

## Suggested sequence and boundaries

1. Prototype extension packaging, `.bc` language registration, and a Run
   command against the existing CLI.
2. Add configuration selection, compile/inspect/replay commands, and clear
   error reporting; test against the checked-in examples on supported
   platforms.
3. Add compiler-backed language features and richer result views as stable
   interfaces become available.

Do not build a visual-only model editor, duplicate the compiler/runtime in
TypeScript, or commit to a standalone desktop GUI during this stage. Reassess a
standalone application later if user needs cannot be met in VS Code. GPU
execution and GPU-specific debugging remain Stage 3 or later work.
