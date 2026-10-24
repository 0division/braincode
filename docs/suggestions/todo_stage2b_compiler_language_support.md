# TODO — Stage 2b: compiler-backed language support

Add editor intelligence by reusing the BrainCode compiler's language
knowledge. The extension should not grow an independent parser whose behavior
can drift from the compiler.

## Candidate features

- Source diagnostics with compiler error messages and locations.
- Completion and navigation based on declarations, rules, inputs, and
  available host symbols.
- Formatting and documentation hints that preserve BrainCode syntax and
  source locations.
- Clear diagnostics for unsupported constructs and incomplete static checks.

Prefer a small language server or a stable structured interface exposed by the
compiler. First identify which features can be supported accurately by
existing compiler APIs; extend those APIs when needed, and distinguish
compile-time diagnostics from errors that are only discoverable at runtime.

Implement features incrementally with tests that compare editor-facing
results to compiler behavior. Avoid promising full type checking,
undeclared-symbol detection, or refactorings until the compiler implements
them.
