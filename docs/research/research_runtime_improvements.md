# Can BrainCode Make Discrete Neural Networks Faster?

## Abstract

This document examines, without running benchmarks, whether BrainCode could
execute discrete neural-network workloads faster than programs written in
other languages. It separates properties of the language from properties of
its current runtime and from capabilities a future compiler or accelerator
could provide. The central finding is that BrainCode's synchronous,
data-parallel semantics can expose parallel work, but do not themselves
execute that work in parallel. The current implementation is a serial Python
reference runtime, so the repository does not establish a speed advantage.
A future compiled CPU or GPU backend could be competitive for sufficiently
large, regular workloads, but only if it generates efficient kernels, controls
memory traffic, and preserves the required semantics. That is a plausible
engineering hypothesis, not a demonstrated result.

## Research question and scope

**Question:** Under what conditions could BrainCode execute a discrete
neural-network model faster than an equivalent implementation in Python,
NumPy, a compiled general-purpose language, or a machine-learning framework?

This is a **non-empirical, theory-based analysis** of the implemented language
contract, compiler/runtime architecture, and established performance models.
No benchmark was run for this study, and no timing result or measured speedup
is claimed. It is not a systematic literature review. Its purpose is to
identify defensible conclusions, plausible hypotheses, and the conditions
that any future empirical study would need to test.

The term *discrete neural network* is used descriptively for models whose
state evolves in discrete steps and whose values or activation rules may be
discrete. It does not imply that every BrainCode model is a neural network, or
that such a model is intelligent.

## What BrainCode currently specifies

BrainCode rules compute a candidate next frame from committed state and
tick-indexed inputs. Rules in a transition read the same committed history;
they do not observe one another's uncommitted results. Population and tensor
rules express iteration domains, and duplicate writes are rejected. These
properties make independence within a tick easier to reason about than
implicit, order-dependent mutation in a general-purpose program.

The word `parallel` currently identifies a data-parallel iteration domain and
its synchronous semantics. It does **not** start worker threads or GPU
kernels. The only implemented execution backend is `python-serial`; population
elements are evaluated serially. See the [execution model](../02-execution-model.md)
and the [Stage 1 contract](../stage1-contract.md).

The current frontend lowers `.bc` into a structured `.bcc.json` IR, but that
fact alone does not imply native code generation. The present backend remains
the Python reference implementation. Consequently, potential parallelism in
the model is not yet the same as realized hardware parallelism.

## Theoretical performance model

Let:

- `W` be the total work required for one transition;
- `S` be the critical-path work that must remain sequential;
- `P` be the number of effective processing elements;
- `O(P, n)` be parallel scheduling, synchronization, and communication
  overhead for a workload of size `n`;
- `M` be the cost of moving data between host and device memory, where
  applicable.

An idealized parallel execution time has a lower bound of approximately
`max(W / P, S)`. A real implementation also pays overhead, so a useful
qualitative model is:

```text
T_parallel >= max(W / P, S) + O(P, n) + M
```

This is a model for reasoning, not a BrainCode timing formula. It explains
several important limits:

1. More parallel hardware helps only when there is enough independent work.
2. Sequential dependencies bound speedup even with many processors.
3. Scheduling, kernel launches, synchronization, and data movement can exceed
   the useful work for small or communication-heavy jobs.
4. A language-level declaration of independence does not remove these costs.

Amdahl's law describes the bound when only a fraction of a fixed workload can
be parallelized. Gustafson's law considers scaling the workload as more
processors are added. Both support the same practical conclusion: the
parallel fraction and workload size matter; a parallel-capable notation alone
does not predict performance [1, 2].

For memory-bound workloads, processor count is not the only limit. The
Roofline model relates achievable compute throughput to arithmetic intensity
(operations per byte moved), compute capacity, and memory bandwidth. A regular
grid update may expose many independent cells yet still be limited by
neighbor-data movement. Dense neural layers may have higher arithmetic
intensity and benefit more from optimized matrix kernels, subject to shape and
batch size [3].

## Comparison by implementation target

### Current BrainCode versus direct Python

There is no theoretical basis for expecting the current BrainCode runtime to
outperform a well-written direct Python implementation for ordinary
CPU workloads. The host is Python, and a DSL runtime must additionally
interpret model rules, resolve state/history references, validate writes, and
construct committed frames. A direct loop over simple values can avoid much
of that machinery.

This is an architectural expectation, not a measured comparison. For
particular programs, implementation details and workload shape could change
the result; this document does not claim timings.

### Current BrainCode versus NumPy or machine-learning frameworks

Vectorized numerical libraries and machine-learning frameworks can dispatch
work to optimized native CPU or GPU kernels. The current serial BrainCode
backend has no such accelerator path. For workloads already expressed as
efficient array operations or matrix multiplications, BrainCode has no
established execution-speed advantage over those systems.

A future backend would have to lower BrainCode operations to comparably
optimized kernels. Exposing an `each ... parallel` domain is not a substitute
for vectorization, kernel fusion, efficient layouts, or tuned matrix
operations.

### A possible future BrainCode compiler/backend

BrainCode may be a useful *semantic frontend* for a specialized backend:
explicit state, time delays, whole-tick synchronization, and declared
iteration domains can give a compiler facts that are difficult to recover
from arbitrary imperative code. Those facts could enable dependency analysis,
fusion of compatible operations, vectorization, or GPU mapping.

They enable optimization; they do not guarantee that an optimizer implements
it or produces code as efficient as established compilers and libraries.
Research on domain-specific languages such as Halide illustrates the
importance of compiler transformations and explicit scheduling decisions; the
performance benefit comes from the generated implementation and schedule, not
from concise syntax by itself [4].

## Workloads with plausible parallel potential

The most plausible candidates are regular workloads where many elements apply
the same rule to committed prior state:

- cellular automata and stencil updates over large grids;
- batched, element-wise state transitions;
- dense network layers with sufficiently large batches and efficient matrix
  operations;
- independent populations or samples that can be processed together.

Within a tick, the elements of such a domain may be independent. Across ticks,
however, the next frame generally depends on the previous committed frame.
Therefore, a run of `T` ticks usually has a sequential temporal dependency of
depth `T`, even if each tick contains substantial spatial or batch
parallelism. This distinction is important for recurrent or time-stepped
networks: parallelism within a step does not remove the dependency between
steps.

## Workloads with weaker or conditional prospects

- **Small populations:** fixed costs for dispatch, validation, and memory
  movement may be larger than the computation.
- **Low arithmetic intensity:** a large grid may be limited by memory
  bandwidth and neighborhood traffic rather than arithmetic throughput.
- **Irregular or highly conditional rules:** divergence, gathers, scatters, or
  uneven work may reduce accelerator utilization.
- **Sequential recurrence within a tick:** true data dependencies limit
  available parallelism.
- **Host-function-heavy rules:** crossing into Python or other host callbacks
  can block fusion and device execution unless functions are separately
  compiled and have suitable purity and capability contracts.
- **Full-history retention:** retaining every frame increases memory
  consumption with the number of ticks. Bounded history helps storage but can
  restrict later inspection and replay behavior.
- **Floating-point reductions:** the current contract defines ordered
  reductions. Tree reductions or parallel reassociation can change floating
  point results, so a faster backend may need to preserve order or document
  and test a deliberate numerical relaxation.

## Discrete neural-network-specific assessment

Discrete activations do not automatically make a network faster. Boolean or
small-integer state may reduce storage and bandwidth, but only if the backend
uses compact representations and efficient operations. The present contract
includes `Bool`, integer, and floating-point declared values, but the existence
of a type declaration does not guarantee packed storage or specialized
hardware instructions.

Some network structures map naturally to parallel computation:

- independent neurons in a layer can often compute in parallel once their
  input values are committed;
- independent input samples can be batched;
- sparse/event-driven models may avoid work when activity is sufficiently
  sparse, but only if the representation and runtime exploit that sparsity.

Other structures remain constrained:

- layer-to-layer propagation is sequential in depth for ordinary feed-forward
  evaluation;
- recurrent updates are sequential across ticks;
- dense connectivity can require substantial arithmetic and memory traffic;
- exact, deterministic reduction order may constrain parallel summation.

The repository contains neural-network workload sketches, but sketches are
not evidence of a supported, optimized neural-network implementation. In
particular, any example that uses syntax or operations marked unsupported
must not be counted as an implemented workload or a performance result.

## Conditions for a defensible speed claim

It would be scientifically reasonable to claim that BrainCode is faster only
for a precisely delimited comparison. A future study should state:

1. the exact BrainCode program, inputs, tick count, and numerical semantics;
2. the equivalent baseline implementation and whether it uses optimized
   libraries;
3. the compiler/runtime/backend versions and supported feature subset;
4. the hardware, thread/device settings, precision, and memory layout;
5. whether compile time, warm-up, data transfer, and result serialization are
   included or reported separately;
6. the workload sizes and batch sizes for which the result holds;
7. output correctness/conformance checks and any allowed numerical tolerance;
8. repeated measurements, variability, and memory consumption.

The comparison must avoid asymmetry: comparing an interpreter to optimized
GPU kernels answers whether the current implementations differ, but does not
isolate the merit of the language. Comparing a future BrainCode backend to an
equally optimized baseline is needed to support a language/backend advantage.
Both end-to-end user-visible time and kernel-only time may be useful, but they
answer different questions and should not be conflated.

## Runtime improvement implications

The theory suggests the following order of engineering work. These are design
recommendations, not measured predictions:

1. **Keep semantics precise.** Preserve committed-history reads, atomic frame
   commits, conflict detection, and declared numeric behavior as backend
   requirements.
2. **Lower rules to executable operations.** Avoid repeatedly interpreting
   expression syntax for every population element. A typed or otherwise
   normalized executable IR could make dispatch and validation costs more
   manageable.
3. **Improve data representation.** Investigate contiguous typed arrays,
   reusable frame buffers, and copy-on-write or double-buffered state where
   they preserve observable history semantics. Nested Python lists are
   flexible but do not guarantee locality or compact storage.
4. **Optimize the serial CPU path first.** Use conformance tests to guide
   expression evaluation, loop specialization, and memory traffic improvements.
   The serial backend remains the oracle even if another backend is added.
5. **Parallelize only exposed independent domains.** A CPU-parallel or GPU
   backend should map population elements to hardware only when dependencies,
   writes, reduction order, and error behavior are understood.
6. **Measure data movement and retention.** Keep state resident on an
   accelerator across ticks where possible, and make history, transfers,
   compilation, launch, and serialization costs visible to users.
7. **Treat host extensions as a boundary.** Arbitrary Python callbacks limit
   portability, fusion, and device execution. Any future compiled host
   capability needs an explicit purity, type, and backend-availability
   contract.

The main strategic choice is therefore not to promise parallelism immediately,
but to preserve a backend-independent semantic contract and evolve the
runtime from a clear reference implementation toward optimized execution in
measured steps.

## Assessment

**Is BrainCode inherently faster than other programming languages?** No.
Language syntax and temporal semantics do not, by themselves, make execution
faster. Runtime, compiler, memory representation, algorithms, libraries, and
hardware determine performance.

**Can BrainCode express workloads that a future backend can parallelize?**
Yes. Synchronous rules and explicit population domains provide a plausible
basis for identifying independent work within a tick.

**Is the current implementation a “superfast” discrete-neural-network
runtime?** No. It is a deterministic serial Python reference implementation.
No speed advantage has been established.

**Is the underlying idea unreasonable?** No. A focused, explicit language
could be a useful way to describe and validate discrete temporal models, and
could be a good target for AI-assisted authoring or specialized compilation.
Those are separate hypotheses from speed and from any claim about
intelligence. The defensible position is that BrainCode has a potentially
useful semantic model and a path toward optimized backends; its performance
advantage remains unproven.

## Conclusion

The strongest theoretical opportunity is not “BrainCode syntax runs faster,”
but “BrainCode makes certain synchronous data-parallel structures explicit,
which may let a specialized compiler map them efficiently to hardware.” That
opportunity is largest for sufficiently large, regular, compute-dense
workloads with independent elements per tick and manageable data movement. It
is smaller for tiny, irregular, callback-heavy, or strongly sequential models.

Until a compiled or accelerated backend exists and is compared fairly against
optimized alternatives, “superspeed” should be described as a research and
engineering goal—not a property of the language already demonstrated.

## References

1. Amdahl, G. M. (1967). “Validity of the Single Processor Approach to
   Achieving Large Scale Computing Capabilities.” *AFIPS Conference
   Proceedings*, 30, 483–485.
   https://doi.org/10.1109/AFIPS.1967.26
2. Gustafson, J. L. (1988). “Reevaluating Amdahl's Law.” *Communications of
   the ACM*, 31(5), 532–533.
   https://doi.org/10.1145/42411.42415
3. Williams, S., Waterman, A., & Patterson, D. (2009). “Roofline: An
   Insightful Visual Performance Model for Multicore Architectures.”
   *Communications of the ACM*, 52(4), 65–76.
   https://doi.org/10.1145/1498765.1498785
4. Ragan-Kelley, J., Adams, A., Paris, S., Levoy, M., Amarasinghe, S., &
   Durand, F. (2013). “Halide: A Language and Compiler for Optimizing
   Parallelism, Locality, and Recomputation in Image Processing.” *Proceedings
   of the 34th ACM SIGPLAN Conference on Programming Language Design and
   Implementation*, 519–530.
   https://doi.org/10.1145/2491956.2462176
