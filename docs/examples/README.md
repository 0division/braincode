# BrainCode Examples

These `.bc` files use BrainCode's own DSL syntax; they are not Python source. The v0.2 compiler and Python reference runtime can compile and run every example with appropriate host-provided initial state and parameters. The larger workloads should be run with small dimensions on the serial reference backend.

The scalar examples use the preferred draft notation `:signal = expression`. A transition from T to T+1 reads only committed history: `:signal~1` means the value at T. Rules cannot see one another's uncommitted results. Each example's host inputs and run settings live in a sibling `.bc.in.json` file, separate from the model source.

## Scalar examples

- [counter.bc](./counter.bc) — one-step state update from an explicit initial value
- [fibonacci.bc](./fibonacci.bc) — recurrence using two historical frames
- [coupled-signals.bc](./coupled-signals.bc) — simultaneous updates from a shared prior state
- [moving-average.bc](./moving-average.bc) — delayed reads over an input signal
- [host-function-max.bc](./host-function-max.bc) — a Python `max` function exposed to a BrainCode expression
- [conditional-hold.bc](./conditional-hold.bc) — a conditional state update using the default hold behavior

## Cellular automata

- [cellular-automaton-2d-conway.bc](./cellular-automaton-2d-conway.bc) — 2D Conway Life, B3/S23, with an eight-cell Moore neighborhood
- [cellular-automaton-3d-life.bc](./cellular-automaton-3d-life.bc) — 3D B6/S567, with a 26-cell Moore neighborhood
- [cellular-automaton-1d-rule110.bc](./cellular-automaton-1d-rule110.bc) — optional 1D example with Rule 110 written directly as a BrainCode truth table

Rule 110 is not required by the language or runtime. It is included as a compact test of local-neighbor access and Boolean rule expressions; the transition is implemented directly in BrainCode and does not depend on a host helper. The 2D and 3D examples are more representative of the intended large-scale parallel workload.

The compiler output for Rule 110 is checked in as both [cellular-automaton-1d-rule110.bcc](./cellular-automaton-1d-rule110.bcc), expanded BrainCode source, and [cellular-automaton-1d-rule110.bcc.json](./cellular-automaton-1d-rule110.bcc.json), structured JSON IR. The `.bcc` source can be loaded and run directly.

## Encoding and mapping

- [unicode-to-utf8-mapper.bc](./unicode-to-utf8-mapper.bc) — maps one Unicode scalar value to one to four UTF-8 bytes

The former `ascii-to-utf8-mapper.bc` name was inaccurate: this is a Unicode scalar-value mapper, not an ASCII-only mapper. It computes each output byte position with conditional BrainCode rules, reports the encoded length, and collects only the non-null bytes in `utf8_out_bytes`. It handles the 1-, 2-, 3-, and 4-byte ranges and rejects out-of-range values and UTF-16 surrogate code points. It is a scalar code-point mapper, not a bit-vector or one-hot representation.

The example input code point is `128512` (`U+1F600`, 😀), configured in [unicode-to-utf8-mapper.bc.in.json](./unicode-to-utf8-mapper.bc.in.json). Its checked execution trace is [unicode-to-utf8-mapper.output.json](./unicode-to-utf8-mapper.output.json). Run it with:

```powershell
python -m braincode run docs/examples/unicode-to-utf8-mapper.bc --input-file docs/examples/unicode-to-utf8-mapper.bc.in.json
```

## Data-parallel workloads

- [game-of-life-large-proposal.bc](./game-of-life-large-proposal.bc) — large 2D grid; `O(width * height)` work per generation
- [three-dimensional-heat-diffusion-proposal.bc](./three-dimensional-heat-diffusion-proposal.bc) — 3D stencil; `O(width * height * depth)` work per step and very high memory demand
- [nbody-all-pairs-proposal.bc](./nbody-all-pairs-proposal.bc) — all-pairs simulation; `O(body_count^2)` interactions per tick
- [dense-matrix-multiply-proposal.bc](./dense-matrix-multiply-proposal.bc) — dense arithmetic; `O(N^3)` multiply-add terms
- [deep-network-inference-proposal.bc](./deep-network-inference-proposal.bc) — batched layered computation; cost depends on batch and layer widths

The workload suffix `-proposal` identifies a proposed modeling workload, not unsupported syntax: the current reference compiler implements the population, tensor, indexing, neighborhood, and reduction forms used in these files. Each `each ... parallel` block is evaluated serially by the reference backend while preserving data-parallel semantics. Any dynamic state consumed by an update is read from the previously committed frame. Reductions may combine values from that prior frame; they do not let a rule read another rule's newly computed result. `let name = expression` bindings are local to one element's evaluation, not temporal signals.

The workloads have different performance bottlenecks: all-pairs interactions are compute-heavy, large stencils are often memory-bandwidth-heavy, and dense matrix operations need efficient tiling and reductions. “Massive parallelism” alone will not make them fast; a runtime and backend must map each workload effectively.

The scalar syntax is `:signal = expression`; `:signal~1` reads the committed value at tick `T` while computing `T+1`, and `:signal~2` reads `T-1`. Expressions may call built-in pure functions or functions explicitly registered by the host, as illustrated by [host-function-max.bc](./host-function-max.bc). Host functions are trusted capabilities supplied by the caller; callers must ensure that functions used in state rules are pure and deterministic.

The standard-library test suite compiles all examples and runs them at small representative dimensions. It is a correctness/conformance check, not a performance benchmark.

To compile and execute every example, including both `.bcc` artifact forms, run `bash run_examples.sh` from the project root. All generated files go under `output/`: expanded BrainCode source, structured JSON IR, per-example execution traces, a JSON summary, a chronological `run.log`, and a Markdown `run-summary.md`.
