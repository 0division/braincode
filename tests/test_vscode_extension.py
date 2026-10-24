from __future__ import annotations

import json
from pathlib import Path
import re
import tempfile
import unittest

from braincode.cli import main as cli_main


ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "vscode-extension"


class VSCodeExtensionTests(unittest.TestCase):
    def test_extension_manifest_points_to_existing_language_resources(self) -> None:
        manifest = json.loads((EXTENSION / "package.json").read_text(encoding="utf-8"))
        language = manifest["contributes"]["languages"][0]
        grammar = manifest["contributes"]["grammars"][0]
        snippets = manifest["contributes"]["snippets"][0]
        launch = json.loads(
            (EXTENSION / ".vscode" / "launch.json").read_text(encoding="utf-8")
        )

        self.assertIn(".bc", language["extensions"])
        self.assertEqual(language["id"], grammar["language"])
        self.assertTrue((EXTENSION / language["configuration"]).is_file())
        self.assertTrue((EXTENSION / grammar["path"]).is_file())
        self.assertTrue((EXTENSION / snippets["path"]).is_file())
        self.assertEqual(launch["configurations"][0]["type"], "extensionHost")
        json.loads((EXTENSION / language["configuration"]).read_text(encoding="utf-8"))
        json.loads((EXTENSION / grammar["path"]).read_text(encoding="utf-8"))
        json.loads((EXTENSION / snippets["path"]).read_text(encoding="utf-8"))

    def test_declared_commands_are_activated_and_registered(self) -> None:
        manifest = json.loads((EXTENSION / "package.json").read_text(encoding="utf-8"))
        command_ids = {
            item["command"] for item in manifest["contributes"]["commands"]
        }
        activation_events = set(manifest["activationEvents"])
        source = (EXTENSION / manifest["main"]).read_text(encoding="utf-8")
        registered_commands = set(
            re.findall(r'register\("(braincode\.[a-z]+)"', source)
        )

        self.assertEqual(command_ids, registered_commands)
        self.assertEqual(
            command_ids,
            {
                event.removeprefix("onCommand:")
                for event in activation_events
                if event.startswith("onCommand:")
            },
        )
        self.assertIn('"pythonPath"', source)
        self.assertIn('"braincode"', source)
        self.assertIn("(arguments omitted)", source)
        self.assertIn("execFile(", source)

    def test_extension_documentation_covers_commands_and_requirements(self) -> None:
        manifest = json.loads((EXTENSION / "package.json").read_text(encoding="utf-8"))
        readme = " ".join(
            (EXTENSION / "README.md").read_text(encoding="utf-8").split()
        )

        for command in manifest["contributes"]["commands"]:
            self.assertIn(command["title"], readme)
        self.assertIn("Python 3.11", readme)
        self.assertIn("serial Python reference backend", readme)

    def test_cli_workflow_used_by_extension_compiles_runs_and_replays(self) -> None:
        source = ROOT / "docs" / "examples" / "counter.bc"
        config = ROOT / "docs" / "examples" / "counter.bc.in.json"
        with tempfile.TemporaryDirectory() as directory:
            expanded = Path(directory) / "counter.bcc"
            ir = Path(directory) / "counter.bcc.json"
            trace = Path(directory) / "counter.output.json"
            report = Path(directory) / "counter.run.md"
            manifest = Path(directory) / "counter.run.json"
            replay = Path(directory) / "counter.replay.json"

            self.assertEqual(
                cli_main(
                    [
                        "compile",
                        str(source),
                        "--output",
                        str(expanded),
                        "--json-output",
                        str(ir),
                        "--parameters",
                        "{}",
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "run",
                        str(source),
                        "--input-file",
                        str(config),
                        "--output",
                        str(trace),
                        "--markdown-output",
                        str(report),
                        "--manifest-output",
                        str(manifest),
                    ]
                ),
                0,
            )
            self.assertEqual(
                cli_main(
                    [
                        "replay",
                        str(manifest),
                        "--output",
                        str(replay),
                    ]
                ),
                0,
            )
            self.assertTrue(expanded.is_file())
            self.assertTrue(ir.is_file())
            self.assertTrue(report.is_file())
            self.assertEqual(
                json.loads(trace.read_text(encoding="utf-8")),
                json.loads(replay.read_text(encoding="utf-8")),
            )


if __name__ == "__main__":
    unittest.main()
