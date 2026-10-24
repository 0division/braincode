"""Indentation-aware parser for the BrainCode v0.2 draft syntax."""

from __future__ import annotations

import re

from braincode.expressions import ExpressionError, parse_expression, split_top_level
from braincode.model import Expression, Program, SourceLocation, Statement


class BrainCodeSyntaxError(ValueError):
    """A source-level BrainCode syntax error with a location."""


_DECLARATION = re.compile(
    r"^(population|tensor|state|input)\s+:([A-Za-z_]\w*)\s*(?:\[(.*)\])?"
    r"(?:\s+of\s+([A-Za-z_]\w*))?$"
)
_EACH = re.compile(r"^each\s+(.+?)\s+in\s+:([A-Za-z_]\w*)\s+parallel:$")
_LET = re.compile(r"^let\s+([A-Za-z_]\w*)\s*=\s*(.+)$")
_BOUNDARY = re.compile(r"^boundary\s+:([A-Za-z_]\w*)\s*=\s*([A-Za-z_]\w*)$")
_ASSIGNMENT = re.compile(r"^:([A-Za-z_]\w*)\s*(?:\[(.*)\])?\s*=\s*(.+)$")
_CONDITIONAL = re.compile(r"^\?\((.*)\):$")


def _strip_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char == "#":
            return line[:index]
    return line


def _balance(text: str) -> int:
    depth = 0
    quote: str | None = None
    escaped = False
    for char in text:
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
        elif char in {"'", '"'}:
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
    return depth


def _logical_lines(source: str, source_name: str) -> list[tuple[int, int, str]]:
    result: list[tuple[int, int, str]] = []
    pending: str | None = None
    pending_indent = 0
    pending_line = 0
    pending_balance = 0

    for line_number, raw in enumerate(source.splitlines(), start=1):
        uncommented = _strip_comment(raw).rstrip()
        if not uncommented.strip():
            continue
        leading_whitespace = uncommented[:len(uncommented) - len(uncommented.lstrip())]
        indent = len(leading_whitespace)
        if "\t" in leading_whitespace:
            raise BrainCodeSyntaxError(
                f"{source_name}:{line_number}: tabs are not allowed for indentation"
            )
        text = uncommented.strip()
        if pending is not None:
            continuation = (
                (pending_balance > 0 and indent >= pending_indent)
                or (
                    indent > pending_indent
                    and (
                        pending.rstrip().endswith(("=", "+", "-", "*", "/"))
                        or text.startswith(("else ", "and ", "or ", "+", "-", "*", "/"))
                    )
                )
            )
            if continuation:
                pending += " " + text
                pending_balance += _balance(text)
                continue
            result.append((pending_indent, pending_line, pending))
            pending = None
        pending = text
        pending_indent = indent
        pending_line = line_number
        pending_balance = _balance(text)
        if pending_balance < 0:
            raise BrainCodeSyntaxError(
                f"{source_name}:{line_number}: unmatched closing delimiter"
            )
        if pending_balance == 0 and not pending.endswith("="):
            result.append((pending_indent, pending_line, pending))
            pending = None

    if pending is not None:
        if pending_balance != 0:
            raise BrainCodeSyntaxError(
                f"{source_name}:{pending_line}: unclosed delimiter"
            )
        result.append((pending_indent, pending_line, pending))
    return result


class _Parser:
    def __init__(self, source: str, source_name: str):
        self.source = source
        self.source_name = source_name
        self.lines = _logical_lines(source, source_name)
        self.index = 0

    def parse(self) -> Program:
        if not self.lines:
            raise BrainCodeSyntaxError(f"{self.source_name}: source is empty")
        statements = self._block(self.lines[0][0])
        if self.index != len(self.lines):
            indent, line, _ = self.lines[self.index]
            raise BrainCodeSyntaxError(
                f"{self.source_name}:{line}: unexpected indentation of {indent} spaces"
            )
        declarations: dict[str, Statement] = {}
        for statement in statements:
            if statement.kind in {"population", "tensor", "state", "input"}:
                if statement.name in declarations:
                    raise BrainCodeSyntaxError(
                        f"{statement.location.source}:{statement.location.line}: "
                        f"duplicate declaration for :{statement.name}"
                    )
                declarations[statement.name or ""] = statement
        return Program(
            source=self.source,
            statements=tuple(statements),
            source_name=self.source_name,
            declarations=declarations,
        )

    def _block(self, indentation: int) -> list[Statement]:
        statements: list[Statement] = []
        while self.index < len(self.lines):
            indent, line_number, text = self.lines[self.index]
            if indent < indentation:
                break
            if indent > indentation:
                raise BrainCodeSyntaxError(
                    f"{self.source_name}:{line_number}: unexpected indentation"
                )
            location = SourceLocation(self.source_name, line_number)
            self.index += 1

            declaration = _DECLARATION.fullmatch(text)
            if declaration:
                kind, name, dimensions, value_type = declaration.groups()
                if kind in {"state", "input"}:
                    if dimensions is not None:
                        raise BrainCodeSyntaxError(
                            f"{location.source}:{location.line}: "
                            f"{kind} declarations do not accept dimensions"
                        )
                    dimensions_expr = ()
                else:
                    dimensions_expr = tuple(
                        self._expression(part, location)
                        for part in split_top_level(dimensions or "")
                    )
                statements.append(Statement(
                    kind=kind,
                    location=location,
                    name=name,
                    dimensions=dimensions_expr,
                    value_type=value_type or "Float64",
                ))
                continue

            boundary = _BOUNDARY.fullmatch(text)
            if boundary:
                name, policy = boundary.groups()
                statements.append(Statement(
                    kind="boundary", location=location, name=name, boundary=policy
                ))
                continue

            each = _EACH.fullmatch(text)
            if each:
                raw_bindings, collection = each.groups()
                if raw_bindings.startswith("(") and raw_bindings.endswith(")"):
                    raw_bindings = raw_bindings[1:-1]
                bindings = tuple(
                    token.strip().removeprefix(":")
                    for token in split_top_level(raw_bindings)
                )
                if not bindings or any(not re.fullmatch(r"[A-Za-z_]\w*", item)
                                       for item in bindings):
                    self._error(location, "invalid `each` binding")
                body = self._child_block(indentation, location)
                statements.append(Statement(
                    kind="each",
                    location=location,
                    bindings=bindings,
                    collection=collection,
                    body=tuple(body),
                ))
                continue

            conditional = _CONDITIONAL.fullmatch(text)
            if conditional:
                body = self._child_block(indentation, location)
                statements.append(Statement(
                    kind="conditional",
                    location=location,
                    condition=self._expression(conditional.group(1), location),
                    body=tuple(body),
                ))
                continue

            local = _LET.fullmatch(text)
            if local:
                name, value = local.groups()
                statements.append(Statement(
                    kind="let",
                    location=location,
                    name=name,
                    expression=self._expression(value, location),
                ))
                continue

            assignment = _ASSIGNMENT.fullmatch(text)
            if assignment:
                name, raw_indices, value = assignment.groups()
                indices = tuple(
                    self._expression(part, location)
                    for part in split_top_level(raw_indices)
                ) if raw_indices is not None else ()
                statements.append(Statement(
                    kind="assignment",
                    location=location,
                    name=name,
                    target_indices=indices,
                    expression=self._expression(value, location),
                ))
                continue

            self._error(location, f"unrecognized statement: {text}")
        return statements

    def _child_block(self, parent_indent: int, location: SourceLocation) -> list[Statement]:
        if self.index >= len(self.lines) or self.lines[self.index][0] <= parent_indent:
            self._error(location, "expected an indented block")
        child_indent = self.lines[self.index][0]
        return self._block(child_indent)

    def _expression(self, source: str, location: SourceLocation) -> Expression:
        expression = Expression(source.strip(), location)
        try:
            parse_expression(expression)
        except ExpressionError as error:
            self._error(location, str(error))
        return expression

    def _error(self, location: SourceLocation, message: str) -> None:
        raise BrainCodeSyntaxError(
            f"{location.source}:{location.line}: {message}"
        )


def parse_source(source: str, source_name: str = "<string>") -> Program:
    return _Parser(source, source_name).parse()
