# Stage 1 suggestion: Prepare for massive parallelism

Massive parallelism is a BrainCode product target. Stage 1 should make that
target concrete and prepare the Python implementation to serve as its
correctness reference. It should not claim that the current serial Python
runtime already runs in parallel.

## Stage 1 preparation

- Specify which rule patterns are independent and which dependencies prevent
  parallel execution.
- Define deterministic write-conflict and reduction semantics.
- Keep the intermediate representation and runtime boundaries suitable for
  more than one backend without adding a GPU implementation now.
- Add representative population/tensor workloads and correctness tests.
- Establish serial timing and memory baselines in Python for those workloads.
- Document numerical behavior that a parallel backend must preserve or
  explicitly qualify.

The `parallel` keyword describes the intended iteration domain and synchronous
semantics in the current language; the reference runtime executes those
iterations serially.

## Later-stage handoff

Stage 3 should use the Stage 1 conformance suite and benchmarks to choose a
bounded GPU subset, measure scaling and transfer costs, and show any numeric
differences. Massive parallelism is the target; efficient acceleration remains
workload- and backend-dependent.
