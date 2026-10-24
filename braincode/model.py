"""Typed syntax tree for the BrainCode source language."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SourceLocation:
    source: str
    line: int
    column: int = 1


@dataclass(frozen=True)
class Expression:
    source: str
    location: SourceLocation


@dataclass(frozen=True)
class Statement:
    kind: str
    location: SourceLocation
    name: str | None = None
    target_indices: tuple[Expression, ...] = ()
    expression: Expression | None = None
    condition: Expression | None = None
    bindings: tuple[str, ...] = ()
    collection: str | None = None
    dimensions: tuple[Expression, ...] = ()
    value_type: str | None = None
    body: tuple[Statement, ...] = ()
    boundary: str | None = None


@dataclass(frozen=True)
class Program:
    source: str
    statements: tuple[Statement, ...]
    source_name: str = "<string>"
    declarations: dict[str, Statement] = field(default_factory=dict)
