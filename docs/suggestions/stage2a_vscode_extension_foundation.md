# Stage 2a suggestion: VS Code extension foundation

Build the first BrainCode authoring and run experience as a VS Code extension.
Use VS Code's existing editor, workspace, tasks, terminals, command palette,
and output channels instead of creating a standalone GUI or custom process
manager.

## Initial scope

- Register `.bc` as a BrainCode language with syntax highlighting, comments,
  bracket handling, and useful snippets.
- Add commands to compile, inspect, run, and replay a model by invoking the
  existing BrainCode CLI.
- Allow users to choose or edit a `.bc.in.json` run configuration and report
  CLI output and failures clearly.
- Leave generated `.bcc`, JSON IR, traces, Markdown reports, and run manifests
  as normal workspace files, with commands to open the relevant artifacts.

Keep the extension a client of the compiler and runtime, not a second
interpreter. Start with the Python serial backend and validate the workflow
against the checked-in examples on supported platforms.

## Boundaries

- Do not duplicate BrainCode parsing or execution in TypeScript.
- Do not require a new project format while the workspace and existing run
  files are sufficient.
- Do not imply that a Run command provides live progress or interactive
  debugging; those require runtime support.
- Reassess a standalone desktop application only if user needs cannot be met
  in VS Code.
