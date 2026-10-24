# BrainCode: Further Concept Improvements

This document records design improvements and remaining gaps. Core temporal, population, tensor, boundary, and reduction behavior is now implemented by the v0.2 reference runtime; recommendations below concern its limits and future evolution.

## 1. Make the central promise more specific

The current concept combines several ideas:

- synchronous state updates;
- explicit historical access;
- replay and inspection;
- massive parallelism;
- AI-assisted program generation;
- “discrete intelligence.”

These ideas are related, but none automatically implies the others. The strongest near-term definition is:

> BrainCode is a declarative language for discrete-time state-transition models with explicit delayed dependencies and inspectable execution history.

Treat parallel execution as a possible implementation strategy and AI-generated modeling as an evaluation hypothesis. Keep “discrete intelligence” as a research question until it has an operational definition and a demonstrable use case.

## 2. Define what is parallel

The current scalar signal model allows rules to be evaluated independently when they read only prior frames. That defines synchronous semantics, but it does not yet explain where “massive” parallelism comes from.

To express data-parallel models, BrainCode now has first-class constructs for:

- populations and tensors;
- a shared `each ... parallel` rule over elements;
- per-element indices and local `let` values;
- explicit neighborhood access and boundary policies;
- serial deterministic reductions and write-conflict checks.

The [example collection](./examples/README.md) includes small executable conformance cases and larger O(N), O(N^2), and O(N^3) workload sketches. The Python backend currently runs serially; actual acceleration and performance comparisons remain future work.

## 3. Keep state dependencies delayed

The design decision is to forbid same-tick reads of computed state, so every state rule reads only committed prior frames. This gives a simple, race-free update model. An expression may still perform a reduction or call a pure function over values from that prior frame; the restriction is about reading newly computed state, not about the internal operations of an expression.

This is a consequential design choice: every dependency on another computed state adds at least one tick of latency. Compute-heavy operations such as matrix products should be expressed as reductions over prior-frame input/state, not as a path for reading another rule's uncommitted output.

If an application needs a multi-stage computation, model the stages across ticks or execute them as an explicitly separate host/backend operation whose result is supplied as a later tick input. Do not introduce implicit same-tick dependencies.

## 4. Separate state, input, and action

The concept currently uses “variable,” “signal,” “input,” and side-effect call in overlapping ways. Define three distinct categories:

1. **State signals** are calculated and stored in each committed frame.
2. **Inputs** are supplied externally for a specific tick and recorded for replay.
3. **Actions** are requests for effects outside the model and run only after commit.

This separation improves determinism, makes replay meaningful, and helps prevent generated programs from invoking arbitrary host capabilities.

## 5. Specify initialization as a first-class operation

Examples currently rely on implicit startup assumptions or conditional expressions that read history only after the initial ticks. Define how a model declares initial frames and when ordinary rules begin.

Possible approaches include explicit seed values per signal or a host-provided initial frame. Whichever is chosen, the specification should answer:

- Is every state signal required in the initial frame?
- Can a signal have a multi-tick initial history?
- Are inputs available at tick zero?
- Does a rule execute at tick zero, or only after initialization?
- What exact error is raised when a required historical value is missing?

Explicit initialization is preferable to silent zero-fill because it keeps model intent and startup errors visible.

## 6. Establish a small, portable value system

The current concept uses integers, floats, booleans, strings, and host-language functions without defining supported values. A portable runtime needs a minimum value model.

For an initial version, define:

- integer and floating-point behavior, including overflow and division;
- booleans and conditional expressions;
- strings only where needed for labels or actions;
- whether compound values, arrays, and user-defined records are out of scope;
- type checking rules and where errors are reported.

Do not inherit host-language behavior accidentally. If BrainCode is intended to run in multiple hosts, its observable arithmetic and comparison semantics must be specified independently.

## 7. Bound resource use and execution

The TVB can grow with every tick, and a delay can request arbitrarily old history. A runtime should expose limits rather than unexpectedly consume unbounded memory or time.

The specification and implementation should eventually define:

- maximum tick count or explicit run termination;
- maximum delay and required retained-history window;
- optional full-trace versus bounded-history modes;
- limits for model size, evaluation steps, and action volume;
- clear diagnostics when a configured budget is exceeded.

For the first prototype, document that full history is intended for short development runs and keep the runtime's storage interface replaceable.

## 8. Make determinism and parallel execution measurable

The language should define deterministic results first, then treat parallel execution as an optimization that must conform to those results.

Useful requirements:

- repeated runs with identical program, initial frame, and input log produce identical frames;
- action ordering is defined and separate from state evaluation;
- reductions specify ordering or use operations whose result is order-independent;
- serial and parallel backends pass the same conformance suite;
- performance claims are backed by benchmarks on representative workloads.

Floating-point reductions deserve particular care because different evaluation orders can produce different rounded results.

## 9. Design for inspection, not only storage

The TVB is more valuable if users and tools can ask why a value exists, not merely retrieve it. A future trace format should be able to record:

- signal and tick;
- rule location or stable rule identifier;
- historical values and inputs used;
- action events emitted;
- validation and runtime diagnostics.

This explainability would support manual debugging and could be especially useful for validating AI-generated models. It should remain optional because detailed traces can be expensive.

## 10. Use examples as executable specification

Each example should state its initial frame and expected output. Once the parser exists, the same examples should become conformance tests rather than illustrative prose only.

The examples added in [`examples/`](./examples/README.md) distinguish between:

- syntax drafts using the currently preferred notation but awaiting a parser;
- proposed population/tensor extensions, which intentionally demonstrate features not yet defined by the core grammar.

This avoids accidentally presenting speculative syntax as a supported feature.

## Suggested priority

| Priority | Improvement | Why it comes first |
| --- | --- | --- |
| 1 | Define tick, initialization, delay, and update semantics | Required for any compatible runtime |
| 2 | Separate state signals, inputs, and actions | Required for determinism and replay |
| 3 | Define value types and diagnostics | Required for a portable, testable language |
| 4 | Build small executable examples and conformance tests | Turns the concept into falsifiable behavior |
| 5 | Benchmark a population-scale target model | Tests the “massive parallelism” motivation |
| 6 | Evaluate AI-generated models against a baseline | Tests the AI-friendliness hypothesis |
| 7 | Add bounded storage, replay, and parallel backends | Runtime features after semantics stabilize |

## Questions for the next design pass

1. Is BrainCode's core unit a scalar signal, an entity, or both?
2. Which population-scale example best represents the intended parallelism?
3. Should a BrainCode model be self-contained, or depend on a host-provided initial frame and inputs?
4. Which value types are essential for the first useful implementation?

The implementation plan should be updated after these questions are answered, rather than silently choosing semantics in code.
