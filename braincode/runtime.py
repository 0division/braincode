"""Deterministic, serial reference runtime for BrainCode."""

from __future__ import annotations

import copy
import itertools
import math
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from braincode.compiler import CompiledProgram
from braincode.expressions import evaluate_expression
from braincode.model import Expression, Statement


class BrainCodeRuntimeError(RuntimeError):
    """A model could not be evaluated or committed."""


@dataclass(frozen=True)
class _ArrayView:
    name: str
    values: Any


def _zero_for_type(value_type: str | None) -> Any:
    if value_type == "Bool":
        return False
    return 0.0 if value_type in {"Float32", "Float64"} else 0


def _make_array(shape: tuple[int, ...], value: Any) -> Any:
    if not shape:
        return copy.deepcopy(value)
    return [_make_array(shape[1:], value) for _ in range(shape[0])]


def _nested_get(value: Any, indices: tuple[Any, ...]) -> Any:
    current = value
    for index in indices:
        current = current[index]
    return current


def _nested_set(value: Any, indices: tuple[Any, ...], new_value: Any) -> None:
    if not indices:
        raise BrainCodeRuntimeError("cannot index an empty target")
    current = value
    for index in indices[:-1]:
        current = current[index]
    current[indices[-1]] = new_value


def _deep_shape(value: Any) -> tuple[int, ...]:
    if not isinstance(value, list):
        return ()
    if not value:
        return (0,)
    child_shape = _deep_shape(value[0])
    if any(_deep_shape(item) != child_shape for item in value[1:]):
        raise BrainCodeRuntimeError("population values must be rectangular")
    return (len(value),) + child_shape


def _require_integer(value: Any, subject: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise BrainCodeRuntimeError(f"{subject} must be an integer")
    return value


def _life_rule(neighbor_count: int, was_alive: bool) -> bool:
    return neighbor_count == 3 or (was_alive and neighbor_count == 2)


def _vector_length(value: Any) -> float:
    return math.sqrt(sum(float(component) ** 2 for component in value))


def _relu(value: Any) -> Any:
    return max(0, value)


class Runtime:
    """Serial reference evaluator with atomic frame commits."""

    def __init__(
        self,
        program: CompiledProgram,
        *,
        initial_state: Mapping[str, Any] | None = None,
        parameters: Mapping[str, Any] | None = None,
        functions: Mapping[str, Callable[..., Any]] | None = None,
        initial_history: Sequence[Mapping[str, Any]] | None = None,
    ):
        if initial_state is not None and not isinstance(initial_state, Mapping):
            raise BrainCodeRuntimeError("initial_state must be a mapping")
        if parameters is not None and not isinstance(parameters, Mapping):
            raise BrainCodeRuntimeError("parameters must be a mapping")
        if initial_history is not None and (
            isinstance(initial_history, (str, bytes))
            or not isinstance(initial_history, Sequence)
        ):
            raise BrainCodeRuntimeError("initial_history must be a sequence of frames")
        if initial_history is not None and any(
            not isinstance(frame, Mapping) for frame in initial_history
        ):
            raise BrainCodeRuntimeError("each initial history frame must be a mapping")

        self.program = program
        self.parameters = dict(parameters or {})
        self.functions = {
            "life_rule": _life_rule,
            "length": _vector_length,
            "relu": _relu,
        }
        if functions:
            self.functions.update(functions)
        self.boundaries = {
            item.name: item.boundary
            for item in program.program.statements
            if item.kind == "boundary" and item.name is not None
        }
        self.population_shapes: dict[str, tuple[int, ...]] = {}
        history = [dict(frame) for frame in (initial_history or [])]
        if initial_state is not None:
            current = dict(initial_state)
        elif history:
            current = dict(history.pop())
        else:
            current = {}
        self._initialize_populations(current)
        history.append(current)
        self.frames: list[dict[str, Any]] = history
        self.tick = len(history) - 1

    def _symbols(self) -> dict[str, Any]:
        symbols = dict(self.parameters)
        symbols.update({
            "dead": "dead",
            "wrap": "wrap",
            "insulated": "insulated",
            "moore_2d": "moore_2d",
            "moore_3d": "moore_3d",
            "True": True,
            "False": False,
            "None": None,
        })
        return symbols

    def _initialize_populations(self, frame: dict[str, Any]) -> None:
        for name, declaration in self.program.program.declarations.items():
            shape = self._population_shape(declaration, frame)
            self.population_shapes[name] = shape
            if name not in frame:
                frame[name] = _make_array(shape, _zero_for_type(declaration.value_type))
            elif _deep_shape(frame[name]) != shape:
                actual_shape = _deep_shape(frame[name])
                raise BrainCodeRuntimeError(
                    f"initial population :{name} has shape {actual_shape}; "
                    f"declared {shape}"
                )

    def _population_shape(
        self, declaration: Statement, frame: Mapping[str, Any]
    ) -> tuple[int, ...]:
        dimensions: list[int] = []
        for index, expression in enumerate(declaration.dimensions):
            value = self._eval_expression(
                expression, [frame], {}, frame, self.parameters
            )
            dimension = _require_integer(
                value,
                f"dimension {index} of population :{declaration.name}",
            )
            if dimension < 0:
                raise BrainCodeRuntimeError(
                    f"dimension {index} of population :{declaration.name} "
                    "must be non-negative"
                )
            dimensions.append(dimension)
        return tuple(dimensions)

    def _validate_population_shapes(self, frame: Mapping[str, Any]) -> None:
        for name, expected_shape in self.population_shapes.items():
            if name not in frame:
                raise BrainCodeRuntimeError(
                    f"population :{name} is missing from the state frame"
                )
            actual_shape = _deep_shape(frame[name])
            if actual_shape != expected_shape:
                raise BrainCodeRuntimeError(
                    f"population :{name} has shape {actual_shape}; "
                    f"declared {expected_shape}"
                )

    def _read_frame_value(self, frame: Mapping[str, Any], name: str) -> Any:
        if name not in frame:
            raise BrainCodeRuntimeError(f"undefined state signal :{name}")
        value = frame[name]
        if isinstance(value, list):
            return _ArrayView(name, value)
        return value

    def _normalize_indices(
        self,
        name: str,
        indices: tuple[Any, ...],
        value: Any,
        boundary: Any | None = None,
    ) -> tuple[Any, ...] | Any:
        if not indices:
            return ()
        shape = self.population_shapes.get(name)
        if shape is None:
            shape = _deep_shape(value)
        policy = boundary if boundary is not None else self.boundaries.get(name)
        normalized: list[int] = []
        for dimension, raw_index in enumerate(indices):
            index = _require_integer(raw_index, f"index for population :{name}")
            if dimension >= len(shape):
                raise BrainCodeRuntimeError(
                    f"too many indices for population :{name}"
                )
            size = shape[dimension]
            if 0 <= index < size:
                normalized.append(index)
            elif policy == "wrap":
                if size == 0:
                    return False
                normalized.append(index % size)
            elif policy in {"insulated", "clamp"}:
                if size == 0:
                    return False
                normalized.append(min(max(index, 0), size - 1))
            elif policy in {"dead", "False", False, "false"}:
                return False
            else:
                raise BrainCodeRuntimeError(
                    f"index {index} is outside population :{name} "
                    f"(dimension size {size})"
                )
        return tuple(normalized)

    def _index_value(
        self,
        name: str,
        value: Any,
        indices: tuple[Any, ...],
        boundary: Any | None = None,
    ) -> Any:
        normalized = self._normalize_indices(name, indices, value, boundary)
        if normalized is False:
            return False
        return _nested_get(value, normalized)

    def _eval_expression(
        self,
        expression: Expression,
        frames: Sequence[Mapping[str, Any]],
        locals_: Mapping[str, Any],
        next_frame: Mapping[str, Any],
        parameters: Mapping[str, Any],
    ) -> Any:
        def read_symbol(name: str) -> Any:
            if name in locals_:
                return locals_[name]
            if name in parameters:
                return parameters[name]
            return self._read_frame_value(frames[-1], name)

        def read_index(name: str, indices: tuple[Any, ...]) -> Any:
            value = self._read_frame_value(frames[-1], name)
            if isinstance(value, _ArrayView):
                return self._index_value(name, value.values, indices)
            if indices:
                raise BrainCodeRuntimeError(f":{name} is not an indexed population")
            return value

        def read_history(name: str, delay: int, indices: tuple[Any, ...]) -> Any:
            frame_index = len(frames) - delay
            if frame_index < 0:
                raise BrainCodeRuntimeError(
                    f"history :{name}~{delay} is unavailable"
                )
            value = self._read_frame_value(frames[frame_index], name)
            if isinstance(value, _ArrayView):
                if indices:
                    return self._index_value(name, value.values, indices)
                return value
            if indices:
                raise BrainCodeRuntimeError(f":{name} is not an indexed population")
            return value

        try:
            return evaluate_expression(
                expression,
                symbols={**self._symbols(), **parameters},
                locals_=locals_,
                read_symbol=read_symbol,
                read_index=read_index,
                read_history=read_history,
                functions=self.functions | {"neighbor_count": self._neighbor_count},
            )
        except Exception as error:
            if isinstance(error, BrainCodeRuntimeError):
                raise
            raise BrainCodeRuntimeError(
                f"{expression.location.source}:{expression.location.line}: {error}"
            ) from error

    def _neighbor_count(
        self,
        population: _ArrayView,
        *coordinates: int,
        neighborhood: str | None = None,
        boundary: Any = "dead",
        radius: int = 1,
        include_center: bool = False,
    ) -> int:
        if not isinstance(population, _ArrayView):
            raise BrainCodeRuntimeError("neighbor_count expects a population history")
        dimensions = len(coordinates)
        if dimensions not in {1, 2, 3}:
            raise BrainCodeRuntimeError("neighbor_count supports 1D, 2D, or 3D")
        coordinates = tuple(
            _require_integer(value, "neighbor coordinate") for value in coordinates
        )
        radius = _require_integer(radius, "neighbor radius")
        if radius < 0:
            raise BrainCodeRuntimeError("neighbor radius must be non-negative")
        if neighborhood not in {None, "moore_2d", "moore_3d"}:
            raise BrainCodeRuntimeError(
                f"unsupported neighborhood {neighborhood!r}"
            )
        if neighborhood == "moore_2d" and dimensions != 2:
            raise BrainCodeRuntimeError("moore_2d requires two coordinates")
        if neighborhood == "moore_3d" and dimensions != 3:
            raise BrainCodeRuntimeError("moore_3d requires three coordinates")
        count = 0
        ranges = [range(-radius, radius + 1) for _ in range(dimensions)]
        for offset in itertools.product(*ranges):
            if not include_center and all(item == 0 for item in offset):
                continue
            indices = tuple(coordinate + delta for coordinate, delta in zip(coordinates, offset))
            value = self._index_value(
                population.name, population.values, indices, boundary
            )
            count += int(bool(value))
        return count

    def _assign(
        self,
        statement: Statement,
        value: Any,
        frame: dict[str, Any],
        locals_: Mapping[str, Any],
        parameters: Mapping[str, Any],
        frames: Sequence[Mapping[str, Any]],
        writes: set[tuple[str, tuple[int, ...]]],
    ) -> None:
        if statement.name is None:
            raise BrainCodeRuntimeError("assignment has no target")
        if not statement.target_indices:
            key = (statement.name, ())
            if key in writes:
                raise BrainCodeRuntimeError(
                    f"conflicting writes to :{statement.name}"
                )
            writes.add(key)
            frame[statement.name] = copy.deepcopy(value)
            return
        if statement.name not in frame:
            raise BrainCodeRuntimeError(f"undefined assignment target :{statement.name}")
        indices = tuple(
            _require_integer(
                self._eval_expression(item, frames, locals_, frame, parameters),
                f"assignment index for :{statement.name}",
            )
            for item in statement.target_indices
        )
        shape = self.population_shapes.get(statement.name)
        if shape is not None:
            if len(indices) > len(shape):
                raise BrainCodeRuntimeError(
                    f"too many assignment indices for :{statement.name}"
                )
            for dimension, index in enumerate(indices):
                if index < 0 or index >= shape[dimension]:
                    raise BrainCodeRuntimeError(
                        f"assignment index {index} is outside population "
                        f":{statement.name} (dimension size {shape[dimension]})"
                    )
        try:
            previous_value = _nested_get(frame[statement.name], indices)
            if _deep_shape(previous_value) != _deep_shape(value):
                raise BrainCodeRuntimeError(
                    f"assignment to :{statement.name}{indices} changes its shape"
                )
        except (IndexError, TypeError) as error:
            raise BrainCodeRuntimeError(
                f"invalid assignment index for :{statement.name}{indices}"
            ) from error
        key = (statement.name, indices)
        if key in writes:
            raise BrainCodeRuntimeError(
                f"conflicting writes to :{statement.name}{indices}"
            )
        writes.add(key)
        try:
            _nested_set(frame[statement.name], indices, copy.deepcopy(value))
        except (IndexError, TypeError) as error:
            raise BrainCodeRuntimeError(
                f"invalid assignment index for :{statement.name}{indices}"
            ) from error

    def _execute_block(
        self,
        statements: Sequence[Statement],
        frame: dict[str, Any],
        locals_: dict[str, Any],
        parameters: Mapping[str, Any],
        frames: Sequence[Mapping[str, Any]],
        writes: set[tuple[str, tuple[int, ...]]],
    ) -> None:
        for statement in statements:
            if statement.kind == "assignment":
                assert statement.expression is not None
                value = self._eval_expression(
                    statement.expression, frames, locals_, frame, parameters
                )
                self._assign(
                    statement, value, frame, locals_, parameters, frames, writes
                )
            elif statement.kind == "let":
                assert statement.expression is not None and statement.name is not None
                locals_[statement.name] = self._eval_expression(
                    statement.expression, frames, locals_, frame, parameters
                )
            elif statement.kind == "conditional":
                assert statement.condition is not None
                if self._eval_expression(
                    statement.condition, frames, locals_, frame, parameters
                ):
                    self._execute_block(
                        statement.body, frame, dict(locals_), parameters, frames, writes
                    )
            elif statement.kind == "each":
                declaration = self.program.program.declarations[
                    statement.collection or ""
                ]
                shape = self.population_shapes[statement.collection or ""]
                expected = tuple(
                    int(self._eval_expression(item, frames, locals_, frame, parameters))
                    for item in declaration.dimensions
                )
                if shape != expected:
                    raise BrainCodeRuntimeError(
                        f"population :{statement.collection} has shape {shape}; "
                        f"declared {expected}"
                    )
                for indices in itertools.product(*(range(size) for size in expected)):
                    scope = dict(locals_)
                    scope.update(zip(statement.bindings, indices))
                    self._execute_block(
                        statement.body, frame, scope, parameters, frames, writes
                    )

    def step(self, next_inputs: Mapping[str, Any] | None = None) -> dict[str, Any]:
        if next_inputs is not None and not isinstance(next_inputs, Mapping):
            raise BrainCodeRuntimeError("tick inputs must be a mapping")
        current = self.frames[-1]
        next_frame = copy.deepcopy(current)
        if next_inputs:
            next_frame.update(copy.deepcopy(dict(next_inputs)))
        parameters = self.parameters
        read_frames = self.frames
        writes: set[tuple[str, tuple[int, ...]]] = set()
        try:
            self._validate_population_shapes(next_frame)
            executable = tuple(
                statement
                for statement in self.program.program.statements
                if statement.kind not in {"population", "tensor", "boundary"}
            )
            self._execute_block(
                executable, next_frame, {}, parameters, read_frames, writes
            )
        except Exception as error:
            if isinstance(error, BrainCodeRuntimeError):
                raise BrainCodeRuntimeError(
                    f"tick {self.tick + 1}: {error}"
                ) from error
            raise BrainCodeRuntimeError(
                f"tick {self.tick + 1}: {error}"
            ) from error
        self.frames.append(next_frame)
        self.tick += 1
        return copy.deepcopy(next_frame)

    def run(
        self,
        ticks: int,
        *,
        input_frames: Sequence[Mapping[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        if isinstance(ticks, bool) or not isinstance(ticks, int):
            raise ValueError("ticks must be an integer")
        if ticks < 0:
            raise ValueError("ticks must be non-negative")
        if input_frames is not None and (
            isinstance(input_frames, (str, bytes))
            or not isinstance(input_frames, Sequence)
        ):
            raise ValueError("input_frames must be a sequence of mappings")
        inputs = list(input_frames or [])
        if any(not isinstance(frame, Mapping) for frame in inputs):
            raise ValueError("each input frame must be a mapping")
        if len(inputs) > ticks + 1:
            raise ValueError(
                f"received {len(inputs)} input frames for {ticks} ticks; "
                f"at most {ticks + 1} are valid"
            )
        if inputs:
            initial_frame = copy.deepcopy(self.frames[-1])
            initial_frame.update(copy.deepcopy(dict(inputs[0])))
            self._validate_population_shapes(initial_frame)
            self.frames[-1] = initial_frame
        for offset in range(ticks):
            next_inputs = inputs[offset + 1] if offset + 1 < len(inputs) else None
            self.step(next_inputs)
        return copy.deepcopy(self.frames)


def run(
    program: CompiledProgram,
    *,
    initial_state: Mapping[str, Any] | None = None,
    parameters: Mapping[str, Any] | None = None,
    functions: Mapping[str, Callable[..., Any]] | None = None,
    ticks: int = 1,
    input_frames: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    runtime = Runtime(
        program,
        initial_state=initial_state,
        parameters=parameters,
        functions=functions,
    )
    return runtime.run(ticks, input_frames=input_frames)
