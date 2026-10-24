"""Human-readable expansion of data-parallel BrainCode rules."""

from __future__ import annotations

import itertools
import re
from collections.abc import Mapping
from typing import Any

from braincode.compiler import CompiledProgram
from braincode.expressions import evaluate_expression
from braincode.model import Statement


def render_expanded(
    program: CompiledProgram,
    *,
    parameters: Mapping[str, Any] | None = None,
    max_instances: int = 4096,
) -> str:
    """Render loops as executable BrainCode assignments for a .bcc source file."""
    parameters = dict(parameters or {})
    output: list[str] = [
        f"# Compiled BrainCode source expanded from: {program.source_name}",
        "# Data-parallel loops are unfolded into indexed assignments.",
    ]
    emitted = 0

    def dimension(expression: Any) -> int:
        try:
            return int(evaluate_expression(
                expression,
                symbols=parameters,
                locals_={},
                read_symbol=lambda name: parameters[name],
                read_index=lambda name, indices: (_ for _ in ()).throw(
                    ValueError(f"dimension cannot index :{name}")
                ),
                read_history=lambda name, delay, indices: (_ for _ in ()).throw(
                    ValueError(f"dimension cannot read history :{name}~{delay}")
                ),
            ))
        except (KeyError, TypeError, ValueError) as error:
            raise ValueError(
                f"cannot expand dimension {expression.source!r}; provide its "
                "value with --parameters"
            ) from error

    def visit(
        statements: tuple[Statement, ...],
        scope: dict[str, int],
        local_names: dict[str, str],
        indentation: str = "",
    ) -> None:
        nonlocal emitted
        for statement in statements:
            if statement.kind == "each":
                declaration = program.program.declarations[statement.collection or ""]
                shape = tuple(dimension(item) for item in declaration.dimensions)
                count = 1
                for size in shape:
                    count *= size
                if emitted + count > max_instances:
                    raise ValueError(
                        f"expansion requires {emitted + count} instances, exceeding "
                        f"the limit of {max_instances}"
                    )
                for indices in itertools.product(*(range(size) for size in shape)):
                    child_scope = dict(scope)
                    child_scope.update(zip(statement.bindings, indices))
                    child_local_names = dict(local_names)
                    header = ", ".join(
                        f":{name}={value}"
                        for name, value in zip(statement.bindings, indices)
                    )
                    output.append(f"{indentation}# instance ({header})")
                    visit(
                        statement.body,
                        child_scope,
                        child_local_names,
                        indentation,
                    )
                    emitted += 1
            elif statement.kind == "assignment":
                target = f":{statement.name}"
                if statement.target_indices:
                    indices = ", ".join(
                        _replace_locals(expr.source, scope, local_names)
                        for expr in statement.target_indices
                    )
                    target += f"[{indices}]"
                value = _replace_locals(
                    statement.expression.source if statement.expression else "",
                    scope,
                    local_names,
                )
                output.append(f"{indentation}{target} = {value}")
            elif statement.kind == "let":
                value = _replace_locals(
                    statement.expression.source if statement.expression else "",
                    scope,
                    local_names,
                )
                if scope:
                    suffix = "_".join(
                        f"{name}{index}" for name, index in scope.items()
                    )
                    generated_name = f"{statement.name}_{suffix}"
                else:
                    generated_name = statement.name or ""
                output.append(f"{indentation}let {generated_name} = {value}")
                if statement.name is not None:
                    local_names[statement.name] = generated_name
            elif statement.kind == "conditional":
                condition = _replace_locals(
                    statement.condition.source if statement.condition else "",
                    scope,
                    local_names,
                )
                output.append(f"{indentation}?({condition}):")
                visit(
                    statement.body,
                    scope,
                    dict(local_names),
                    indentation + "    ",
                )
            elif statement.kind in {"population", "tensor"}:
                dimensions = ", ".join(item.source for item in statement.dimensions)
                output.append(
                    f"{indentation}"
                    f"{statement.kind} :{statement.name}[{dimensions}] "
                    f"of {statement.value_type}"
                )
            elif statement.kind == "boundary":
                output.append(
                    f"{indentation}boundary :{statement.name} = {statement.boundary}"
                )

    visit(program.program.statements, {}, {})
    return "\n".join(output) + "\n"


def _replace_locals(
    source: str,
    scope: Mapping[str, int],
    local_names: Mapping[str, str],
) -> str:
    for name, value in scope.items():
        source = re.sub(rf":{re.escape(name)}\b", str(value), source)
    if not local_names:
        return source

    result: list[str] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char in {"'", '"'}:
            quote = char
            start = index
            index += 1
            escaped = False
            while index < len(source):
                current = source[index]
                index += 1
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == quote:
                    break
            result.append(source[start:index])
            continue
        if char.isalpha() or char == "_":
            end = index + 1
            while end < len(source) and (source[end].isalnum() or source[end] == "_"):
                end += 1
            identifier = source[index:end]
            result.append(local_names.get(identifier, identifier))
            index = end
            continue
        result.append(char)
        index += 1
    return "".join(result)
