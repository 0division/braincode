# BrainCode for Visual Studio Code

This extension provides basic `.bc` syntax highlighting, snippets, and
commands that invoke the existing BrainCode Python CLI. It does not implement
the BrainCode parser or runtime.

## Requirements

- Visual Studio Code 1.85 or later.
- Python 3.11 or later with BrainCode installed in the selected environment.

From the BrainCode repository root, install the package into the environment
you want VS Code to use:

```powershell
python -m pip install -e .
```

Set `braincode.pythonPath` in VS Code settings if the correct Python
executable is not named `python`. For example, on Windows this can be the
workspace virtual environment's `Scripts\python.exe`.

## Try the extension from this checkout

1. Open the `vscode-extension` folder in VS Code.
2. Press **F5** to launch an Extension Development Host.
3. In the new window, open a BrainCode workspace and a `.bc` model.
4. Use the Command Palette and search for `BrainCode`.

The extension has no build step or npm dependencies. If BrainCode is installed
in a virtual environment, set `braincode.pythonPath` to that environment's
Python executable so the CLI can be imported.

The commands are:

- **BrainCode: Compile Current Model** — writes `.bcc` and `.bcc.json` beside
  the source. It asks before replacing existing compile artifacts and uses
  parameters from an optional `.bc.in.json` file.
- **BrainCode: Inspect Current Model** — displays the compiler's JSON IR in
  the BrainCode output channel.
- **BrainCode: Run Current Model** — asks for an optional `.bc.in.json` file
  and writes the trace, Markdown report, and replay manifest into a unique
  `.braincode/runs/` directory in the workspace.
- **BrainCode: Replay Run Manifest** — replays a selected `.run.json` file and
  writes the replayed trace under `.braincode/runs/replays/`.

Execution is synchronous from the command's perspective and uses the serial
Python reference backend. There is no live progress, cancellation, debugger,
or GPU execution in this initial extension.

## Validation

From the repository root:

```powershell
python -m pytest -q tests/test_vscode_extension.py
```
