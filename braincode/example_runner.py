"""Run every checked-in BrainCode example with small, reproducible inputs."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from braincode.compiler import compile_file, load_compiled, save_compiled
from braincode.expanded import render_expanded
from braincode.runtime import Runtime


ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = ROOT / "docs" / "examples"


@dataclass(frozen=True)
class ExampleConfig:
    initial_state: dict[str, Any]
    parameters: dict[str, Any]
    initial_history: tuple[dict[str, Any], ...] = ()
    ticks: int = 1


def example_configs() -> dict[str, ExampleConfig]:
    configs: dict[str, ExampleConfig] = {}
    for input_path in sorted(EXAMPLES_DIR.glob("*.bc.in.json")):
        source_name = input_path.name.removesuffix(".in.json")
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError(f"{input_path.name} must contain a JSON object")
        configs[source_name] = ExampleConfig(
            initial_state=payload["initial_state"],
            parameters=payload["parameters"],
            initial_history=tuple(payload.get("initial_history", [])),
            ticks=payload.get("ticks", 1),
        )
    return configs


def run_all_examples(output_dir: str | Path) -> list[dict[str, Any]]:
    destination = Path(output_dir)
    destination.mkdir(parents=True, exist_ok=True)
    started_at = datetime.now(timezone.utc)
    started_text = started_at.isoformat(timespec="seconds")
    log_path = destination / "run.log"
    log_path.write_text(
        f"BrainCode example run started at {started_text}\n",
        encoding="utf-8",
    )
    source_files = sorted(EXAMPLES_DIR.glob("*.bc"))
    configs = example_configs()
    source_names = {path.name for path in source_files}
    if source_names != set(configs):
        missing = sorted(source_names - set(configs))
        stale = sorted(set(configs) - source_names)
        raise ValueError(
            f"example configuration mismatch; missing={missing}, stale={stale}"
        )

    summary: list[dict[str, Any]] = []
    succeeded = False
    try:
        for source_path in source_files:
            config = configs[source_path.name]
            stem = source_path.stem
            input_path = EXAMPLES_DIR / f"{source_path.name}.in.json"
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"RUNNING {source_path.name} using {input_path.name}\n")
            program = compile_file(source_path)
            expanded_path = destination / f"{stem}.bcc"
            ir_path = destination / f"{stem}.bcc.json"
            trace_path = destination / f"{stem}.output.json"

            expanded_path.write_text(
                render_expanded(program, parameters=config.parameters),
                encoding="utf-8",
            )
            save_compiled(program, ir_path)
            runtime = Runtime(
                program,
                initial_state=config.initial_state,
                parameters=config.parameters,
                initial_history=config.initial_history,
            )
            frames = runtime.run(config.ticks)
            for artifact_path in (expanded_path, ir_path):
                artifact_program = load_compiled(artifact_path)
                artifact_frames = Runtime(
                    artifact_program,
                    initial_state=config.initial_state,
                    parameters=config.parameters,
                    initial_history=config.initial_history,
                ).run(config.ticks)
                if artifact_frames != frames:
                    raise RuntimeError(
                        f"{artifact_path.name} produced a different trace from "
                        f"{source_path.name}"
                    )
            trace_path.write_text(
                json.dumps(frames, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            summary.append({
                "source": source_path.name,
                "input": input_path.name,
                "ticks": config.ticks,
                "frames": len(frames),
                "expanded_source": expanded_path.name,
                "json_ir": ir_path.name,
                "trace": trace_path.name,
            })
            with log_path.open("a", encoding="utf-8") as log:
                log.write(f"PASS {source_path.name}: {config.ticks} ticks\n")
            print(f"Ran {source_path.name} -> {trace_path.name}")

        summary_path = destination / "summary.json"
        summary_path.write_text(
            json.dumps({"example_count": len(summary), "examples": summary},
                       indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        completed_text = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with log_path.open("a", encoding="utf-8") as log:
            log.write(f"Completed {len(summary)} examples at {completed_text}\n")
        _write_markdown_summary(
            destination / "run-summary.md",
            started_text,
            completed_text,
            summary,
        )
        print(f"Completed {len(summary)} examples; summary: {summary_path}")
        succeeded = True
        return summary
    finally:
        if not succeeded:
            with log_path.open("a", encoding="utf-8") as log:
                log.write("Run did not complete successfully.\n")


def _write_markdown_summary(
    path: Path,
    started_at: str,
    completed_at: str,
    examples: list[dict[str, Any]],
) -> None:
    rows = [
        f"| `{item['source']}` | `{item['input']}` | {item['ticks']} | "
        f"`{item['trace']}` |"
        for item in examples
    ]
    content = [
        "# BrainCode Example Run",
        "",
        f"- Started: {started_at}",
        f"- Completed: {completed_at}",
        f"- Result: passed ({len(examples)} examples)",
        "",
        "| Example | Input | Ticks | Trace |",
        "|---|---|---:|---|",
        *rows,
        "",
        "See `run.log` for the chronological execution log and `summary.json` "
        "for machine-readable results.",
        "",
    ]
    path.write_text("\n".join(content), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Compile and run every BrainCode example at small dimensions."
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "output"),
        help="directory for expanded source, JSON IR, traces, and summary",
    )
    arguments = parser.parse_args(argv)
    run_all_examples(arguments.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
