# BrainCode: Vision and Scope

## In brief

BrainCode is a small embedded DSL for discrete temporal state models. It makes state transitions and access to past values explicit. A host language remains responsible for general-purpose programming, setup, and external interactions.

BrainCode is not primarily intended to be the most convenient general-purpose language for people to write by hand. Its intended value is concise expression of temporal dependencies and systematic inspection of state. A compact grammar might also help AI systems generate and validate programs, but this needs to be tested.

## The problem

Many models represent time through mutable variables, loops, schedulers, or scattered callbacks. This makes questions harder to answer:

- Which inputs and states led to this value?
- What was a signal's value several ticks ago?
- Can the same run be reproduced or inspected at an earlier tick?
- Which parts of an update are independent?

BrainCode proposes treating time indices and synchronous state transitions as part of the model itself.

### Massive parallelism as a design target

BrainCode also targets scalable, massive parallel execution for models with
large independent populations or other data-parallel structure. Explicit
history and synchronous updates are intended to make that independence visible
to compilers and runtimes. This is a product goal, not a claim that the current
serial reference runtime already delivers parallel execution or that every
model can be parallelized efficiently.

## Core ideas

### Discrete time

A model runs over discrete ticks `T = 0, 1, 2, ...`. `~T` denotes the tick currently being computed.

### Explicit history access

`signal~N` denotes the value of `signal` at tick `T-N`. This makes a temporal dependency visible and available for analysis by a compiler or runtime.

### Synchronous state transition

All state rules for a tick should be evaluated from the same already-established historical state. Their results form a new, consistent state. A rule must not accidentally observe an intermediate value merely because it appeared later in source order.

### Traceable execution

A Time-Value Board (TVB) can record states and model inputs per tick. This supports debugging, analysis, and reproducible replay. Recording every variable on every tick is one possible debug configuration, not necessarily the only production storage strategy.

## Target applications

Possible application areas include:

- discrete simulations and agent-based models;
- time-based rules and simple synchronous control models;
- reproducible experiments with inspectable execution history;
- state models where historical queries matter more than general imperative flexibility;
- AI-generated or AI-modified model rules, provided the language offers machine-checkable programs and useful diagnostics.

These are hypotheses. A compelling use case should eventually be compared with existing tools using a concrete example.

## What BrainCode does not promise

- **Massive parallelism is a target, not an automatic guarantee:** BrainCode is intended to expose large-scale data parallelism and support runtimes that exploit it. Real execution and speedup depend on the program's dependency structure, operations, workload size, hardware, and selected backend. The current Python reference runtime is serial.
- **No inherent intelligence:** A language does not create intelligence by itself. “Discrete intelligence” may describe a research direction for discrete temporal models, but it is not yet a precise definition or a demonstrated result.
- **Not a general-purpose replacement:** The host remains responsible for arbitrary algorithms, I/O, and integrations.
- **No free time travel:** Historical queries are not the same as arbitrary rollback, changing the past, and recomputing. Replay requires controlled inputs and side effects.
- **No proven AI advantage:** A compact grammar might benefit AI programming. This needs evaluation on real tasks, with error rates and fair baselines.

## Target audiences

1. Developers of discrete models that need explicit historical access and synchronized updates.
2. Runtime developers who want to execute declarative state graphs deterministically, and possibly in parallel later.
3. Researchers studying AI-generated programs for bounded temporal modeling tasks.

Human readability still matters: people need to review the specification, diagnostics, tests, and AI-generated output, even if making the language maximally pleasant to write by hand is not the primary goal.

## Product principle

BrainCode should remain small. New syntax is justified only when it expresses one of the core properties — explicit discrete time, synchronous state transitions, or inspectable history — more clearly than an idiom in the host language.

## Success criteria for the concept

The concept becomes more credible if a prototype can demonstrate that:

1. the same inputs and configuration produce the same state history;
2. past values can be queried unambiguously and as expected;
3. errors such as missing initial history or conflicting assignments are reported clearly;
4. a non-trivial example is compared with host-language alternatives;
5. at least one representative data-parallel workload demonstrates measured scaling or speedup on an accelerated backend, compared with the serial reference;
6. an AI produces correct programs for a defined task more often, or repairs them more easily, than with a fair baseline.
