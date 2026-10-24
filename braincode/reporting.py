"""Markdown artifacts for BrainCode runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_run_markdown(
    path: str | Path,
    *,
    source_name: str,
    source_code: str,
    initial_state: dict[str, Any],
    parameters: dict[str, Any],
    initial_history: list[dict[str, Any]],
    inputs: list[dict[str, Any]],
    ticks: int,
    frames: list[dict[str, Any]],
) -> None:
    run_data = {
        "initial_state": initial_state,
        "parameters": parameters,
        "initial_history": initial_history,
        "inputs": inputs,
        "ticks": ticks,
    }
    content = [
        f"# BrainCode run: {source_name}",
        "",
        "## Input data",
        "",
        "```json",
        json.dumps(run_data, indent=2, sort_keys=True),
        "```",
        "",
        "## BrainCode source",
        "",
        "```braincode",
        source_code.rstrip(),
        "```",
        "",
        "## Output",
        "",
        "```json",
        json.dumps(frames, indent=2, sort_keys=True),
        "```",
        "",
    ]
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(content), encoding="utf-8")
