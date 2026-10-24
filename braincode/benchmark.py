"""Deterministic small-scale baseline for the serial Python reference runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
import tracemalloc
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from braincode.compiler import compile_source
from braincode.runtime import Runtime


_PROGRAMS = {
    "1d-state-update": compile_source(
        "population :values[N] of Float64\n"
        "each :i in :values parallel:\n"
        "    :values[:i] = :values[:i]~1 + 1.0\n",
        "<serial-1d-baseline>",
    ),
    "2d-stencil": compile_source(
        "population :cells[N, N] of Bool\n"
        "boundary :cells = wrap\n"
        "each (:x, :y) in :cells parallel:\n"
        "    let neighbors = neighbor_count(\n"
        "        :cells~1, :x, :y, neighborhood=moore_2d, boundary=wrap\n"
        "    )\n"
        "    let alive = :cells[:x, :y]~1\n"
        "    :cells[:x, :y] = True if neighbors == 3 else (alive and neighbors == 2)\n",
        "<serial-2d-baseline>",
    ),
}


def run_baseline(
    *,
    sizes: tuple[int, ...] = (8, 16),
    ticks: int = 3,
    repeats: int = 1,
) -> dict[str, Any]:
    if any(isinstance(size, bool) or not isinstance(size, int) or size < 1
           for size in sizes):
        raise ValueError("sizes must contain positive integers")
    if isinstance(ticks, bool) or not isinstance(ticks, int) or ticks < 1:
        raise ValueError("ticks must be a positive integer")
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be a positive integer")

    results: list[dict[str, Any]] = []
    for workload_name, program in _PROGRAMS.items():
        for size in sizes:
            elapsed: list[float] = []
            peak_bytes = 0
            final_hash = ""
            for _ in range(repeats):
                if workload_name == "1d-state-update":
                    initial_state = {"values": [0.0] * size}
                    population_elements = size
                else:
                    initial_state = {
                        "cells": [
                            [((row * 3 + column * 7) % 11 == 0)
                             for column in range(size)]
                            for row in range(size)
                        ]
                    }
                    population_elements = size * size
                runtime = Runtime(
                    program,
                    initial_state=initial_state,
                    parameters={"N": size},
                )
                tracemalloc.start()
                started = time.perf_counter()
                frames = runtime.run(ticks)
                elapsed.append(time.perf_counter() - started)
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                peak_bytes = max(peak_bytes, peak)
                run_hash = hashlib.sha256(
                    json.dumps(frames[-1], sort_keys=True, separators=(",", ":"))
                    .encode("utf-8")
                ).hexdigest()
                if final_hash and run_hash != final_hash:
                    raise RuntimeError(
                        "serial reference output changed between identical "
                        "benchmark runs"
                    )
                final_hash = run_hash
            results.append({
                "workload": workload_name,
                "program_sha256": hashlib.sha256(
                    program.program.source.encode("utf-8")
                ).hexdigest(),
                "size": size,
                "population_elements": population_elements,
                "ticks": ticks,
                "repeats": repeats,
                "median_seconds": statistics.median(elapsed),
                "peak_traced_bytes": peak_bytes,
                "final_frame_sha256": final_hash,
            })
    return {
        "format": "braincode-serial-baseline",
        "backend": "python-serial",
        "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure deterministic small-scale serial BrainCode baselines."
    )
    parser.add_argument("--sizes", type=int, nargs="+", default=[8, 16])
    parser.add_argument("--ticks", type=int, default=3)
    parser.add_argument("--repeats", type=int, default=1)
    parser.add_argument("--output", help="write benchmark JSON to this file")
    arguments = parser.parse_args(argv)
    result = json.dumps(
        run_baseline(
            sizes=tuple(arguments.sizes),
            ticks=arguments.ticks,
            repeats=arguments.repeats,
        ),
        indent=2,
        sort_keys=True,
    ) + "\n"
    if arguments.output:
        output_path = Path(arguments.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result, encoding="utf-8")
    else:
        print(result, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
