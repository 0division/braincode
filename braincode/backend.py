"""Backend contract and the serial reference backend."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import Any, Protocol, runtime_checkable

from braincode.compiler import CompiledProgram
from braincode.runtime import Runtime


@runtime_checkable
class RuntimeSession(Protocol):
    tick: int
    frames: list[dict[str, Any]]

    def step(self, next_inputs: Mapping[str, Any] | None = None) -> dict[str, Any]: ...

    def run(
        self,
        ticks: int,
        *,
        input_frames: Sequence[Mapping[str, Any]] | None = None,
    ) -> list[dict[str, Any]]: ...


class ExecutionBackend(Protocol):
    """Factory boundary for runtimes that implement BrainCode semantics."""

    name: str
    capabilities: frozenset[str]

    def create_runtime(
        self,
        program: CompiledProgram,
        *,
        initial_state: Mapping[str, Any] | None = None,
        parameters: Mapping[str, Any] | None = None,
        functions: Mapping[str, Callable[..., Any]] | None = None,
        initial_history: Sequence[Mapping[str, Any]] | None = None,
        **options: Any,
    ) -> RuntimeSession: ...


class PythonSerialBackend:
    """The deterministic serial implementation; it does not execute in parallel."""

    name = "python-serial"
    capabilities = frozenset({
        "committed-history",
        "atomic-frame-commit",
        "deterministic-ordered-reductions",
        "serial-population-evaluation",
    })

    def create_runtime(
        self,
        program: CompiledProgram,
        *,
        initial_state: Mapping[str, Any] | None = None,
        parameters: Mapping[str, Any] | None = None,
        functions: Mapping[str, Callable[..., Any]] | None = None,
        initial_history: Sequence[Mapping[str, Any]] | None = None,
        **options: Any,
    ) -> Runtime:
        return Runtime(
            program,
            initial_state=initial_state,
            parameters=parameters,
            functions=functions,
            initial_history=initial_history,
            **options,
        )
