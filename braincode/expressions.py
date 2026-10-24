"""Safe parsing and evaluation of BrainCode expressions."""

from __future__ import annotations

import ast
import math
import re
import operator
from collections.abc import Callable, Iterator, Mapping
from typing import Any

from braincode.model import Expression


class ExpressionError(ValueError):
    """An invalid or unsupported BrainCode expression."""


_BINARY_OPERATORS: dict[type[ast.operator], Callable[[Any, Any], Any]] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPERATORS: dict[type[ast.unaryop], Callable[[Any], Any]] = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
    ast.Not: operator.not_,
}
_COMPARE_OPERATORS: dict[type[ast.cmpop], Callable[[Any, Any], bool]] = {
    ast.Eq: operator.eq,
    ast.NotEq: operator.ne,
    ast.Lt: operator.lt,
    ast.LtE: operator.le,
    ast.Gt: operator.gt,
    ast.GtE: operator.ge,
}


def _elementwise(
    operation: Callable[[Any, Any], Any], left: Any, right: Any
) -> Any:
    if isinstance(left, (list, tuple)) or isinstance(right, (list, tuple)):
        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            if len(left) != len(right):
                raise ExpressionError("vector operands must have matching lengths")
            result = [_elementwise(operation, a, b) for a, b in zip(left, right)]
        elif isinstance(left, (list, tuple)):
            result = [_elementwise(operation, item, right) for item in left]
        else:
            result = [_elementwise(operation, left, item) for item in right]
        return tuple(result) if isinstance(left, tuple) else result
    return operation(left, right)


def _sum(values: Any, start: Any = 0) -> Any:
    result = start
    for value in values:
        result = _elementwise(operator.add, result, value)
    return result


_PURE_FUNCTIONS: dict[str, Callable[..., Any]] = {
    "abs": abs,
    "all": all,
    "any": any,
    "bool": bool,
    "float": float,
    "int": int,
    "len": len,
    "max": max,
    "min": min,
    "round": round,
    "range": range,
    "sum": _sum,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "exp": math.exp,
    "log": math.log,
    "floor": math.floor,
    "ceil": math.ceil,
}


def split_top_level(text: str, separator: str = ",") -> list[str]:
    parts: list[str] = []
    start = 0
    depth = 0
    quote: str | None = None
    escaped = False
    for index, char in enumerate(text):
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == separator and depth == 0:
            parts.append(text[start:index].strip())
            start = index + 1
    tail = text[start:].strip()
    if tail or parts:
        parts.append(tail)
    return parts


def _read_balanced(text: str, start: int, opening: str, closing: str) -> tuple[str, int]:
    depth = 0
    quote: str | None = None
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if quote is not None:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
        elif char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start + 1:index], index + 1
    raise ExpressionError(f"Unclosed {opening!r} in expression")


def _rewrite_braincode(source: str) -> str:
    result: list[str] = []
    index = 0
    while index < len(source):
        char = source[index]
        if char in {"'", '"'}:
            start = index
            quote = char
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
        if source.startswith("for", index) and (
            index == 0 or not (source[index - 1].isalnum() or source[index - 1] == "_")
        ):
            match = re.match(r"for\s+:([A-Za-z_]\w*)\s+in\b", source[index:])
            if match is not None:
                result.append(f"for __bc_{match.group(1)} in")
                index += len(match.group(0))
                continue
        if char != ":" or index + 1 >= len(source) or not (
            source[index + 1].isalpha() or source[index + 1] == "_"
        ):
            result.append(char)
            index += 1
            continue

        end = index + 2
        while end < len(source) and (source[end].isalnum() or source[end] == "_"):
            end += 1
        name = source[index + 1:end]
        indices: list[str] = []
        if end < len(source) and source[end] == "[":
            raw_indices, end = _read_balanced(source, end, "[", "]")
            indices = split_top_level(raw_indices)
        delay: int | None = None
        if end < len(source) and source[end] == "~":
            match = re.match(r"~(\d+)", source[end:])
            if match is None:
                raise ExpressionError("A history delay must be a positive integer")
            delay = int(match.group(1))
            if delay < 1:
                raise ExpressionError("A history delay must be at least 1")
            end += len(match.group(0))

        index_tuple = ", ".join(_rewrite_braincode(item) for item in indices)
        if len(indices) == 1:
            index_tuple += ","
        if delay is not None:
            result.append(f'__bc_history__("{name}", {delay}, ({index_tuple}))')
        elif indices:
            result.append(f'__bc_index__("{name}", ({index_tuple}))')
        else:
            result.append(f'__bc_symbol__("{name}")')
        index = end
    return "".join(result)


def parse_expression(expression: Expression) -> ast.Expression:
    try:
        parsed = ast.parse(_rewrite_braincode(expression.source), mode="eval")
    except (SyntaxError, ExpressionError) as error:
        raise ExpressionError(
            f"{expression.location.source}:{expression.location.line}: "
            f"invalid expression: {error}"
        ) from error
    _validate_node(parsed.body)
    return parsed


def _validate_node(node: ast.AST) -> None:
    allowed = (
        ast.Constant, ast.Name, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
        ast.IfExp, ast.Call, ast.Tuple, ast.List, ast.GeneratorExp, ast.Load,
        ast.Store, ast.keyword, ast.comprehension, ast.Add, ast.Sub, ast.Mult, ast.Div,
        ast.FloorDiv, ast.Mod, ast.Pow, ast.UAdd, ast.USub, ast.Not, ast.And,
        ast.Or, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    )
    for child in ast.walk(node):
        if not isinstance(child, allowed):
            raise ExpressionError(
                f"unsupported expression syntax: {type(child).__name__}"
            )
        if isinstance(child, ast.Call) and not isinstance(child.func, ast.Name):
            raise ExpressionError("only named pure functions can be called")
        if isinstance(child, ast.comprehension) and (child.is_async or child.ifs):
            if child.is_async:
                raise ExpressionError("asynchronous comprehensions are unsupported")
            if child.ifs:
                continue
        if isinstance(child, ast.GeneratorExp) and len(child.generators) != 1:
            raise ExpressionError("only a single generator clause is supported")


def expression_to_data(expression: Expression) -> dict[str, Any]:
    tree = parse_expression(expression)

    def encode(node: Any) -> Any:
        if isinstance(node, ast.AST):
            return {
                "node": type(node).__name__,
                **{
                    name: encode(value)
                    for name, value in ast.iter_fields(node)
                },
            }
        if isinstance(node, list):
            return [encode(item) for item in node]
        if isinstance(node, tuple):
            return [encode(item) for item in node]
        return node

    return {
        "source": expression.source,
        "location": {
            "source": expression.location.source,
            "line": expression.location.line,
            "column": expression.location.column,
        },
        "tree": encode(tree.body),
    }


def evaluate_expression(
    expression: Expression,
    *,
    symbols: Mapping[str, Any],
    locals_: Mapping[str, Any],
    read_symbol: Callable[[str], Any],
    read_index: Callable[[str, tuple[Any, ...]], Any],
    read_history: Callable[[str, int, tuple[Any, ...]], Any],
    functions: Mapping[str, Callable[..., Any]] | None = None,
) -> Any:
    tree = parse_expression(expression)
    available_functions = dict(_PURE_FUNCTIONS)
    if functions:
        available_functions.update(functions)

    def evaluate(node: ast.AST, scope: dict[str, Any]) -> Any:
        if isinstance(node, ast.Constant):
            return node.value
        if isinstance(node, ast.Name):
            if node.id.startswith("__bc_"):
                name = node.id[5:]
                if name in scope:
                    return scope[name]
                raise ExpressionError(f"undefined local variable {name!r}")
            if node.id in scope:
                return scope[node.id]
            if node.id in symbols:
                return symbols[node.id]
            if node.id in {"True", "False", "None"}:
                return {"True": True, "False": False, "None": None}[node.id]
            raise ExpressionError(f"undefined name {node.id!r}")
        if isinstance(node, ast.Tuple):
            return tuple(evaluate(item, scope) for item in node.elts)
        if isinstance(node, ast.List):
            return [evaluate(item, scope) for item in node.elts]
        if isinstance(node, ast.UnaryOp):
            operation = _UNARY_OPERATORS.get(type(node.op))
            if operation is None:
                raise ExpressionError("unsupported unary operator")
            return operation(evaluate(node.operand, scope))
        if isinstance(node, ast.BinOp):
            operation = _BINARY_OPERATORS.get(type(node.op))
            if operation is None:
                raise ExpressionError("unsupported arithmetic operator")
            return _elementwise(
                operation, evaluate(node.left, scope), evaluate(node.right, scope)
            )
        if isinstance(node, ast.BoolOp):
            if isinstance(node.op, ast.And):
                value: Any = True
                for item in node.values:
                    value = evaluate(item, scope)
                    if not value:
                        return value
                return value
            value = False
            for item in node.values:
                value = evaluate(item, scope)
                if value:
                    return value
            return value
        if isinstance(node, ast.Compare):
            left = evaluate(node.left, scope)
            for operation_node, comparator in zip(node.ops, node.comparators):
                operation = _COMPARE_OPERATORS.get(type(operation_node))
                right = evaluate(comparator, scope)
                if operation is None or not operation(left, right):
                    return False
                left = right
            return True
        if isinstance(node, ast.IfExp):
            branch = node.body if evaluate(node.test, scope) else node.orelse
            return evaluate(branch, scope)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {
                "__bc_symbol__", "__bc_index__", "__bc_history__"
            }:
                function_name = node.func.id
                args = [evaluate(item, scope) for item in node.args]
                if function_name == "__bc_symbol__":
                    if args[0] in scope:
                        return scope[args[0]]
                    if args[0] in symbols:
                        return symbols[args[0]]
                    return read_symbol(args[0])
                if function_name == "__bc_index__":
                    return read_index(args[0], args[1])
                return read_history(args[0], args[1], args[2])
            if not isinstance(node.func, ast.Name):
                raise ExpressionError("only named pure functions can be called")
            function = available_functions.get(node.func.id)
            if function is None:
                raise ExpressionError(f"function {node.func.id!r} is not registered")
            args = [evaluate(item, scope) for item in node.args]
            kwargs = {
                keyword.arg: evaluate(keyword.value, scope)
                for keyword in node.keywords
                if keyword.arg is not None
            }
            return function(*args, **kwargs)
        if isinstance(node, ast.GeneratorExp):
            generator = node.generators[0]
            if not isinstance(generator.target, ast.Name):
                raise ExpressionError("generator target must be a single name")
            iter_values = evaluate(generator.iter, scope)

            def values() -> Iterator[Any]:
                for value in iter_values:
                    child_scope = dict(scope)
                    target_name = generator.target.id.removeprefix("__bc_")
                    child_scope[target_name] = value
                    if all(evaluate(condition, child_scope) for condition in generator.ifs):
                        yield evaluate(node.elt, child_scope)

            return values()
        raise ExpressionError(f"unsupported expression node {type(node).__name__}")

    return evaluate(tree.body, dict(locals_))
