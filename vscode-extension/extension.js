"use strict";

const childProcess = require("child_process");
const fs = require("fs");
const path = require("path");
const vscode = require("vscode");

const CONFIG_GLOB = "**/*.bc.in.json";
const MANIFEST_GLOB = "**/*.run.json";
const EXCLUDED_GLOB = "**/{.git,.venv,node_modules,.braincode}/**";

function activate(context) {
  const output = vscode.window.createOutputChannel("BrainCode");
  context.subscriptions.push(output);

  const register = (command, handler) => {
    context.subscriptions.push(
      vscode.commands.registerCommand(command, async () => {
        try {
          await handler();
        } catch (error) {
          const message = error instanceof Error ? error.message : String(error);
          output.appendLine(`ERROR: ${message}`);
          output.show(true);
          await vscode.window.showErrorMessage(`BrainCode: ${message}`);
        }
      }),
    );
  };

  register("braincode.compile", async () => {
    const model = activeModel();
    if (!model) {
      return;
    }

    const configPath = await chooseRunConfig(model);
    if (configPath === undefined) {
      return;
    }

    const runConfig = configPath ? readRunConfig(configPath) : {};
    const parameters =
      runConfig.parameters === undefined ? {} : runConfig.parameters;
    if (
      parameters === null ||
      typeof parameters !== "object" ||
      Array.isArray(parameters)
    ) {
      throw new Error(`Run configuration parameters must be an object: ${configPath}`);
    }

    const stem = path.basename(model.sourcePath, path.extname(model.sourcePath));
    const expandedPath = path.join(path.dirname(model.sourcePath), `${stem}.bcc`);
    const irPath = `${expandedPath}.json`;
    if (fs.existsSync(expandedPath) || fs.existsSync(irPath)) {
      const choice = await vscode.window.showWarningMessage(
        `Replace existing compile artifacts for ${stem}?`,
        "Replace",
      );
      if (choice !== "Replace") {
        return;
      }
    }

    const args = [
      "compile",
      model.sourcePath,
      "--output",
      expandedPath,
      "--json-output",
      irPath,
      "--parameters",
      JSON.stringify(parameters),
    ];
    await runCli(output, model.workspace.uri.fsPath, args);
    await vscode.window.showInformationMessage(
      `BrainCode compiled ${path.basename(model.sourcePath)}.`,
    );
  });

  register("braincode.inspect", async () => {
    const model = activeModel();
    if (!model) {
      return;
    }
    await runCli(output, model.workspace.uri.fsPath, ["show", model.sourcePath]);
  });

  register("braincode.run", async () => {
    const model = activeModel();
    if (!model) {
      return;
    }
    const configPath = await chooseRunConfig(model);
    if (configPath === undefined) {
      return;
    }

    const runDirectory = createRunDirectory(model.workspace.uri.fsPath, model.sourcePath);
    const stem = path.basename(model.sourcePath, path.extname(model.sourcePath));
    const tracePath = path.join(runDirectory, `${stem}.output.json`);
    const reportPath = path.join(runDirectory, `${stem}.run.md`);
    const manifestPath = path.join(runDirectory, `${stem}.run.json`);
    const args = ["run", model.sourcePath];
    if (configPath) {
      args.push("--input-file", configPath);
    }
    args.push(
      "--output",
      tracePath,
      "--markdown-output",
      reportPath,
      "--manifest-output",
      manifestPath,
    );
    await runCli(output, model.workspace.uri.fsPath, args);
    const action = await vscode.window.showInformationMessage(
      `BrainCode run completed. Results: ${vscode.workspace.asRelativePath(tracePath)}`,
      "Open report",
    );
    if (action === "Open report") {
      const document = await vscode.workspace.openTextDocument(reportPath);
      await vscode.window.showTextDocument(document, { preview: true });
    }
  });

  register("braincode.replay", async () => {
    const workspace = activeWorkspace();
    if (!workspace) {
      return;
    }
    const manifestPath = await chooseManifest();
    if (!manifestPath) {
      return;
    }
    const replayDirectory = createRunDirectory(
      workspace.uri.fsPath,
      manifestPath,
      "replays",
    );
    const stem = path.basename(manifestPath).replace(/\.run\.json$/, "");
    const tracePath = path.join(replayDirectory, `${stem}.replay.output.json`);
    await runCli(output, workspace.uri.fsPath, [
      "replay",
      manifestPath,
      "--output",
      tracePath,
    ]);
    await vscode.window.showInformationMessage(
      `BrainCode replay completed. Results: ${vscode.workspace.asRelativePath(tracePath)}`,
    );
  });
}

function activeModel() {
  const editor = vscode.window.activeTextEditor;
  if (
    !editor ||
    editor.document.uri.scheme !== "file" ||
    !editor.document.fileName.toLowerCase().endsWith(".bc")
  ) {
    void vscode.window.showErrorMessage("Open a .bc model file first.");
    return undefined;
  }
  const workspace = vscode.workspace.getWorkspaceFolder(editor.document.uri);
  if (!workspace) {
    void vscode.window.showErrorMessage("Open the model inside a VS Code workspace first.");
    return undefined;
  }
  return {
    sourcePath: editor.document.uri.fsPath,
    workspace,
  };
}

function activeWorkspace() {
  const editor = vscode.window.activeTextEditor;
  if (editor) {
    const workspace = vscode.workspace.getWorkspaceFolder(editor.document.uri);
    if (workspace) {
      return workspace;
    }
  }
  if (vscode.workspace.workspaceFolders && vscode.workspace.workspaceFolders.length === 1) {
    return vscode.workspace.workspaceFolders[0];
  }
  void vscode.window.showErrorMessage(
    "Open a VS Code workspace to select a run manifest.",
  );
  return undefined;
}

async function chooseRunConfig(model) {
  const companionPath = `${model.sourcePath}.in.json`;
  const files = await vscode.workspace.findFiles(CONFIG_GLOB, EXCLUDED_GLOB);
  const paths = new Set(files.map((file) => file.fsPath));
  if (fs.existsSync(companionPath)) {
    paths.add(companionPath);
  }

  const items = [...paths].map((filePath) => ({
    label: path.basename(filePath),
    description: vscode.workspace.asRelativePath(filePath),
    filePath,
  }));
  items.sort((left, right) => left.filePath.localeCompare(right.filePath));
  const choices = [
    ...items,
    { label: "Browse for a run configuration…", filePath: undefined },
    { label: "Run without a configuration", filePath: null },
  ];
  const selected = await vscode.window.showQuickPick(choices, {
    placeHolder: "Choose a .bc.in.json run configuration",
  });
  if (!selected) {
    return undefined;
  }
  if (selected.label === "Browse for a run configuration…") {
    const files = await vscode.window.showOpenDialog({
      canSelectMany: false,
      openLabel: "Use run configuration",
      filters: { "BrainCode run configuration": ["json"] },
      defaultUri: vscode.Uri.file(companionPath),
    });
    return files && files.length ? files[0].fsPath : undefined;
  }
  return selected.filePath;
}

async function chooseManifest() {
  const files = await vscode.workspace.findFiles(MANIFEST_GLOB, EXCLUDED_GLOB);
  const items = files.map((file) => ({
    label: path.basename(file.fsPath),
    description: vscode.workspace.asRelativePath(file),
    filePath: file.fsPath,
  }));
  items.sort((left, right) => left.filePath.localeCompare(right.filePath));
  const selected = await vscode.window.showQuickPick(
    [
      ...items,
      { label: "Browse for a manifest…", filePath: undefined },
    ],
    { placeHolder: "Choose a BrainCode .run.json manifest to replay" },
  );
  if (!selected) {
    return undefined;
  }
  if (selected.filePath) {
    return selected.filePath;
  }
  const filesFromDialog = await vscode.window.showOpenDialog({
    canSelectMany: false,
    openLabel: "Replay manifest",
    filters: { "BrainCode run manifest": ["json"] },
  });
  return filesFromDialog && filesFromDialog.length
    ? filesFromDialog[0].fsPath
    : undefined;
}

function readRunConfig(configPath) {
  let config;
  try {
    config = JSON.parse(fs.readFileSync(configPath, "utf8"));
  } catch (error) {
    const detail = error instanceof Error ? error.message : String(error);
    throw new Error(`Could not read run configuration ${configPath}: ${detail}`);
  }
  if (!config || typeof config !== "object" || Array.isArray(config)) {
    throw new Error(`Run configuration must contain a JSON object: ${configPath}`);
  }
  return config;
}

function createRunDirectory(workspacePath, sourcePath, subdirectory = "") {
  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const modelName = path.basename(sourcePath, path.extname(sourcePath));
  const runPath = path.join(
    workspacePath,
    ".braincode",
    "runs",
    subdirectory,
    `${modelName}-${stamp}`,
  );
  fs.mkdirSync(runPath, { recursive: true });
  return runPath;
}

function runCli(output, cwd, args) {
  const pythonPath = vscode.workspace
    .getConfiguration("braincode")
    .get("pythonPath", "python");
  output.appendLine("");
  output.appendLine(`> ${pythonPath} -m braincode ${args[0]} (arguments omitted)`);
  output.show(true);

  return new Promise((resolve, reject) => {
    childProcess.execFile(
      pythonPath,
      ["-m", "braincode", ...args],
      {
        cwd,
        encoding: "utf8",
        maxBuffer: 16 * 1024 * 1024,
        windowsHide: true,
      },
      (error, stdout, stderr) => {
        if (stdout) {
          output.append(stdout);
          if (!stdout.endsWith("\n")) {
            output.appendLine("");
          }
        }
        if (stderr) {
          output.append(stderr);
          if (!stderr.endsWith("\n")) {
            output.appendLine("");
          }
        }
        if (error) {
          output.appendLine(`Command failed: ${error.message}`);
          reject(error);
          return;
        }
        resolve();
      },
    );
  });
}

function deactivate() {}

module.exports = {
  activate,
  deactivate,
};
