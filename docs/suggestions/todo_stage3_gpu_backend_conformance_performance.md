# TODO — Stage 3: GPU backend, conformance, and performance

Stage 3 implements GPU execution for useful workloads. The serial Python
runtime remains the semantic reference.

## Backend and scope

- Select a small, high-value subset such as regular population updates and
  stencil computations.
- Define capability reporting and explain when a model cannot run on the GPU.
- Provide explicit CPU fallback where appropriate.
- Keep data resident on the device across ticks where possible.

## Correctness and numeric behavior

- Run shared conformance cases against the Python and GPU implementations.
- Preserve documented synchronous update and write-conflict semantics.
- Specify supported numeric types, precision, reduction ordering, and any
  permitted differences.
- Make reproducibility guarantees explicit per backend and execution mode.

## Performance evidence

- Benchmark representative workload sizes, including transfer and compilation
  costs separately from execution time.
- Measure memory consumption and device limits.
- Report scaling and speedup against the serial Python reference.
- Expand backend coverage only when examples and measured benefits justify it.

Massive parallel execution is the target; actual speedup depends on model
structure, workload size, hardware, and backend capability.
