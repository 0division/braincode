from __future__ import annotations

import json
from pathlib import Path

import pytest

from braincode.compiler import compile_source
from braincode.cli import main as cli_main
from braincode.runtime import BrainCodeRuntimeError, Runtime


@pytest.mark.parametrize("dimension", ["-1", "2.5", "True"])
def test_population_dimensions_must_be_non_negative_integers(
    dimension: str,
) -> None:
    program = compile_source(f"population :cells[{dimension}] of Bool\n")

    with pytest.raises(BrainCodeRuntimeError, match="dimension"):
        Runtime(program)


@pytest.mark.parametrize("index", ["-1", "2", "0.5", "True"])
def test_indexed_writes_require_in_bounds_integer_indices(index: str) -> None:
    program = compile_source(
        "population :cells[2] of Bool\n"
        f":cells[{index}] = True\n"
    )
    runtime = Runtime(program, initial_state={"cells": [False, False]})

    with pytest.raises(BrainCodeRuntimeError, match="index"):
        runtime.step()

    assert runtime.tick == 0
    assert runtime.frames == [{"cells": [False, False]}]


def test_indexed_reads_require_integer_indices() -> None:
    program = compile_source(
        "population :cells[2] of Bool\n"
        ":selected = :cells[0.5]~1\n"
    )
    runtime = Runtime(program, initial_state={"cells": [False, True]})

    with pytest.raises(BrainCodeRuntimeError, match="index"):
        runtime.step()

    assert runtime.tick == 0


def test_indexed_write_cannot_change_population_shape() -> None:
    program = compile_source(
        "population :cells[2] of Bool\n"
        ":cells[0] = [True, False]\n"
    )
    runtime = Runtime(program, initial_state={"cells": [False, False]})

    with pytest.raises(BrainCodeRuntimeError, match="shape"):
        runtime.step()

    assert runtime.frames == [{"cells": [False, False]}]


def test_tick_input_cannot_change_declared_population_shape() -> None:
    program = compile_source(
        "population :cells[2] of Bool\n"
        ":count = 1\n"
    )
    runtime = Runtime(program, initial_state={"cells": [False, False]})

    with pytest.raises(BrainCodeRuntimeError, match="shape"):
        runtime.step({"cells": [True]})

    assert runtime.tick == 0
    assert runtime.frames == [{"cells": [False, False]}]


def test_population_values_must_be_rectangular() -> None:
    program = compile_source("tensor :grid[2, 2] of Float32\n")

    with pytest.raises(BrainCodeRuntimeError, match="rectangular"):
        Runtime(program, initial_state={"grid": [[0.0, 1.0], [2.0]]})


@pytest.mark.parametrize("ticks", [True, 1.5, "2"])
def test_run_ticks_must_be_an_integer(ticks: object) -> None:
    runtime = Runtime(compile_source(":value = 1\n"))

    with pytest.raises(ValueError, match="ticks must be an integer"):
        runtime.run(ticks)  # type: ignore[arg-type]


def test_run_rejects_unused_tick_input_frames() -> None:
    runtime = Runtime(compile_source(":value = :input~1\n"))

    with pytest.raises(ValueError, match="at most 2 are valid"):
        runtime.run(1, input_frames=[{}, {}, {}])

    assert runtime.frames == [{}]


def test_run_rejects_non_object_tick_inputs() -> None:
    runtime = Runtime(compile_source(":value = 1\n"))

    with pytest.raises(ValueError, match="each input frame must be a mapping"):
        runtime.run(1, input_frames=[[]])  # type: ignore[list-item]


def test_invalid_initial_tick_input_does_not_mutate_state() -> None:
    runtime = Runtime(
        compile_source("population :cells[2] of Bool\n"),
        initial_state={"cells": [False, False]},
    )

    with pytest.raises(BrainCodeRuntimeError, match="shape"):
        runtime.run(0, input_frames=[{"cells": [True]}])

    assert runtime.frames == [{"cells": [False, False]}]


def test_runtime_rejects_non_mapping_initial_state() -> None:
    with pytest.raises(BrainCodeRuntimeError, match="initial_state must be a mapping"):
        Runtime(compile_source(":value = 1\n"), initial_state=[("value", 0)])  # type: ignore[arg-type]


def test_neighbor_count_rejects_negative_radius() -> None:
    program = compile_source(
        "population :cells[3] of Bool\n"
        ':neighbors = neighbor_count(:cells~1, 1, radius=-1)\n'
    )
    runtime = Runtime(program, initial_state={"cells": [False, True, False]})

    with pytest.raises(BrainCodeRuntimeError, match="radius must be non-negative"):
        runtime.step()

    assert runtime.tick == 0


def test_valid_indexed_writes_preserve_shape_and_commit() -> None:
    program = compile_source(
        "population :cells[2] of Bool\n"
        "each :i in :cells parallel:\n"
        "    :cells[:i] = not :cells[:i]~1\n"
    )
    runtime = Runtime(program, initial_state={"cells": [False, True]})

    result = runtime.step()

    assert result["cells"] == [True, False]
    assert runtime.tick == 1


def test_valid_tick_inputs_are_aligned_to_committed_frames() -> None:
    program = compile_source(":seen = :input~1\n")
    runtime = Runtime(program, initial_state={"input": 0})

    frames = runtime.run(
        2,
        input_frames=[{"input": 1}, {"input": 2}, {"input": 3}],
    )

    assert frames == [
        {"input": 1},
        {"input": 2, "seen": 1},
        {"input": 3, "seen": 2},
    ]


def test_cli_input_file_rejects_non_integer_ticks(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "counter.bc"
    source.write_text(":counter = :counter~1 + 1\n", encoding="utf-8")
    config = tmp_path / "counter.bc.in.json"
    config.write_text(
        json.dumps({"initial_state": {"counter": 0}, "ticks": 1.5}),
        encoding="utf-8",
    )

    result = cli_main(["run", str(source), "--input-file", str(config)])

    assert result == 1
    assert "ticks must be an integer" in capsys.readouterr().err


def test_cli_options_override_input_file_values(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "counter.bc"
    source.write_text(":counter = :counter~1 + 1\n", encoding="utf-8")
    config = tmp_path / "counter.bc.in.json"
    config.write_text(
        json.dumps({"initial_state": {"counter": 0}, "ticks": 1}),
        encoding="utf-8",
    )
    output = tmp_path / "trace.json"

    result = cli_main([
        "run",
        str(source),
        "--input-file",
        str(config),
        "--ticks",
        "2",
        "--output",
        str(output),
    ])

    assert result == 0
    assert capsys.readouterr().err == ""
    frames = json.loads(output.read_text(encoding="utf-8"))
    assert len(frames) == 3
    assert frames[-1]["counter"] == 2
