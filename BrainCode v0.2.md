# BrainCode v0.2

> A Hybrid Neuro-Temporal Language for Sequential Hosts and Parallel Temporal State

## 1. Conceptual Summary

BrainCode v0.2 is a temporal, embedded domain-specific language designed to run inside a standard sequential host such as Python. Its purpose is not to replace the host language, but to augment it with a compact, declarative layer for time-aware computation.

The central idea is simple:

- the host language handles setup, external I/O, and ordinary imperative logic;
- BrainCode defines a graph of synchronous, parallel state updates over time;
- each time step computes a new state from the previous one and from explicitly declared temporal access patterns.

In other words, BrainCode treats time as first-class state, instead of as a side effect of loops or callbacks.

---

## 2. Core Design Goals

BrainCode v0.2 is designed around five core principles:

1. Host-language interoperability
   - It should fit naturally into Python, JavaScript, or another host runtime.
2. Temporal locality
   - Variables can refer to their own or others' previous values using explicit temporal operators.
3. Parallel semantics
   - All BrainCode assignments within a time step are conceptually simultaneous.
4. Debuggability
   - The history of each variable is preserved in a temporal state board for inspection and replay.
5. Operational clarity
   - The language should remain small, readable, and close to existing programming patterns.

---

## 3. Execution Model

BrainCode is evaluated inside a simulated runtime loop. At each tick:

1. the host runtime prepares the current environment;
2. BrainCode reads required historical values from the temporal state;
3. all active assignments are evaluated as a parallel update set;
4. the resulting state is committed to the next time slice;
5. side effects may be emitted conditionally as actions.

This creates a model similar to a synchronous dataflow graph with a temporal memory.

---

## 4. Host Language Integration

The host language remains the primary environment for:

- initialization constants;
- helper functions;
- input/output;
- external libraries;
- orchestration and user interaction.

BrainCode variables are not independent runtime interpreters; they are a temporal layer over the host environment.

Example:

```python
# Host-side initialization
WEIGHT_A = 0.5
TIME_LIMIT = 50


def complex_filter(data_in):
    return data_in * 2
```

This setup feeds the temporal graph, but the graph itself is defined by BrainCode constructs.

---

## 5. Temporal Access Model

The most important innovation in BrainCode is explicit temporal access.

### 5.1 Current time

```text
~T
```

`~T` represents the current global time step.

### 5.2 Past access

```text
var~N
```

This means: "the value of `var` from `N` time steps in the past." This is the key operator that transforms ordinary stateful code into a temporal graph.

Examples:

```text
counter~1
fib~2
pos~3
```

This is conceptually similar to delayed or recursive signal access, but implemented in a simple and explicit form.

---

## 6. BrainCode Syntax

### 6.1 Simultaneous assignment

```text
:[variable] := expression
```

This defines how a variable evolves in the next time step.

Example:

```python
:pos := pos~1 + vel~1
```

Interpretation:

- current position is computed from the previous position and previous velocity;
- the assignment is part of a temporally synchronized update set.

### 6.2 Conditional blocks

```text
?(condition):
    ...parallel actions...
```

A conditional block executes only when the condition holds for the current time step.

Example:

```python
?(counter~1 > 1000):
    :counter := 0
    !(print("Counter reset triggered."))
```

This allows system control logic and effects to be expressed in a compact temporal style.

### 6.3 Side-effect actions

```text
!(call_name(arguments))
```

This represents a side effect such as logging, display, or file output. It must be used inside a conditional block, ensuring that side effects are temporally gated.

Example:

```python
?(~T % 5 == 0):
    !(print(f"[~T] Counter value: {counter~1}"))
```

---

## 7. Semantics of Parallelism

A BrainCode program is conceptually evaluated as a set of simultaneous updates.

This means:

- all assignments in a time step are computed from the same prior state;
- no assignment is allowed to observe another assignment in the same step unless the runtime explicitly models it as a chained dependency;
- the result is a synchronized next-state snapshot.

This mirrors the model of synchronous systems, where all state transitions are computed relative to the same instant in time.

---

## 8. Time-Value Boards (TVB)

The Time-Value Board is the memory model that makes BrainCode traceable and replayable.

It is a temporal ledger that records the values of variables at each tick.

### Example

| Time | counter | pos | fib | log_flag |
| --- | ---: | ---: | ---: | ---: |
| T=0 | 0 | 10.0 | 0 | False |
| T=1 | 1 | 10.5 | 1 | False |
| T=2 | 2 | 11.5 | 1 | False |
| T=3 | 3 | 12.5 | 2 | False |
| T=4 | 4 | 13.5 | 3 | True |

This board supports:

- debugging;
- history-aware logic;
- replay of execution traces;
- temporal analysis after the fact.

More importantly, it gives BrainCode a reliable mechanism for supporting expressions like `fib~2` and `counter~1` without magical hidden state.

---

## 9. Programming Example: Hybrid Counter

```python
# Host setup
start_value = 0

# BrainCode temporal graph
:counter := counter~1 + 1

?(~T % 5 == 0):
    !(print(f"[~T] Counter value: {counter~1}"))
    :log_flag := True

?(counter~1 > 1000):
    :counter := 0
    !(print("Counter reset triggered."))
```

Behavior:

- each tick increments the counter;
- every fifth tick logs the state;
- if the counter exceeds 1000, it resets while emitting a notification.

---

## 10. Programming Example: Fibonacci Sequence

```python
:fib := 0 if ~T == 0 \
    else 1 if ~T == 1 \
    else fib~1 + fib~2

?(~T == 10):
    !(print(f"Fibonacci at T=10 is: {fib~1}"))
    !(stop_simulation())
```

The value of `fib` at any time is computed from its two previous values, which makes the recurrence explicit and temporally grounded.

---

## 11. Why this is useful

BrainCode v0.2 is especially strong in domains where time is part of the computation itself:

- simulation systems;
- temporal control loops;
- signal processing;
- reactive systems;
- debugging and forensic analysis of state transitions;
- introspection of deeply stateful systems.

It is not trying to be a full standalone programming language; it is a temporal extension layer that makes history and synchrony explicit.

---

## 12. Refined Design Statement

BrainCode v0.2 can be described as:

"A small temporal DSL embedded in a host programming language, where state updates are expressed as synchronous assignments over time, historical access is explicit via delay operators, and runtime behavior is captured in a temporal board for analysis and replay."

This is more precise than v0.1 because it clarifies the purpose, semantics, and operational role of the language.

---

## 13. Summary

BrainCode v0.2 improves on the original concept by making the core model clearer:

- time is explicit and first-class;
- assignments are parallel and synchronous at each tick;
- history is recorded and queryable;
- host-language integration remains clean and practical;
- reasoning about temporal systems becomes easier and more direct.

This version is more conceptually stable, easier to explain, and better suited to implementation in a real runtime.
