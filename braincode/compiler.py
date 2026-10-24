"""BrainCode source compiler and versioned JSON IR serialization."""

from __future__ import annotations

import ast
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from braincode.expressions import expression_to_data, parse_expression
from braincode.model import Expression, Program, SourceLocation, Statement
from braincode.parser import parse_source


IR_VERSION = 1
LANGUAGE_VERSION = "0.2"
VALUE_TYPES = {"Bool", "Int32", "Int64", "Float32", "Float64"}


class BrainCodeCompileError(ValueError):
    """A BrainCode program failed validation."""


class CompiledProgram:
    """A validated BrainCode program ready for a backend."""

    def __init__(self, program: Program):
        self.program = program

    @property
    def source_name(self) -> str:
        return self.program.source_name

    def to_dict(self) -> dict[str, Any]:
        return {
            "format": "braincode",
            "ir_version": IR_VERSION,
            "language_version": LANGUAGE_VERSION,
            "source_name": self.program.source_name,
            "statements": [_statement_to_data(item) for item in self.program.statements],
        }

    def to_json(self, *, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, sort_keys=True) + "\n"


def _statement_to_data(statement: Statement) -> dict[str, Any]:
    result: dict[str, Any] = {
        "kind": statement.kind,
        "location": asdict(statement.location),
    }
    if statement.name is not None:
        result["name"] = statement.name
    if statement.target_indices:
        result["target_indices"] = [
            expression_to_data(item) for item in statement.target_indices
        ]
    if statement.expression is not None:
        result["expression"] = expression_to_data(statement.expression)
    if statement.condition is not None:
        result["condition"] = expression_to_data(statement.condition)
    if statement.bindings:
        result["bindings"] = list(statement.bindings)
    if statement.collection is not None:
        result["collection"] = statement.collection
    if statement.dimensions:
        result["dimensions"] = [
            expression_to_data(item) for item in statement.dimensions
        ]
    if statement.value_type is not None:
        result["value_type"] = statement.value_type
    if statement.body:
        result["body"] = [_statement_to_data(item) for item in statement.body]
    if statement.boundary is not None:
        result["boundary"] = statement.boundary
    return result


def _expression_from_data(data: dict[str, Any]) -> Expression:
    expression = Expression(
        source=data["source"],
        location=SourceLocation(
            data["location"]["source"],
            data["location"]["line"],
            data["location"].get("column", 1),
        ),
    )
    expected_tree = expression_to_data(expression)["tree"]
    if "tree" in data and data["tree"] != expected_tree:
        raise BrainCodeCompileError(
            f"{expression.location.source}:{expression.location.line}: "
            "compiled expression tree does not match its source"
        )
    parse_expression(expression)
    return expression


def _statement_from_data(data: dict[str, Any]) -> Statement:
    location_data = data["location"]
    return Statement(
        kind=data["kind"],
        location=SourceLocation(
            location_data["source"],
            location_data["line"],
            location_data.get("column", 1),
        ),
        name=data.get("name"),
        target_indices=tuple(
            _expression_from_data(item) for item in data.get("target_indices", [])
        ),
        expression=_expression_from_data(data["expression"])
        if "expression" in data else None,
        condition=_expression_from_data(data["condition"])
        if "condition" in data else None,
        bindings=tuple(data.get("bindings", [])),
        collection=data.get("collection"),
        dimensions=tuple(
            _expression_from_data(item) for item in data.get("dimensions", [])
        ),
        value_type=data.get("value_type"),
        body=tuple(_statement_from_data(item) for item in data.get("body", [])),
        boundary=data.get("boundary"),
    )


def compile_source(source: str, source_name: str = "<string>") -> CompiledProgram:
    program = parse_source(source, source_name)
    _validate_program(program)
    return CompiledProgram(program)


def compile_file(
    source_path: str | Path,
    output_path: str | Path | None = None,
) -> CompiledProgram:
    path = Path(source_path)
    compiled = compile_source(path.read_text(encoding="utf-8"), str(path))
    if output_path is not None:
        save_compiled(compiled, output_path)
    return compiled


def save_compiled(program: CompiledProgram, output_path: str | Path) -> None:
    Path(output_path).write_text(program.to_json(), encoding="utf-8")


def load_compiled(path: str | Path) -> CompiledProgram:
    artifact_path = Path(path)
    if artifact_path.suffix.lower() == ".bcc":
        return compile_source(
            artifact_path.read_text(encoding="utf-8"),
            str(artifact_path),
        )
    data = json.loads(artifact_path.read_text(encoding="utf-8"))
    if data.get("format") != "braincode":
        raise BrainCodeCompileError("not a BrainCode compiled artifact")
    if data.get("ir_version") != IR_VERSION:
        raise BrainCodeCompileError(
            f"unsupported .bcc IR version {data.get('ir_version')!r}; "
            f"this runtime supports {IR_VERSION}"
        )
    statements = tuple(_statement_from_data(item) for item in data["statements"])
    declarations = {
        item.name: item
        for item in statements
        if item.kind in {"population", "tensor", "state", "input"}
        and item.name is not None
    }
    program = Program(
        source="",
        statements=statements,
        source_name=data.get("source_name", str(path)),
        declarations=declarations,
    )
    _validate_program(program)
    return CompiledProgram(program)


def _validate_program(program: Program) -> None:
    declarations = program.declarations
    strict_signal_declarations = any(
        item.kind in {"state", "input"} for item in program.statements
    )
    declared_signal_names = set(declarations)
    declared_signal_names.update(
        statement.name
        for statement in _walk(program.statements)
        if statement.kind == "assignment" and statement.name is not None
    )
    for statement in _walk(program.statements):
        if statement.kind in {"state", "input", "population", "tensor"}:
            if statement.value_type not in VALUE_TYPES:
                _error(
                    statement,
                    f"unsupported declared value type {statement.value_type!r}; "
                    f"expected one of {sorted(VALUE_TYPES)}",
                )
        if statement.kind in {"population", "tensor"} and not statement.dimensions:
            _error(statement, f"{statement.kind} :{statement.name} needs at least one dimension")
        if statement.kind == "boundary":
            if statement.name not in declarations:
                _error(statement, f"boundary target :{statement.name} is undeclared")
            if declarations[statement.name or ""].kind not in {"population", "tensor"}:
                _error(
                    statement,
                    f"boundary target :{statement.name} must be a population or tensor",
                )
            if statement.boundary not in {
                "dead", "wrap", "insulated", "clamp", "False", "false"
            }:
                _error(
                    statement,
                    f"unsupported boundary policy {statement.boundary!r}",
                )
        if statement.kind == "assignment" and statement.name in declarations:
            declaration = declarations[statement.name or ""]
            if declaration.kind == "input":
                _error(statement, f"input :{statement.name} is read-only")
        if strict_signal_declarations:
            for expression in _statement_expressions(statement):
                for name in _braincode_references(expression):
                    if name not in declared_signal_names:
                        _error(
                            statement,
                            f"undeclared signal :{name}; declare it as state or input",
                        )
        if statement.kind == "each":
            if statement.collection not in declarations:
                _error(statement, f"unknown population :{statement.collection}")
            declaration = declarations[statement.collection or ""]
            if len(statement.bindings) != len(declaration.dimensions):
                _error(
                    statement,
                    f"`each` binds {len(statement.bindings)} index value(s), but "
                    f":{statement.collection} has {len(declaration.dimensions)} dimension(s)",
                )
        if statement.kind == "assignment" and statement.target_indices:
            declaration = declarations.get(statement.name or "")
            if declaration is None:
                _error(
                    statement,
                    f"indexed assignment target :{statement.name} has no population "
                    "or tensor declaration",
                )
            if len(statement.target_indices) > len(declaration.dimensions):
                _error(
                    statement,
                    f"assignment to :{statement.name} uses "
                    f"{len(statement.target_indices)} index value(s), but the "
                    f"population has only {len(declaration.dimensions)} dimension(s)",
                )

    writers: dict[str, set[tuple[str, ...] | None]] = {}
    for statement in _collect_assignments(program.statements, inside_each=False):
        if statement.name is None:
            continue
        target = (
            tuple(item.source for item in statement.target_indices)
            if statement.target_indices else None
        )
        targets = writers.setdefault(statement.name, set())
        if target is None and targets or target in targets:
            _error(
                statement,
                f"duplicate rule target for :{statement.name}; combine scalar "
                "rules or ensure indexed targets are unique",
            )
        if target is not None and None in targets:
            _error(
                statement,
                f"scalar and indexed rule sites both write :{statement.name}",
            )
        targets.add(target)


def _collect_assignments(
    statements: tuple[Statement, ...], *, inside_each: bool
) -> list[Statement]:
    assignments: list[Statement] = []
    for statement in statements:
        if statement.kind == "assignment":
            if inside_each and not statement.target_indices:
                _error(
                    statement,
                    "a rule inside `each` must write an indexed population element",
                )
            assignments.append(statement)
        elif statement.kind == "each":
            local_targets: set[tuple[str, tuple[str, ...] | None]] = set()
            representative_assignments: list[Statement] = []
            for assignment in _collect_assignments(statement.body, inside_each=True):
                if assignment.name is None:
                    continue
                target = (
                    tuple(item.source for item in assignment.target_indices)
                    if assignment.target_indices else None
                )
                identity = (assignment.name, target)
                if identity in local_targets:
                    _error(
                        assignment,
                        f"duplicate rule target for :{assignment.name}{target}",
                    )
                local_targets.add(identity)
                representative_assignments.append(assignment)
            assignments.extend(representative_assignments)
        else:
            assignments.extend(
                _collect_assignments(statement.body, inside_each=inside_each)
            )
    return assignments


def _walk(statements: tuple[Statement, ...]) -> list[Statement]:
    result: list[Statement] = []
    for statement in statements:
        result.append(statement)
        result.extend(_walk(statement.body))
    return result


def _statement_expressions(statement: Statement) -> list[Expression]:
    result = [*statement.target_indices, *statement.dimensions]
    if statement.expression is not None:
        result.append(statement.expression)
    if statement.condition is not None:
        result.append(statement.condition)
    return result


def _braincode_references(expression: Expression) -> set[str]:
    tree = parse_expression(expression)
    names: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in {
                "__bc_symbol__", "__bc_index__", "__bc_history__"
            }
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and isinstance(node.args[0].value, str)
        ):
            names.add(node.args[0].value)
    return names


def _error(statement: Statement, message: str) -> None:
    raise BrainCodeCompileError(
        f"{statement.location.source}:{statement.location.line}:"
        f"{statement.location.column}: {message}"
    )
