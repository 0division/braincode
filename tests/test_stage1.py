from __future__ import annotations

import json

import pytest

from braincode.backend import PythonSerialBackend, RuntimeSession
from braincode.benchmark import run_baseline
from braincode.cli import main as cli_main
from braincode.compiler import BrainCodeCompileError, compile_source
from braincode.manifest import replay_run_manifest, save_run_manifest
from braincode.runtime import BrainCodeAdapterError, BrainCodeRuntimeError, Runtime


def test_typed_state_and_population_enforce_declared_values() -> None:
    program = compile_source(
        "state :count of Int32\n"
        ":count = :count~1 + 1\n"
    )
    runtime = Runtime(program, initial_state={"count": 2**31 - 1})

    with pytest.raises(BrainCodeRuntimeError, match="Int32 range"):
        runtime.step()

    assert runtime.frames == [{"count": 2**31 - 1}]


def test_declarations_require_supported_types_and_initial_state() -> None:
    with pytest.raises(BrainCodeCompileError, match="unsupported declared value type"):
        compile_source("state :count of BigInt\n")
    with pytest.raises(BrainCodeCompileError, match="needs at least one dimension"):
        compile_source("population :cells of Bool\n")
    with pytest.raises(BrainCodeRuntimeError, match="missing from initial_state"):
        Runtime(compile_source("state :count of Int64\n"))
    with pytest.raises(BrainCodeRuntimeError, match="missing from the state frame"):
        Runtime(
            compile_source("state :count of Int64\n"),
            initial_state={"count": 2},
            initial_history=[{}],
        )


def test_explicit_state_input_mode_rejects_undeclared_signals() -> None:
    with pytest.raises(
        BrainCodeCompileError,
        match="undeclared signal :sensor; declare it as state or input",
    ):
        compile_source(
            "state :count of Int32\n"
            ":count = :sensor~1\n"
        )
    compile_source(
        "input :sensor of Int32\n"
        "state :count of Int32\n"
        ":count = :sensor~1\n"
    )


def test_runtime_errors_include_source_line_and_column() -> None:
    runtime = Runtime(
        compile_source(":value = :missing~1\n", "missing-value.bc")
    )

    with pytest.raises(
        BrainCodeRuntimeError,
        match=r"missing-value\.bc:1:1:.*undefined state signal",
    ):
        runtime.step()


def test_whole_population_assignment_cannot_change_declared_shape() -> None:
    runtime = Runtime(
        compile_source(
            "population :cells[2] of Bool\n"
            ":cells = [True]\n"
        ),
        initial_state={"cells": [False, False]},
    )

    with pytest.raises(BrainCodeRuntimeError, match="declared \\(2,\\)"):
        runtime.step()

    assert runtime.frames == [{"cells": [False, False]}]


def test_float32_values_are_rounded_to_ieee_binary32() -> None:
    program = compile_source(
        "state :value of Float32\n"
        ":value = 16777217.0\n"
    )
    frames = Runtime(program, initial_state={"value": 0.0}).run(1)

    assert frames[-1]["value"] == 16777216.0


def test_input_declarations_are_typed_and_read_only() -> None:
    with pytest.raises(BrainCodeCompileError, match="read-only"):
        compile_source(
            "input :sensor of Int32\n"
            ":sensor = 1\n"
        )
    with pytest.raises(BrainCodeRuntimeError, match="requires Int32"):
        Runtime(
            compile_source("input :sensor of Int32\n"),
            initial_state={"sensor": True},
        )
    with pytest.raises(BrainCodeRuntimeError, match="undeclared signal"):
        Runtime(
            compile_source("input :sensor of Int32\n"),
            initial_state={"other": 1},
        )
    with pytest.raises(BrainCodeRuntimeError, match="undeclared input"):
        Runtime(
            compile_source("input :sensor of Int32\n"),
        ).run(1, input_frames=[{"other": 1}])


def test_python_serial_backend_implements_runtime_session() -> None:
    runtime = PythonSerialBackend().create_runtime(
        compile_source(":value = :value~1 + 1\n"),
        initial_state={"value": 0},
    )

    assert isinstance(runtime, RuntimeSession)
    assert runtime.run(1)[-1]["value"] == 1


def test_input_adapter_precedes_evaluation_and_output_adapter_follows_commit() -> None:
    program = compile_source(
        "input :sensor of Int32\n"
        "state :doubled of Int32\n"
        ":doubled = :sensor~1 * 2\n"
    )
    observed: list[tuple[int, dict[str, object]]] = []
    runtime = Runtime(program, initial_state={"doubled": 0})
    runtime.register_input_adapter("sensor", lambda raw: raw + 1)
    runtime.register_output_adapter(
        "observer",
        lambda tick, frame: observed.append((tick, dict(frame))),
    )

    frames = runtime.run(
        2,
        input_frames=[{"sensor": 0}, {"sensor": 2}, {"sensor": 3}],
    )

    assert frames[-1] == {"doubled": 6, "sensor": 4}
    assert observed == [
        (1, {"doubled": 2, "sensor": 3}),
        (2, {"doubled": 6, "sensor": 4}),
    ]
    assert runtime.input_log == [
        {"sensor": 1},
        {"sensor": 3},
        {"sensor": 4},
    ]


def test_adapters_execute_in_registration_order() -> None:
    program = compile_source(
        "input :sensor of Int32\n"
        "input :ambient of Int32\n"
        "state :count of Int32\n"
        ":count = :count~1 + 1\n"
    )
    events: list[str] = []
    runtime = Runtime(program, initial_state={"count": 0})
    runtime.register_input_adapter(
        "ambient", lambda value: events.append("input-ambient") or value
    )
    runtime.register_input_adapter(
        "sensor", lambda value: events.append("input-sensor") or value
    )
    runtime.register_output_adapter(
        "sink-first", lambda _tick, _frame: events.append("output-first")
    )
    runtime.register_output_adapter(
        "sink-second", lambda _tick, _frame: events.append("output-second")
    )

    runtime.run(0, input_frames=[{"sensor": 1, "ambient": 2}])
    runtime.step()

    assert events == [
        "input-ambient",
        "input-sensor",
        "output-first",
        "output-second",
    ]


def test_adapter_failures_preserve_documented_commit_boundary() -> None:
    program = compile_source(
        "input :sensor of Int32\n"
        "state :value of Int32\n"
        ":value = :value~1 + 1\n"
    )
    before_commit = Runtime(program, initial_state={"value": 0})
    before_commit.register_input_adapter(
        "sensor", lambda _value: (_ for _ in ()).throw(ValueError("bad input"))
    )
    with pytest.raises(BrainCodeAdapterError, match="bad input"):
        before_commit.step({"sensor": 1})
    assert before_commit.frames == [{"value": 0}]

    after_commit = Runtime(program, initial_state={"value": 0})
    after_commit.register_output_adapter(
        "sink", lambda _tick, _frame: (_ for _ in ()).throw(OSError("sink down"))
    )
    with pytest.raises(BrainCodeAdapterError, match="committed.*sink down"):
        after_commit.step()
    assert after_commit.frames == [{"value": 0}, {"value": 1}]


def test_history_window_and_budgets_are_enforced_without_partial_ticks() -> None:
    program = compile_source(":value = :value~2 + 1\n")
    with pytest.raises(ValueError, match="maximum history delay"):
        Runtime(program, initial_state={"value": 0}, history_window=1)

    runtime = Runtime(
        compile_source(":value = :value~1 + 1\n"),
        initial_state={"value": 0},
        history_window=1,
        max_ticks=1,
        max_frame_bytes=64,
    )
    with pytest.raises(BrainCodeRuntimeError, match="requests 2 ticks"):
        runtime.run(2, input_frames=[{"value": 10}])
    assert runtime.frames == [{"value": 0}]
    assert runtime.run(1) == [{"value": 1}]

    with pytest.raises(BrainCodeRuntimeError, match="configured limit is 1"):
        Runtime(
            compile_source("population :cells[2] of Bool\n"),
            max_population_elements=1,
        )
    with pytest.raises(BrainCodeRuntimeError, match="frame is .* bytes"):
        Runtime(
            compile_source(":value = 1\n"),
            initial_state={"value": 0},
            max_frame_bytes=1,
        )


def test_history_window_retains_every_frame_required_by_delays() -> None:
    runtime = Runtime(
        compile_source(":value = :value~2 + 1\n"),
        initial_history=[{"value": 1}, {"value": 2}],
        history_window=2,
    )

    frames = runtime.run(2)

    assert frames == [{"value": 2}, {"value": 3}]
    assert runtime.tick == 3
    quoted_delay = Runtime(
        compile_source(':label = "text~99"\n'),
        history_window=1,
    )
    assert quoted_delay.run(1)[-1]["label"] == "text~99"


def test_run_manifest_replays_source_inputs_adapters_and_outputs(tmp_path) -> None:
    program = compile_source(
        "input :sensor of Int32\n"
        "state :doubled of Int32\n"
        ":doubled = :sensor~1 * 2\n",
        "sensor-model.bc",
    )
    initial_state = {"doubled": 0}
    input_frames = [{"sensor": 0}, {"sensor": 2}, {"sensor": 3}]
    adapter = lambda value: value + 1
    runtime = Runtime(program, initial_state=initial_state, history_window=1)
    runtime.register_input_adapter("sensor", adapter)
    frames = runtime.run(2, input_frames=input_frames)
    path = tmp_path / "nested" / "run.json"

    save_run_manifest(
        path,
        program,
        initial_state=initial_state,
        input_frames=input_frames,
        ticks=2,
        runtime_options={"history_window": 1},
        input_adapter_names=["sensor"],
        frames=frames,
    )

    manifest = json.loads(path.read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 1
    assert replay_run_manifest(path, input_adapters={"sensor": adapter}) == frames
    with pytest.raises(ValueError, match="requires input adapter"):
        replay_run_manifest(path)
    manifest["frames"][0]["doubled"] = 100
    path.write_text(json.dumps(manifest), encoding="utf-8")
    with pytest.raises(ValueError, match="do not match"):
        replay_run_manifest(path, input_adapters={"sensor": adapter})


def test_serial_benchmark_reports_reproducible_correctness_and_memory() -> None:
    first = run_baseline(sizes=(4,), ticks=2, repeats=2)
    second = run_baseline(sizes=(4,), ticks=2, repeats=1)

    assert first["backend"] == "python-serial"
    assert first["results"][0]["final_frame_sha256"] == (
        second["results"][0]["final_frame_sha256"]
    )
    assert first["results"][0]["peak_traced_bytes"] > 0


def test_cli_writes_and_replays_run_manifests(tmp_path) -> None:
    source = tmp_path / "counter.bc"
    config = tmp_path / "counter.in.json"
    manifest = tmp_path / "counter.run.json"
    trace = tmp_path / "replay.json"
    source.write_text(":value = :value~1 + 1\n", encoding="utf-8")
    config.write_text(
        json.dumps({
            "initial_state": {"value": 0},
            "ticks": 2,
            "manifest_output": str(manifest),
        }),
        encoding="utf-8",
    )

    assert cli_main(["run", str(source), "--input-file", str(config)]) == 0
    assert cli_main(["replay", str(manifest), "--output", str(trace)]) == 0
    assert json.loads(trace.read_text(encoding="utf-8")) == [
        {"value": 0},
        {"value": 1},
        {"value": 2},
    ]
