"""Deterministic, serial reference runtime for BrainCode."""

from __future__ import annotations

import ast
import copy
import itertools
import json
import math
import struct
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from braincode.compiler import CompiledProgram
from braincode.expressions import evaluate_expression, parse_expression
from braincode.model import Expression, Statement


class BrainCodeRuntimeError(RuntimeError):
    """A model could not be evaluated or committed."""


class BrainCodeAdapterError(BrainCodeRuntimeError):
    """A host adapter failed before or after a committed transition."""


@dataclass(frozen=True)
class _ArrayView:
    name: str
    values: Any


def _zero_for_type(value_type: str | None) -> Any:
    if value_type == "Bool":
        return False
    return 0.0 if value_type in {"Float32", "Float64"} else 0


def _typed_value(name: str, value: Any, value_type: str | None) -> Any:
    if value_type is None:
        return value
    if isinstance(value, list):
        return [_typed_value(name, item, value_type) for item in value]
    if value_type == "Bool":
        if not isinstance(value, bool):
            raise BrainCodeRuntimeError(f":{name} requires Bool values")
        return value
    if value_type in {"Int32", "Int64"}:
        if isinstance(value, bool) or not isinstance(value, int):
            raise BrainCodeRuntimeError(f":{name} requires {value_type} values")
        lower, upper = (
            (-(2**31), 2**31 - 1)
            if value_type == "Int32"
            else (-(2**63), 2**63 - 1)
        )
        if not lower <= value <= upper:
            raise BrainCodeRuntimeError(
                f":{name} value {value} is outside the {value_type} range"
            )
        return value
    if value_type in {"Float32", "Float64"}:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise BrainCodeRuntimeError(f":{name} requires {value_type} values")
        try:
            converted = float(value)
        except (OverflowError, ValueError) as error:
            raise BrainCodeRuntimeError(
                f":{name} value is outside the {value_type} range"
            ) from error
        if not math.isfinite(converted):
            raise BrainCodeRuntimeError(f":{name} requires finite {value_type} values")
        if value_type == "Float32":
            try:
                converted = struct.unpack("!f", struct.pack("!f", converted))[0]
            except OverflowError as error:
                raise BrainCodeRuntimeError(
                    f":{name} value is outside the Float32 range"
                ) from error
        return converted
    raise BrainCodeRuntimeError(f"unsupported declared type {value_type!r} for :{name}")


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
        history_window: int | None = None,
        max_ticks: int | None = None,
        max_population_elements: int | None = None,
        max_frame_bytes: int | None = None,
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
        for option_name, option in (
            ("history_window", history_window),
            ("max_population_elements", max_population_elements),
            ("max_frame_bytes", max_frame_bytes),
        ):
            if option is not None and (
                isinstance(option, bool) or not isinstance(option, int) or option < 1
            ):
                raise ValueError(f"{option_name} must be a positive integer")
        if max_ticks is not None and (
            isinstance(max_ticks, bool) or not isinstance(max_ticks, int) or max_ticks < 0
        ):
            raise ValueError("max_ticks must be a non-negative integer")

        self.program = program
        self._strict_declarations = any(
            item.kind in {"state", "input"} for item in program.program.statements
        )
        self._declared_input_names = {
            name for name, item in program.program.declarations.items()
            if item.kind == "input"
        }
        self._known_state_names = set(program.program.declarations)
        self._known_state_names.update(
            item.name
            for item in _walk_statements(program.program.statements)
            if item.kind == "assignment" and item.name is not None
        )
        self.history_window = history_window
        self.max_ticks = max_ticks
        self.max_population_elements = max_population_elements
        self.max_frame_bytes = max_frame_bytes
        self.input_adapters: dict[str, Callable[[Any], Any]] = {}
        self.output_adapters: dict[str, Callable[[int, Mapping[str, Any]], Any]] = {}
        self.input_log: list[dict[str, Any]] = []
        self._ticks_executed = 0
        self._active_statement: Statement | None = None
        self._max_history_delay = _program_max_history_delay(program)
        if history_window is not None and history_window < self._max_history_delay:
            raise ValueError(
                f"history_window must be at least the maximum history delay "
                f"({self._max_history_delay})"
            )
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
        self._validate_state_frame_names(current)
        self._initialize_populations(current)
        for historical_frame in history:
            self._validate_state_frame_names(historical_frame)
            self._validate_population_shapes(historical_frame)
        for name, declaration in program.program.declarations.items():
            if declaration.kind == "state":
                if name not in current:
                    raise BrainCodeRuntimeError(
                        f"declared state :{name} is missing from initial_state"
                    )
                current[name] = _typed_value(
                    name, current[name], declaration.value_type
                )
            elif declaration.kind == "input" and name in current:
                current[name] = _typed_value(
                    name, current[name], declaration.value_type
                )
        history.append(current)
        self.frames: list[dict[str, Any]] = history
        self.tick = len(history) - 1
        self._trim_history()
        for frame_index, frame in enumerate(self.frames):
            self._validate_frame_size(
                frame,
                self.tick - len(self.frames) + frame_index + 1,
            )

    def register_input_adapter(
        self, name: str, adapter: Callable[[Any], Any]
    ) -> None:
        if not name:
            raise ValueError("input adapter name must not be empty")
        if name in self.input_adapters:
            raise ValueError(f"input adapter {name!r} is already registered")
        if not callable(adapter):
            raise TypeError("input adapter must be callable")
        self.input_adapters[name] = adapter

    def register_output_adapter(
        self,
        name: str,
        adapter: Callable[[int, Mapping[str, Any]], Any],
    ) -> None:
        if not name:
            raise ValueError("output adapter name must not be empty")
        if name in self.output_adapters:
            raise ValueError(f"output adapter {name!r} is already registered")
        if not callable(adapter):
            raise TypeError("output adapter must be callable")
        self.output_adapters[name] = adapter

    def _adapt_inputs(self, inputs: Mapping[str, Any] | None) -> dict[str, Any]:
        if inputs is None:
            return {}
        if not isinstance(inputs, Mapping):
            raise BrainCodeRuntimeError("tick inputs must be a mapping")
        result = copy.deepcopy(dict(inputs))
        if self._strict_declarations:
            unknown_inputs = set(result) - self._declared_input_names
            if unknown_inputs:
                raise BrainCodeRuntimeError(
                    f"tick inputs contain undeclared input(s): "
                    f"{sorted(unknown_inputs)}"
                )
        for name, adapter in self.input_adapters.items():
            if name not in result:
                continue
            try:
                result[name] = adapter(copy.deepcopy(result[name]))
            except Exception as error:
                raise BrainCodeAdapterError(
                    f"input adapter {name!r} failed: {error}"
                ) from error
        return result

    def _validate_state_frame_names(self, frame: Mapping[str, Any]) -> None:
        if self._strict_declarations:
            unknown_names = set(frame) - self._known_state_names
            if unknown_names:
                raise BrainCodeRuntimeError(
                    f"state frame contains undeclared signal(s): "
                    f"{sorted(unknown_names)}"
                )

    def _dispatch_outputs(self) -> None:
        committed_frame = copy.deepcopy(self.frames[-1])
        for name, adapter in self.output_adapters.items():
            try:
                adapter(self.tick, copy.deepcopy(committed_frame))
            except Exception as error:
                raise BrainCodeAdapterError(
                    f"tick {self.tick} committed, but output adapter {name!r} "
                    f"failed: {error}"
                ) from error

    def _trim_history(self) -> None:
        if self.history_window is not None and len(self.frames) > self.history_window:
            del self.frames[:-self.history_window]

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
        total_elements = 0
        for name, declaration in self.program.program.declarations.items():
            if declaration.kind not in {"population", "tensor"}:
                continue
            shape = self._population_shape(declaration, frame)
            element_count = math.prod(shape)
            total_elements += element_count
            if self.max_population_elements is not None and (
                total_elements > self.max_population_elements
            ):
                raise BrainCodeRuntimeError(
                    f"declared populations contain at least {total_elements} "
                    f"elements; configured limit is {self.max_population_elements}"
                )
            self.population_shapes[name] = shape
            if name not in frame:
                frame[name] = _make_array(shape, _zero_for_type(declaration.value_type))
            else:
                frame[name] = _typed_value(name, frame[name], declaration.value_type)
            if _deep_shape(frame[name]) != shape:
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

    def _validate_population_shapes(self, frame: dict[str, Any]) -> None:
        for name, expected_shape in self.population_shapes.items():
            if name not in frame:
                raise BrainCodeRuntimeError(
                    f"population :{name} is missing from the state frame"
                )
            declaration = self.program.program.declarations[name]
            frame[name] = _typed_value(name, frame[name], declaration.value_type)
            actual_shape = _deep_shape(frame[name])
            if actual_shape != expected_shape:
                raise BrainCodeRuntimeError(
                    f"population :{name} has shape {actual_shape}; "
                    f"declared {expected_shape}"
                )
        for name, declaration in self.program.program.declarations.items():
            if declaration.kind == "state" and name not in frame:
                raise BrainCodeRuntimeError(
                    f"declared state :{name} is missing from the state frame"
                )
            if declaration.kind in {"state", "input"} and name in frame:
                frame[name] = _typed_value(name, frame[name], declaration.value_type)

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
            declaration = self.program.program.declarations.get(statement.name)
            if declaration is not None:
                value = _typed_value(
                    statement.name, value, declaration.value_type
                )
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
        declaration = self.program.program.declarations.get(statement.name)
        if declaration is not None:
            value = _typed_value(statement.name, value, declaration.value_type)
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
            self._active_statement = statement
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
                    _require_integer(
                        self._eval_expression(
                            item, frames, locals_, frame, parameters
                        ),
                        f"dimension of population :{statement.collection}",
                    )
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
        if self.max_ticks is not None and self._ticks_executed >= self.max_ticks:
            raise BrainCodeRuntimeError(
                f"configured tick limit of {self.max_ticks} has been reached"
            )
        current = self.frames[-1]
        next_frame = copy.deepcopy(current)
        adapted_inputs = self._adapt_inputs(next_inputs)
        if adapted_inputs:
            next_frame.update(copy.deepcopy(adapted_inputs))
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
            self._validate_population_shapes(next_frame)
        except Exception as error:
            message = str(error)
            active = self._active_statement
            if active is not None:
                location_prefix = (
                    f"{active.location.source}:{active.location.line}:"
                )
                if location_prefix not in message:
                    message = (
                        f"{active.location.source}:{active.location.line}:"
                        f"{active.location.column}: {message}"
                    )
            if isinstance(error, BrainCodeRuntimeError):
                raise BrainCodeRuntimeError(
                    f"tick {self.tick + 1}: {message}"
                ) from error
            raise BrainCodeRuntimeError(
                f"tick {self.tick + 1}: {message}"
            ) from error
        finally:
            self._active_statement = None
        self._validate_frame_size(next_frame, self.tick + 1)
        self.frames.append(next_frame)
        self.tick += 1
        self._ticks_executed += 1
        self.input_log.append(copy.deepcopy(adapted_inputs))
        self._trim_history()
        self._dispatch_outputs()
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
        if self.max_ticks is not None and self._ticks_executed + ticks > self.max_ticks:
            raise BrainCodeRuntimeError(
                f"run requests {self._ticks_executed + ticks} ticks; configured "
                f"limit is {self.max_ticks}"
            )
        if inputs:
            adapted_initial_inputs = self._adapt_inputs(inputs[0])
            initial_frame = copy.deepcopy(self.frames[-1])
            initial_frame.update(copy.deepcopy(adapted_initial_inputs))
            self._validate_population_shapes(initial_frame)
            self._validate_frame_size(initial_frame, self.tick)
            self.frames[-1] = initial_frame
            self.input_log.append(copy.deepcopy(adapted_initial_inputs))
            inputs[0] = adapted_initial_inputs
        for offset in range(ticks):
            next_inputs = inputs[offset + 1] if offset + 1 < len(inputs) else None
            self.step(next_inputs)
        return copy.deepcopy(self.frames)

    def _validate_frame_size(self, frame: Mapping[str, Any], tick: int) -> None:
        if self.max_frame_bytes is None:
            return
        try:
            frame_size = len(
                json.dumps(frame, sort_keys=True, separators=(",", ":")).encode("utf-8")
            )
        except (TypeError, ValueError) as error:
            raise BrainCodeRuntimeError(
                f"tick {tick} frame cannot be serialized for the configured "
                f"max_frame_bytes limit: {error}"
            ) from error
        if frame_size > self.max_frame_bytes:
            raise BrainCodeRuntimeError(
                f"tick {tick} frame is {frame_size} bytes; configured limit is "
                f"{self.max_frame_bytes}"
            )


def _walk_statements(statements: Sequence[Statement]) -> list[Statement]:
    result: list[Statement] = []
    for statement in statements:
        result.append(statement)
        result.extend(_walk_statements(statement.body))
    return result


def _statement_expressions(statement: Statement) -> list[Expression]:
    expressions = [
        *statement.target_indices,
        *statement.dimensions,
    ]
    if statement.expression is not None:
        expressions.append(statement.expression)
    if statement.condition is not None:
        expressions.append(statement.condition)
    return expressions


def _program_max_history_delay(program: CompiledProgram) -> int:
    delays = [1]
    for statement in _walk_statements(program.program.statements):
        for expression in _statement_expressions(statement):
            for node in ast.walk(parse_expression(expression)):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Name)
                    and node.func.id == "__bc_history__"
                    and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant)
                    and isinstance(node.args[1].value, int)
                    and not isinstance(node.args[1].value, bool)
                ):
                    delays.append(node.args[1].value)
    return max(delays)


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
