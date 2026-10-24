"""Deterministic small-scale baseline for the serial Python reference runtime."""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import statistics
import time
import tracemalloc
from typing import Any

from braincode.compiler import compile_source
from braincode.runtime import Runtime


_PROGRAM = compile_source(
    "population :values[N] of Float64\n"
    "each :i in :values parallel:\n"
    "    :values[:i] = :values[:i]~1 + 1.0\n",
    "<serial-baseline>",
)


def run_baseline(
    *,
    sizes: tuple[int, ...] = (64, 256, 1024),
    ticks: int = 10,
    repeats: int = 3,
) -> dict[str, Any]:
    if any(isinstance(size, bool) or not isinstance(size, int) or size < 1
           for size in sizes):
        raise ValueError("sizes must contain positive integers")
    if isinstance(ticks, bool) or not isinstance(ticks, int) or ticks < 1:
        raise ValueError("ticks must be a positive integer")
    if isinstance(repeats, bool) or not isinstance(repeats, int) or repeats < 1:
        raise ValueError("repeats must be a positive integer")

    results: list[dict[str, Any]] = []
    for size in sizes:
        elapsed: list[float] = []
        peak_bytes = 0
        final_hash = ""
        for _ in range(repeats):
            runtime = Runtime(
                _PROGRAM,
                initial_state={"values": [0.0] * size},
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
                    "serial reference output changed between identical benchmark runs"
                )
            final_hash = run_hash
        results.append({
            "population_elements": size,
            "ticks": ticks,
            "repeats": repeats,
            "median_seconds": statistics.median(elapsed),
            "peak_traced_bytes": peak_bytes,
            "final_frame_sha256": final_hash,
        })
    return {
        "format": "braincode-serial-baseline",
        "backend": "python-serial",
        "python_version": platform.python_version(),
        "platform": platform.platform(),
        "results": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Measure deterministic small-scale serial BrainCode baselines."
    )
    parser.add_argument("--sizes", type=int, nargs="+", default=[64, 256, 1024])
    parser.add_argument("--ticks", type=int, default=10)
    parser.add_argument("--repeats", type=int, default=3)
    arguments = parser.parse_args(argv)
    print(json.dumps(
        run_baseline(
            sizes=tuple(arguments.sizes),
            ticks=arguments.ticks,
            repeats=arguments.repeats,
        ),
        indent=2,
        sort_keys=True,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
