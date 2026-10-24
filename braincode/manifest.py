"""Versioned, self-contained run manifests and deterministic replay."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any

from braincode.compiler import (
    IR_VERSION,
    LANGUAGE_VERSION,
    CompiledProgram,
    compile_source,
)
from braincode.runtime import Runtime


RUN_MANIFEST_VERSION = 1
RUNTIME_VERSION = "0.2.0"


def save_run_manifest(
    path: str | Path,
    program: CompiledProgram,
    *,
    initial_state: Mapping[str, Any] | None = None,
    parameters: Mapping[str, Any] | None = None,
    initial_history: Sequence[Mapping[str, Any]] | None = None,
    input_frames: Sequence[Mapping[str, Any]] | None = None,
    ticks: int,
    runtime_options: Mapping[str, Any] | None = None,
    frames: Sequence[Mapping[str, Any]] | None = None,
    backend: str = "python-serial",
    input_adapter_names: Sequence[str] = (),
    function_names: Sequence[str] = (),
) -> None:
    if isinstance(ticks, bool) or not isinstance(ticks, int) or ticks < 0:
        raise ValueError("ticks must be a non-negative integer")
    if backend != "python-serial":
        raise ValueError(f"unsupported manifest backend {backend!r}")
    source = program.program.source
    if not source:
        raise ValueError("cannot create a replay manifest without BrainCode source")
    source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    manifest = {
        "format": "braincode-run",
        "manifest_version": RUN_MANIFEST_VERSION,
        "runtime_version": RUNTIME_VERSION,
        "language_version": LANGUAGE_VERSION,
        "ir_version": IR_VERSION,
        "backend": backend,
        "source_name": Path(program.source_name).name,
        "source": source,
        "source_sha256": source_hash,
        "initial_state": (
            dict(initial_state) if initial_state is not None else None
        ),
        "parameters": dict(parameters or {}),
        "initial_history": [dict(frame) for frame in (initial_history or [])],
        "input_frames": [dict(frame) for frame in (input_frames or [])],
        "ticks": ticks,
        "runtime_options": dict(runtime_options or {}),
        "input_adapters": list(input_adapter_names),
        "host_functions": list(function_names),
        "frames": [dict(frame) for frame in frames] if frames is not None else None,
    }
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def load_run_manifest(path: str | Path) -> dict[str, Any]:
    manifest = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(manifest, dict):
        raise ValueError("run manifest must contain a JSON object")
    if manifest.get("format") != "braincode-run":
        raise ValueError("not a BrainCode run manifest")
    if manifest.get("manifest_version") != RUN_MANIFEST_VERSION:
        raise ValueError(
            f"unsupported run manifest version {manifest.get('manifest_version')!r}; "
            f"this runtime supports {RUN_MANIFEST_VERSION}"
        )
    source = manifest.get("source")
    if not isinstance(source, str):
        raise ValueError("run manifest is missing BrainCode source")
    expected_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
    if manifest.get("source_sha256") != expected_hash:
        raise ValueError("run manifest source hash does not match its source")
    if manifest.get("language_version") != LANGUAGE_VERSION:
        raise ValueError(
            f"run manifest uses language version "
            f"{manifest.get('language_version')!r}; this runtime supports "
            f"{LANGUAGE_VERSION!r}"
        )
    if manifest.get("runtime_version") != RUNTIME_VERSION:
        raise ValueError(
            f"run manifest uses runtime version "
            f"{manifest.get('runtime_version')!r}; this runtime supports "
            f"{RUNTIME_VERSION!r}"
        )
    if manifest.get("ir_version") != IR_VERSION:
        raise ValueError(
            f"run manifest uses IR version {manifest.get('ir_version')!r}; "
            f"this runtime supports {IR_VERSION}"
        )
    if manifest.get("backend") != "python-serial":
        raise ValueError(
            f"cannot replay backend {manifest.get('backend')!r}; "
            "this runtime supports 'python-serial'"
        )
    _validate_manifest_shape(manifest)
    return manifest


def _validate_manifest_shape(manifest: Mapping[str, Any]) -> None:
    if not isinstance(manifest.get("initial_state"), (dict, type(None))):
        raise ValueError("run manifest initial_state must be an object or null")
    for field in ("parameters", "runtime_options"):
        if not isinstance(manifest.get(field), dict):
            raise ValueError(f"run manifest {field} must be an object")
    for field in ("initial_history", "input_frames"):
        value = manifest.get(field)
        if not isinstance(value, list) or any(not isinstance(frame, dict) for frame in value):
            raise ValueError(f"run manifest {field} must be an array of objects")
    ticks = manifest.get("ticks")
    if isinstance(ticks, bool) or not isinstance(ticks, int) or ticks < 0:
        raise ValueError("run manifest ticks must be a non-negative integer")
    for field in ("input_adapters", "host_functions"):
        value = manifest.get(field)
        if not isinstance(value, list) or any(not isinstance(name, str) for name in value):
            raise ValueError(f"run manifest {field} must be an array of names")
    frames = manifest.get("frames")
    if frames is not None and (
        not isinstance(frames, list) or any(not isinstance(frame, dict) for frame in frames)
    ):
        raise ValueError("run manifest frames must be an array of objects or null")


def replay_run_manifest(
    path: str | Path,
    *,
    input_adapters: Mapping[str, Callable[[Any], Any]] | None = None,
    functions: Mapping[str, Callable[..., Any]] | None = None,
) -> list[dict[str, Any]]:
    manifest = load_run_manifest(path)
    missing_adapters = set(manifest["input_adapters"]) - set(input_adapters or {})
    if missing_adapters:
        raise ValueError(
            f"replay requires input adapter(s): {sorted(missing_adapters)}"
        )
    missing_functions = set(manifest["host_functions"]) - set(functions or {})
    if missing_functions:
        raise ValueError(
            f"replay requires host function(s): {sorted(missing_functions)}"
        )
    program = compile_source(
        manifest["source"],
        manifest.get("source_name", "<manifest>"),
    )
    runtime = Runtime(
        program,
        initial_state=manifest["initial_state"],
        parameters=manifest["parameters"],
        initial_history=manifest["initial_history"],
        functions=functions,
        **manifest.get("runtime_options", {}),
    )
    for name, adapter in (input_adapters or {}).items():
        runtime.register_input_adapter(name, adapter)
    frames = runtime.run(
        manifest["ticks"],
        input_frames=manifest["input_frames"],
    )
    expected_frames = manifest.get("frames")
    if expected_frames is not None and frames != expected_frames:
        raise ValueError("replayed frames do not match the recorded run output")
    return frames
