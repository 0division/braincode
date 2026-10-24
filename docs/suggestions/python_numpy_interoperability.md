# Cross-cutting suggestion: Python API and NumPy interoperability

Make BrainCode easier to use from Python programs and define a deliberate,
optional interchange path for NumPy arrays. This proposal builds on the
Python API that already exists; it does not imply that BrainCode currently
executes through NumPy or that NumPy integration would make execution faster.

## Current foundation

The `braincode` package already exports `compile_source`, `compile_file`,
`Runtime`, and `run`. Python callers can also provide named host functions
for BrainCode expressions. The proposal is to document and refine this
embedding workflow and, if useful, add tested array conversion helpers.

## Candidate work

- Document a typical Python-hosted workflow: compile once, supply parameters,
  initial state and tick inputs, run, and consume results.
- Clarify how registered Python host functions are called, their expected
  determinism and side-effect behavior, and the limits they place on backend
  portability.
- Consider optional NumPy adapters for converting arrays at the Python API
  boundary for initial state, inputs, and results.
- Specify shape and dtype validation, conversion errors, ownership and copy
  behavior, and whether arrays are copied or exposed as views. Do not make
  these semantics implicit.
- Keep NumPy an optional dependency and preserve a standard-library-only
  installation and runtime path.
- Add tests for supported dtypes and shapes, invalid arrays, and parity with
  equivalent list-based inputs and outputs.

## Separate interoperation from acceleration

Passing NumPy arrays to or from the existing serial runtime is data
interoperability; it is not a vectorized NumPy execution backend. A future
NumPy-backed backend would be a separate design and performance project. It
would need to map supported BrainCode operations to array operations, preserve
the synchronous update and write-conflict contract, define numeric behavior,
and demonstrate value against comparably optimized alternatives.

Keep the initial API surface small. Add an adapter only where it removes
meaningful friction for Python users, and make unsupported conversions fail
clearly rather than silently changing types or shapes.
