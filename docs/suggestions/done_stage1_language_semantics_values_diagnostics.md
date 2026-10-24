# Completed Stage 1: Language semantics, values, and diagnostics

Stage 1 uses Python as the implementation host and reference runtime. Its
purpose is to make BrainCode's language contract explicit and testable before
building GUI or GPU product features.

## Specify the language contract

- Define tick, initialization, delayed reads, synchronous updates, and failed
  tick behavior.
- Keep reads against committed history; do not introduce implicit same-tick
  dependencies.
- Define the supported value types and observable arithmetic behavior rather
  than inheriting Python behavior accidentally.
- Specify what happens when history or a required input is missing.

## Support extensibility without arbitrary expression execution

BrainCode expressions should remain structured and inspectable, not become
arbitrary Python source. Keep the AST evaluator and its explicit function
registration model. Document that host-registered functions are trusted
capabilities and must be deterministic and side-effect-free when used during
state evaluation.

This is not a restriction to simple arithmetic: the expression language can
grow through explicit AST constructs and named functions with documented
semantics. General-purpose setup, I/O, and stream processing belong in host
code at the runtime boundary.

## Improve validation and errors

- Add static checks for declarations, shapes, indices, and incompatible uses
  where the information is available at compile time.
- Keep runtime checks for values that depend on host inputs or execution.
- Report source locations and actionable causes consistently.
- Add regression tests for accepted syntax and each rejected invalid case.

## Stage 1 deliverable

A versioned, documented language contract and a conformance suite are
available in [`../stage1-contract.md`](../stage1-contract.md). Declared values
and strict declaration-mode checks are implemented. Full static inference and
strict checking of legacy implicit-state programs remain follow-up work.
