"""Command-line interface for compiling, inspecting, and running BrainCode."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from braincode.compiler import CompiledProgram, compile_file, load_compiled
from braincode.expanded import render_expanded
from braincode.reporting import write_run_markdown
from braincode.runtime import BrainCodeRuntimeError, Runtime


def _read_json(path: str | None, default: Any) -> Any:
    if path is None:
        return default
    candidate = Path(path)
    text = candidate.read_text(encoding="utf-8") if candidate.is_file() else path
    return json.loads(text)


def _load_program(path: str) -> CompiledProgram:
    if path.lower().endswith((".bcc", ".bcc.json")):
        return load_compiled(path)
    return compile_file(path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="braincode")
    commands = parser.add_subparsers(dest="command", required=True)

    compile_command = commands.add_parser(
        "compile", help="compile .bc source to expanded .bcc and structured .bcc.json"
    )
    compile_command.add_argument("source")
    compile_command.add_argument(
        "-o", "--output",
        help="write expanded BrainCode output to this path; omitted by default",
    )
    compile_command.add_argument(
        "--json-output",
        help="write JSON IR output to this path; omitted by default",
    )
    compile_command.add_argument(
        "--parameters", help="JSON object or file used to resolve population dimensions"
    )

    show_command = commands.add_parser("show", help="inspect compiled BrainCode")
    show_command.add_argument("source", help=".bc or .bcc file")
    show_command.add_argument("--expanded", action="store_true")
    show_command.add_argument("--parameters", help="JSON file with compile parameters")

    run_command = commands.add_parser("run", help="run a BrainCode model")
    run_command.add_argument("source", help=".bc or .bcc file")
    run_command.add_argument(
        "--input-file",
        help="JSON run configuration, conventionally named source.bc.in.json",
    )
    run_command.add_argument("--ticks", type=int)
    run_command.add_argument("--initial-state", help="JSON object for tick zero")
    run_command.add_argument("--parameters", help="JSON object with model parameters")
    run_command.add_argument("--inputs", help="JSON array of tick-indexed input objects")
    run_command.add_argument(
        "--initial-history",
        help="JSON array of prior state frames, oldest first",
    )
    run_command.add_argument(
        "-o", "--output",
        help="write frames to this JSON file; omitted by default",
    )
    run_command.add_argument(
        "--markdown-output",
        help="write a Markdown summary to this file; omitted by default",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "compile":
            source_path = Path(arguments.source)
            output_path = Path(arguments.output) if arguments.output else None
            json_path = Path(arguments.json_output) if arguments.json_output else None
            program = compile_file(source_path)
            parameters = _read_json(arguments.parameters, {})
            expanded = render_expanded(program, parameters=parameters)
            if output_path is not None:
                output_path.write_text(expanded, encoding="utf-8")
                print(output_path)
            else:
                sys.stdout.write(expanded)
            if json_path is not None:
                json_path.write_text(program.to_json(), encoding="utf-8")
                print(json_path)
            return 0

        program = _load_program(arguments.source)
        if arguments.command == "show":
            if arguments.expanded:
                parameters = _read_json(arguments.parameters, {})
                sys.stdout.write(render_expanded(program, parameters=parameters))
            else:
                sys.stdout.write(program.to_json())
            return 0

        run_config = _read_json(arguments.input_file, {})
        if not isinstance(run_config, dict):
            raise ValueError("--input-file must contain a JSON object")
        unknown_config_keys = set(run_config) - {
            "initial_state",
            "parameters",
            "initial_history",
            "inputs",
            "ticks",
            "md_output",
        }
        if unknown_config_keys:
            raise ValueError(
                f"--input-file contains unsupported keys: "
                f"{sorted(unknown_config_keys)}"
            )
        initial_state = (
            _read_json(arguments.initial_state, run_config.get("initial_state", {}))
        )
        parameters = _read_json(arguments.parameters, run_config.get("parameters", {}))
        inputs = _read_json(arguments.inputs, run_config.get("inputs", []))
        initial_history = _read_json(
            arguments.initial_history,
            run_config.get("initial_history", []),
        )
        ticks = (
            arguments.ticks
            if arguments.ticks is not None
            else run_config.get("ticks", 1)
        )
        if not isinstance(initial_state, dict):
            raise ValueError("initial_state must be a JSON object")
        if not isinstance(parameters, dict):
            raise ValueError("parameters must be a JSON object")
        if not isinstance(inputs, list):
            raise ValueError("inputs must be a JSON array of objects")
        if not isinstance(initial_history, list):
            raise ValueError("initial_history must be a JSON array of objects")
        if any(not isinstance(frame, dict) for frame in inputs):
            raise ValueError("each item in inputs must be a JSON object")
        if any(not isinstance(frame, dict) for frame in initial_history):
            raise ValueError("each item in initial_history must be a JSON object")
        if isinstance(ticks, bool) or not isinstance(ticks, int):
            raise ValueError("ticks must be an integer")
        md_output = run_config.get("md_output", False)
        if not isinstance(md_output, (bool, str)):
            raise ValueError("md_output must be a boolean or output path")
        if isinstance(md_output, str) and not md_output:
            raise ValueError("md_output path must not be empty")
        runtime = Runtime(
            program,
            initial_state=initial_state,
            parameters=parameters,
            initial_history=initial_history,
        )
        frames = runtime.run(ticks, input_frames=inputs)
        result = json.dumps(frames, indent=2, sort_keys=True) + "\n"
        if arguments.output:
            Path(arguments.output).write_text(result, encoding="utf-8")
        markdown_output = arguments.markdown_output
        if markdown_output is None and md_output:
            markdown_output = (
                md_output if isinstance(md_output, str) else
                str(Path(arguments.source).parent / "output" /
                    f"{Path(arguments.source).stem}.run.md")
            )
        if markdown_output:
            source_path = Path(arguments.source)
            write_run_markdown(
                markdown_output,
                source_name=str(Path(arguments.source)),
                source_code=source_path.read_text(encoding="utf-8"),
                initial_state=initial_state,
                parameters=parameters,
                initial_history=initial_history,
                inputs=inputs,
                frames=frames,
                ticks=ticks,
            )
        if not arguments.output and not markdown_output:
            sys.stdout.write(result)
        return 0
    except (OSError, ValueError, TypeError, BrainCodeRuntimeError) as error:
        print(f"braincode: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
