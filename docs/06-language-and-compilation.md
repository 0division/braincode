# BrainCode: Language and Compilation Model

> The v0.2 subset described here has a compiler and serial Python reference runtime. Future backend and tooling features remain proposals.

## Implemented v0.2 subset

The compiler currently parses scalar rules, delayed reads, conditions, local `let`, population/tensor declarations, indexed reads and writes, `each ... parallel`, boundaries, named function calls, and single-clause generator reductions. It emits expanded BrainCode source in `.bcc` and a versioned structured JSON IR in `.bcc.json`. Both forms can be loaded by the deterministic, serial reference runtime. Every current `.bc` example is covered by a small-scale compile/run test.

The implementation deliberately does not promise hardware parallelism. `parallel` defines a data-parallel iteration domain; the Python backend visits elements serially. Type checking, explicit `.bc` input/parameter declarations, actions, bounded history, and optimized backends remain future work. See the [implementation status and roadmap](./implementation-plan.md) for details.

The frontend is intentionally lightweight: a custom indentation-aware statement parser uses regular expressions for a few statement forms and explicit delimiter scanning for multiline input. BrainCode references are rewritten into internal nodes, then the restricted Python-like expression subset is parsed and allowlisted. This is not a full Python parser for `.bc` files, and the small current grammar does not justify introducing Flex or another generated lexer. If the grammar grows substantially—or the implementation moves to C/C++—a formal lexer/parser generator can be reconsidered.

## Language boundary

BrainCode has its own syntax. A `.bc` file is not a Python module, even though some expression syntax may intentionally resemble Python.

The project can use Python in three distinct roles:

1. **Afferent/host language:** Python prepares inputs, configures a run, and may process outputs.
2. **BrainCode language:** The custom DSL describes state transitions, history access, and eventually data-parallel operations.
3. **Efferent/backend language:** Initially Python for a portable reference backend; later a backend may target CUDA or another platform.

These roles should be explicit in configuration. Python is a host/backend choice, not the BrainCode grammar.

## Proposed project configuration

An optional `braincode.yaml` could make language roles and compilation choices visible:

See the illustrative [braincode.yaml.example](./braincode.yaml.example).

Provisional meanings:

- `braincode_afferent_language`: the host/source language used for preparation and orchestration;
- `braincode_language`: the language used to write model rules;
- `braincode_efferent_language`: the initial execution/code-generation target.

Initially, the values are `python`, `braincode`, and `python`. A later GPU backend could change the efferent target to `cuda` without changing the BrainCode source.

## Example: host code and BrainCode source

Host-side Python can prepare inputs and invoke the BrainCode compiler/runtime:

```python
from braincode import compile_file, run

initial_state = {"counter": 0}
program = compile_file("docs/examples/counter.bc")
result = run(program, initial_state=initial_state, ticks=100)
```

The `.bc` file contains BrainCode syntax, not Python:

```text
:t = max(:t~1, :t~2)
```

This example assumes `max` is available as a permitted pure host function. The compiler must parse the BrainCode structure and validate the call before execution. Here, `:t~1` is the value at `T` and `:t~2` is the value at `T-1` when the rule computes `T+1`.

## Expression syntax and Python functions

BrainCode owns its statement syntax and temporal references such as `:signal~1`. The current expression subset supports Python-like arithmetic, comparisons, Boolean operators, parentheses, named function calls, conditional expressions, and single-clause generator reductions. The frontend parses only that restricted expression subset and evaluates an allowlisted tree; it does not execute Python source. A `let name = expression` binding names an intermediate value local to one rule or population-element evaluation. It is not a state signal, is not stored in the TVB, and is not visible to other rules.

Host functions can be passed to the runtime explicitly. Built-in pure functions include `min`, `max`, `abs`, `sum`, and selected `math` operations; the compiler/runtime does not execute arbitrary Python source or use unrestricted `eval`.

Recommended initial policy:

- allow built-in pure functions such as `min`, `max`, `abs`, and selected `math` functions;
- allow additional host functions only when explicitly registered with type and purity metadata;
- keep file access, network access, mutation, randomness, and other side effects outside state expressions;
- express external values as tick-indexed inputs;
- represent side effects as explicit BrainCode actions that run after a successful state commit.

The current built-in registry includes `min`, `max`, `abs`, `sum`, `range`, basic conversions, and selected `math` functions. User functions are explicitly supplied to the runtime; their purity and argument types are not statically verified yet.

## Temporal assignment semantics

The current preferred transition model is:

- the model has a committed frame at tick `T`;
- each BrainCode rule reads only committed history and tick-indexed inputs;
- each rule computes a value for the next frame, `T+1`;
- all next-frame values are committed together;
- a rule cannot read another rule's uncommitted next-frame result.

Under this convention, while computing `T+1`:

| Reference | Reads |
| --- | --- |
| `:signal~1` | `signal[T]`, the current committed value |
| `:signal~2` | `signal[T-1]` |
| `:signal~N` | `signal[T+1-N]` |

`~T` denotes the current committed/source tick. Same-tick dependencies are intentionally unavailable in the initial model. Data-parallel population operations may still run across many elements, provided each element reads the committed previous frame.

Immutable model parameters such as a grid size or physical constant are configuration, not time-varying state. Every dynamic model/input value read by a state rule must come from an explicitly defined prior frame or tick-indexed input.

## Conditional state updates

When a conditional state update is inactive, the default behavior is to hold that state's value from the prior committed frame. An explicit alternative may later request a reset value or an error.

For example, the following conditional block updates `:heater` only when the condition is true; otherwise, the runtime carries its prior value into the next frame:

```text
?(:temperature~1 < :limit):
    :heater = True
```

The compiler rejects multiple rule sites for one target, and the runtime detects repeated indexed writes that resolve to the same element.

## Compilation pipeline

Current pipeline:

1. Read `.bc` source.
2. Parse indentation-aware statements and source locations.
3. Parse and allowlist the supported expression subset.
4. Validate population dimensions, loop bindings, indexed targets, and writer conflicts.
5. Serialize a versioned, backend-independent BrainCode IR.
6. Execute the IR with the serial Python reference backend.

The custom statement parser is responsible for BrainCode syntax. The implementation uses Python's expression AST only for its restricted expression subset. Python is also the initial host and backend; it is not the parser for the whole `.bc` file.

## Compiled artifacts

`.bcc` is generated BrainCode source, not Python source and not a platform-specific native executable. It preserves BrainCode expressions and declarations but unfolds each data-parallel loop into explicit indexed assignments. The result can be read, recompiled, and run as BrainCode. Symbolic population dimensions must be provided during compilation using `--parameters`.

`.bcc.json` is the versioned structured IR. It contains:

- artifact format, language, and IR versions;
- population/tensor declarations, rules, and boundaries;
- expression trees and source text;
- source locations for diagnostics.

Runtime parameters, initial state, and tick-indexed input frames are host-supplied and are not embedded in either artifact. The IR does not package host functions; the runtime caller supplies those capabilities when constructing a run.

Host-side Python preparation and post-processing should remain outside the portable model artifact unless a later packaging format explicitly includes them. The artifact should never contain executable Python text that is evaluated without validation.

## Execution modes

### Interactive/development mode

1. Parse `.bc` source.
2. Validate and lower it to IR.
3. Run the Python reference backend.
4. Allow the host application to inspect the state trace and process results.

### Ahead-of-time mode

1. Parse and validate `.bc` source.
2. Compile it to expanded `.bcc` source and structured `.bcc.json` IR.
3. Load the artifact with a selected backend.
4. Supply initial state and tick-indexed inputs through the host interface.

“Compile once” means the model need not be reparsed from the compact `.bc` source for each run. The expanded `.bcc` remains BrainCode; `.bcc.json` provides the structured serialization. Neither artifact includes host Python code.

## Security and reproducibility

Calling host functions from expressions is useful, but unconstrained calls can undermine both safety and reproducibility.

- Only registered functions should be callable from BrainCode.
- Functions used by state rules should be pure and deterministic.
- Inputs such as time, randomness, and sensor values should be passed explicitly for a tick.
- Side-effecting operations should use a separate action interface and execute only after commit.
- The compiler should reject unknown calls rather than silently resolving arbitrary Python globals.

## Remaining implementation work

The first compiler settles the syntax needed by the examples but is not a complete stable language specification. Remaining work includes complete static type checking, explicit declaration syntax for host inputs and parameters, numeric overflow/precision guarantees, resource budgets, a stable host-function capability API, and optimized backends. The illustrative YAML file does not yet configure runtime behavior.
