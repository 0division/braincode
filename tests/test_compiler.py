from __future__ import annotations

import json
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from braincode.compiler import compile_file, compile_source, load_compiled, save_compiled
from braincode.expanded import render_expanded
from braincode.compiler import BrainCodeCompileError
from braincode.runtime import BrainCodeRuntimeError, Runtime
from braincode.cli import main as cli_main
from braincode.example_runner import example_configs, run_all_examples
from braincode.manifest import replay_run_manifest


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES = ROOT / "docs" / "examples"


class CompilerTests(unittest.TestCase):
    def test_every_example_compiles(self) -> None:
        examples = sorted(EXAMPLES.glob("*.bc"))
        self.assertEqual(len(examples), 16)
        for example in examples:
            with self.subTest(example=example.name):
                compile_file(example)

    def test_every_example_runs_at_small_scale(self) -> None:
        cases = example_configs()
        self.assertEqual(set(cases), {path.name for path in EXAMPLES.glob("*.bc")})
        for filename, config in cases.items():
            with self.subTest(example=filename):
                program = compile_file(EXAMPLES / filename)
                runtime = Runtime(
                    program,
                    initial_state=config.initial_state,
                    parameters=config.parameters,
                    initial_history=config.initial_history,
                )
                initial_frames = len(runtime.frames)
                self.assertEqual(
                    len(runtime.run(config.ticks, input_frames=config.inputs)),
                    initial_frames + config.ticks,
                )

    def test_committed_example_traces_and_manifests_are_conformant(self) -> None:
        output_dir = EXAMPLES / "output"
        for filename, config in example_configs().items():
            with self.subTest(example=filename):
                expected = json.loads(
                    (output_dir / f"{Path(filename).stem}.output.json")
                    .read_text(encoding="utf-8")
                )
                program = compile_file(EXAMPLES / filename)
                frames = Runtime(
                    program,
                    initial_state=config.initial_state,
                    parameters=config.parameters,
                    initial_history=config.initial_history,
                ).run(config.ticks, input_frames=config.inputs)
                self.assertEqual(frames, expected)
                self.assertEqual(
                    replay_run_manifest(
                        output_dir / f"{Path(filename).stem}.run.json"
                    ),
                    expected,
                )

    def test_utf8_mapper_encodes_every_length(self) -> None:
        cases = {
            0x41: ([0x41], [0x41, None, None, None]),
            0x7F: ([0x7F], [0x7F, None, None, None]),
            0x80: ([0xC2, 0x80], [0xC2, 0x80, None, None]),
            0x7FF: ([0xDF, 0xBF], [0xDF, 0xBF, None, None]),
            0x800: ([0xE0, 0xA0, 0x80], [0xE0, 0xA0, 0x80, None]),
            0xD7FF: ([0xED, 0x9F, 0xBF], [0xED, 0x9F, 0xBF, None]),
            0xE000: ([0xEE, 0x80, 0x80], [0xEE, 0x80, 0x80, None]),
            0xFFFF: ([0xEF, 0xBF, 0xBF], [0xEF, 0xBF, 0xBF, None]),
            0x10000: ([0xF0, 0x90, 0x80, 0x80], [0xF0, 0x90, 0x80, 0x80]),
            0x10FFFF: ([0xF4, 0x8F, 0xBF, 0xBF], [0xF4, 0x8F, 0xBF, 0xBF]),
            0xE9: ([0xC3, 0xA9], [0xC3, 0xA9, None, None]),
            0x20AC: ([0xE2, 0x82, 0xAC], [0xE2, 0x82, 0xAC, None]),
            0x1F600: ([0xF0, 0x9F, 0x98, 0x80], [0xF0, 0x9F, 0x98, 0x80]),
        }
        program = compile_file(EXAMPLES / "unicode-to-utf8-mapper.bc")
        for codepoint, (encoded, slots) in cases.items():
            with self.subTest(codepoint=hex(codepoint)):
                result = Runtime(
                    program,
                    initial_state={"unicode_in": codepoint},
                ).run(1)[-1]
                self.assertTrue(result["valid_unicode"])
                self.assertEqual(result["utf8_out_bytes"], encoded)
                self.assertEqual(result["utf8_out_length"], len(encoded))
                self.assertEqual(
                    [result[f"utf8_out_char{index}"] for index in range(4)],
                    slots,
                )
                self.assertEqual(
                    bytes(result["utf8_out_bytes"]),
                    chr(codepoint).encode("utf-8"),
                )

    def test_utf8_mapper_rejects_non_scalar_values(self) -> None:
        program = compile_file(EXAMPLES / "unicode-to-utf8-mapper.bc")
        for codepoint in (-1, 0xD800, 0xDFFF, 0x110000):
            with self.subTest(codepoint=hex(codepoint)):
                result = Runtime(
                    program,
                    initial_state={"unicode_in": codepoint},
                ).run(1)[-1]
                self.assertFalse(result["valid_unicode"])
                self.assertEqual(result["utf8_out_bytes"], [])
                self.assertEqual(result["utf8_out_length"], 0)
                self.assertTrue(all(
                    result[f"utf8_out_char{index}"] is None
                    for index in range(4)
                ))

    def test_automata_and_matrix_results(self) -> None:
        rule110_program = compile_file(EXAMPLES / "cellular-automaton-1d-rule110.bc")
        self.assertNotIn("rule110(", rule110_program.program.source)
        for neighborhood in range(8):
            cells = [False] * 7
            cells[2:5] = [
                bool((neighborhood >> 2) & 1),
                bool((neighborhood >> 1) & 1),
                bool(neighborhood & 1),
            ]
            with self.subTest(neighborhood=f"{neighborhood:03b}"):
                output = Runtime(
                    rule110_program,
                    initial_state={"cells": cells},
                ).run(1)[-1]["cells"][3]
                expected = bool((110 >> neighborhood) & 1)
                self.assertEqual(output, expected)

        blinker = [
            [False, False, False, False, False],
            [False, False, True, False, False],
            [False, False, True, False, False],
            [False, False, True, False, False],
            [False, False, False, False, False],
        ]
        next_grid = Runtime(
            compile_file(EXAMPLES / "cellular-automaton-2d-conway.bc"),
            initial_state={"cells": blinker},
            parameters={"WIDTH": 5, "HEIGHT": 5},
        ).run(1)[-1]["cells"]
        self.assertEqual(
            next_grid[2], [False, True, True, True, False]
        )
        self.assertEqual(
            [row[2] for row in next_grid],
            [False, False, True, False, False],
        )

        life_3d = compile_file(EXAMPLES / "cellular-automaton-3d-life.bc")
        for count, alive, expected in (
            (4, False, False),
            (5, True, True),
            (6, False, True),
            (7, True, True),
            (8, True, False),
        ):
            cells = [
                [[False for _ in range(3)] for _ in range(3)]
                for _ in range(3)
            ]
            cells[1][1][1] = alive
            neighbors = [
                (0, 0, 0), (0, 0, 1), (0, 0, 2),
                (0, 1, 0), (0, 1, 2), (0, 2, 0),
                (0, 2, 1), (0, 2, 2),
            ]
            for x, y, z in neighbors[:count]:
                cells[x][y][z] = True
            result = Runtime(
                life_3d,
                initial_state={"cells": cells},
                parameters={"WIDTH": 3, "HEIGHT": 3, "DEPTH": 3},
            ).run(1)[-1]["cells"][1][1][1]
            with self.subTest(neighbors=count, alive=alive):
                self.assertEqual(result, expected)

        product = Runtime(
            compile_file(EXAMPLES / "dense-matrix-multiply-proposal.bc"),
            initial_state={"A": [[1, 2], [3, 4]], "B": [[5, 6], [7, 8]]},
            parameters={"N": 2},
        ).run(1)[-1]["C"]
        self.assertEqual(product, [[19, 22], [43, 50]])

    def test_compiled_artifact_round_trips(self) -> None:
        program = compile_file(EXAMPLES / "counter.bc")
        with tempfile.TemporaryDirectory() as directory:
            artifact = Path(directory) / "counter.bcc.json"
            save_compiled(program, artifact)
            loaded = load_compiled(artifact)
            result = Runtime(loaded, initial_state={"counter": 2}).run(2)
        self.assertEqual(result[-1]["counter"], 4)

    def test_cli_writes_expanded_bcc_and_json_ir_pair(self) -> None:
        program_path = EXAMPLES / "cellular-automaton-1d-rule110.bc"
        initial = {"cells": [False, False, False, True, False, False, False]}
        with tempfile.TemporaryDirectory() as directory:
            bcc_path = Path(directory) / "rule110.bcc"
            json_path = Path(directory) / "rule110.bcc.json"
            with redirect_stdout(StringIO()):
                result = cli_main([
                    "compile",
                    str(program_path),
                    "--output",
                    str(bcc_path),
                    "--json-output",
                    str(json_path),
                ])
            self.assertEqual(result, 0)
            self.assertTrue(bcc_path.is_file())
            self.assertTrue(json_path.is_file())

            expanded_source = bcc_path.read_text(encoding="utf-8")
            self.assertNotIn("\neach ", expanded_source)
            self.assertIn("# instance (:i=0)", expanded_source)
            self.assertIn(":cells[0] =", expanded_source)
            self.assertIn(":cells[6] =", expanded_source)

            expanded_program = load_compiled(bcc_path)
            expanded_result = Runtime(
                expanded_program, initial_state=initial
            ).run(1)[-1]["cells"]
            json_program = load_compiled(json_path)
            json_result = Runtime(
                json_program, initial_state=initial
            ).run(1)[-1]["cells"]
        expected = [False, False, True, True, False, False, False]
        self.assertEqual(expanded_result, expected)
        self.assertEqual(json_result, expected)

    def test_cli_compile_does_not_create_files_without_output_options(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "counter.bc"
            source_path.write_text(":counter = :counter~1 + 1\n", encoding="utf-8")
            stdout = StringIO()
            with redirect_stdout(stdout):
                result = cli_main(["compile", str(source_path)])
            self.assertEqual(result, 0)
            self.assertEqual(len(list(Path(directory).iterdir())), 1)
            self.assertIn(":counter =", stdout.getvalue())

    def test_example_runner_writes_all_artifacts_to_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            summary = run_all_examples(directory)
            output = Path(directory)
            self.assertEqual(len(summary), 16)
            self.assertTrue((output / "summary.json").is_file())
            self.assertTrue((output / "run.log").is_file())
            self.assertTrue((output / "run-summary.md").is_file())
            self.assertIn("PASS counter.bc", (output / "run.log").read_text())
            self.assertIn("counter.bc.in.json", (output / "run-summary.md").read_text())
            for entry in summary:
                with self.subTest(example=entry["source"]):
                    self.assertTrue((output / entry["expanded_source"]).is_file())
                    self.assertTrue((output / entry["json_ir"]).is_file())
                    self.assertTrue((output / entry["trace"]).is_file())
                    self.assertTrue((output / entry["manifest"]).is_file())
                    report = output / entry["markdown"]
                    self.assertTrue(report.is_file())
                    report_text = report.read_text(encoding="utf-8")
                    self.assertIn("## Input data", report_text)
                    self.assertIn("## BrainCode source", report_text)
                    self.assertIn("## Output", report_text)
                    self.assertTrue((EXAMPLES / entry["input"]).is_file())

    def test_example_runner_runs_without_writing_files_when_output_is_omitted(self) -> None:
        summary = run_all_examples(None)
        self.assertEqual(len(summary), 16)
        self.assertTrue(all(entry["expanded_source"] is None for entry in summary))
        self.assertTrue(all(entry["json_ir"] is None for entry in summary))
        self.assertTrue(all(entry["trace"] is None for entry in summary))
        self.assertTrue(all(entry["markdown"] is None for entry in summary))
        self.assertTrue(all(entry["manifest"] is None for entry in summary))

    def test_expanded_view_shows_scalar_utf8_mapping(self) -> None:
        listing = render_expanded(
            compile_file(EXAMPLES / "unicode-to-utf8-mapper.bc"),
        )
        self.assertIn(":utf8_out_char3 =", listing)
        self.assertNotIn("\n# instance ", listing)

    def test_cli_runs_example_input_file(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            output_path = Path(directory) / "counter.json"
            summary_path = Path(directory) / "counter.md"
            result = cli_main([
                "run",
                str(EXAMPLES / "counter.bc"),
                "--input-file",
                str(EXAMPLES / "counter.bc.in.json"),
                "--output",
                str(output_path),
                "--markdown-output",
                str(summary_path),
            ])
            self.assertEqual(result, 0)
            self.assertTrue(output_path.is_file())
            self.assertTrue(summary_path.is_file())
            frames = json.loads(output_path.read_text(encoding="utf-8"))
            self.assertEqual(len(frames), 6)
            self.assertEqual(frames[-1]["counter"], 5)
            report = summary_path.read_text(encoding="utf-8")
            self.assertIn("# BrainCode run: ", report)
            self.assertIn(":counter = :counter~1 + 1", report)
            self.assertIn('"counter": 5', report)

    def test_cli_writes_detailed_markdown_when_md_output_is_set(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "counter.bc"
            source_path.write_text(":counter = :counter~1 + 1\n", encoding="utf-8")
            config_path = Path(directory) / "counter.in.json"
            config_path.write_text(
                json.dumps({
                    "initial_state": {"counter": 2},
                    "parameters": {},
                    "ticks": 2,
                    "md_output": True,
                }),
                encoding="utf-8",
            )
            result = cli_main([
                "run",
                str(source_path),
                "--input-file",
                str(config_path),
            ])
            self.assertEqual(result, 0)
            report_path = Path(directory) / "output" / "counter.run.md"
            self.assertTrue(report_path.is_file())
            report = report_path.read_text(encoding="utf-8")
            self.assertIn('"counter": 2', report)
            self.assertIn(":counter = :counter~1 + 1", report)
            self.assertIn('"counter": 4', report)

    def test_failed_tick_does_not_commit_partial_frame(self) -> None:
        program = compile_source(":a = 10\n:b = :missing~1\n")
        runtime = Runtime(program, initial_state={"a": 1, "b": 2})
        with self.assertRaises(BrainCodeRuntimeError):
            runtime.step()
        self.assertEqual(runtime.tick, 0)
        self.assertEqual(runtime.frames, [{"a": 1, "b": 2}])

    def test_compiler_rejects_duplicate_rule_writers(self) -> None:
        with self.assertRaises(BrainCodeCompileError):
            compile_source(":value = 1\n:value = 2\n")

    def test_runtime_rejects_duplicate_parallel_element_writes(self) -> None:
        program = compile_source(
            "population :bits[2] of Bool\n"
            "each :i in :bits parallel:\n"
            "    :bits[0] = True\n"
        )
        runtime = Runtime(program)
        with self.assertRaisesRegex(BrainCodeRuntimeError, "conflicting writes"):
            runtime.step()
        self.assertEqual(runtime.tick, 0)

    def test_string_literals_are_not_rewritten_as_signals(self) -> None:
        program = compile_source(':label = "literal :not_a_signal"\n')
        result = Runtime(program).run(1)[-1]
        self.assertEqual(result["label"], "literal :not_a_signal")


if __name__ == "__main__":
    unittest.main()
