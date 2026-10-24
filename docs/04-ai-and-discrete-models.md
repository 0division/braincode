# BrainCode: AI-Assisted Programming and Discrete Models

## AI as a potential target audience

BrainCode might be interesting for AI-assisted program synthesis because it aims to provide a bounded, explicit language for a focused class of tasks:

- named state;
- discrete ticks;
- explicit historical dependencies;
- synchronous rules;
- machine-checkable programs.

A small grammar can reduce the number of available constructs. Explicit temporal dependencies could also make static checking, error localization, and repair easier.

Using a compact custom syntax with familiar expression forms and callable Python host functions could lower the barrier for AI systems trained on Python while retaining a restricted, verifiable model language. That benefit is still a hypothesis: the compiler must distinguish BrainCode expressions from arbitrary host-language behavior.

This is a **research hypothesis**, not a demonstrated competitive advantage. A compact syntax alone does not make AI output correct. The language also needs formal semantics, clear diagnostics, executable tests, and useful interfaces.

## Requirements for an AI-friendly language

If AI generation is an important goal, BrainCode should provide:

1. **A small, unambiguous grammar:** no implicit ordering or hidden state changes.
2. **Machine-readable diagnostics:** error code, source location, affected name, and concrete cause.
3. **Validation before execution:** syntax, type, initialization, and conflict checks.
4. **A stable formatter and AST:** programs can be normalized, compared, and edited precisely.
5. **Deterministic tests:** the same inputs produce the same expected frames.
6. **Safe host access:** generated programs can use only explicitly approved functions and actions.
7. **Explainable traces:** the runtime can show the rule and historical values used to compute a value.

## Suggested evaluation

A fair evaluation should compare BrainCode with at least one host-language baseline, rather than measuring syntax preference alone.

Possible study design:

- a defined set of discrete modeling tasks with reference tests;
- the same AI model, prompt information, and comparable tool support;
- metrics such as test pass rate, required repair rounds, runtime, rule violations, and human review effort;
- tasks at multiple difficulty levels;
- published prompts, programs, and evaluation methodology.

A positive result might show that AI-generated BrainCode models for temporal tasks are more reliable to validate or easier to repair. If an ordinary host language performs as well or better, that is an important result and a reason to narrow BrainCode's intended advantage.

## “Discrete intelligence”: a cautious framing

The phrase “discrete intelligence” has not yet been defined. BrainCode can initially provide infrastructure for discrete, time-dependent state models. That does not imply that a model is intelligent.

For the term to become scientifically useful, it needs answers to questions such as:

- What qualifies as a discrete model, and at what timescale?
- Which capabilities or observable criteria count as “intelligence” here?
- How does the approach differ from finite-state machines, agent-based models, rule systems, cellular automata, and other discrete systems?
- Which tasks demonstrate an advantage beyond a change in terminology?

Until these questions are answered, “discrete intelligence” should be described as a possible research direction, not a product claim or promise.

## Relationship to parallelism

AI-friendliness and parallel execution are separate questions. An AI may generate a program in a declarative language without that program running on parallel hardware. Conversely, a runtime may later parallelize independent nodes in a correct BrainCode graph.

Recommended sequence:

1. define synchronous rule semantics;
2. build a deterministic reference runtime;
3. analyze dependencies;
4. compare a parallel backend against the same conformance tests.

## Working hypothesis

> BrainCode could improve AI-assisted development of discrete temporal models by making time dependencies explicit, programs verifiable, and state histories inspectable.

This statement is concrete and testable. It is more defensible than claiming that AI will program BrainCode especially well merely because its syntax is compact.
