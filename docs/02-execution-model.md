# BrainCode: Execution Model

> The core semantics below are implemented by the serial reference runtime. Declared-value numeric behavior and optional bounded history are available; model-level side-effecting actions remain future work.

## Terms

- **Tick `T`:** A discrete model-evaluation index, starting at `0`.
- **Signal:** A named temporal value stored in the model state.
- **Rule:** An expression that determines a signal's value for a tick.
- **Frame:** The complete state of all signals at a tick.
- **Input:** An externally supplied value associated with a specific tick.
- **Action:** An explicitly marked call that may produce an external side effect.

## Tick semantics

For a transition from committed tick `T` to tick `T+1`, the runtime should compute the next frame in three phases:

1. **Read:** All rule inputs come from committed frames and tick-indexed inputs. While producing `T+1`, `signal~1` means the value of `signal` at `T`; larger delays read older frames. Rules cannot read another rule's uncommitted result.
2. **Evaluate:** All signal rules for `T+1` read the same committed state at `T` and the same input set. Source order must not affect the result.
3. **Commit:** The complete frame `T+1` is published atomically only after all rules have been evaluated successfully.

An expression `signal~0` is not supported. `~T` denotes the currently committed/source tick; `next_tick` denotes the frame being computed. Rules must not read values of that uncommitted next frame.

### Important clarification

The preferred temporal interpretation is “compute the next state from the previous committed state.” BrainCode uses its own syntax; for example, `:counter = :counter~1 + 1` computes the next counter value from the current committed value. While computing `T+1`, `:counter~1` reads `counter[T]`.

## Initialization and missing history

Historical frames before the supplied run history do not exist automatically. The host supplies the current frame and may supply older frames through the library API.

- Missing scalar state or a requested historical frame produces a runtime error.
- Declared populations/tensors omitted from the initial state are currently allocated with type-based zero values; callers should provide explicit initial values whenever the model depends on them.
- The CLI accepts an initial-state JSON object. The Python API additionally accepts `initial_history` and tick-indexed `input_frames`.
- Population dimensions must evaluate to non-negative integers. Supplied and updated population values must remain rectangular and match their declared shape.
- Array indices must be integers. Boundary policies affect out-of-range reads; writes must remain within the declared population bounds and cannot change the population's shape.
- For a run of `N` ticks, an input-frame sequence may contain at most `N+1` frames. Frame zero initializes the starting committed state; later frames provide inputs at each following committed tick. Every input frame must be a mapping.

The type-based population initialization is a convenience; declared state values, by contrast, must be present in the host's initial state.

## Assignments and conflicts

A model must define deterministically when a signal receives a value for each tick. Some v0.1 examples include a default rule and a second conditional assignment to the same signal. Without a conflict rule, this is ambiguous.

- the compiler rejects multiple rule sites that write the same signal/population;
- indexed writes inside one `each` block may target distinct elements;
- conditional state updates hold the previous value by default when their condition is false;
- branches for a signal can be written in a single conditional expression.

Example without competing assignments, using the proposed BrainCode syntax:

```text
:counter = 0 if :counter~1 > 1000
           else :counter~1 + 1
```

If a rule is conditional and does not produce a value, the runtime holds its previous state. Explicit reset/error policies are not implemented.

## Conditions

A condition for the transition `T -> T+1` may access the source tick `T`, host constants or tick-indexed inputs, and already committed historical values. It must not depend on the evaluation order of other rules.

The current grammar allows conditional blocks containing state assignments. The runtime treats them as conditional state assignments with hold behavior; they are not action blocks.

## Parallelism model

“Parallel” initially describes the **semantics**: rules for a tick are independent of their textual order and read the same prior state. It does not guarantee simultaneous execution on multiple CPU cores.

A backend may evaluate rules in parallel when:

- their dependencies refer only to already committed frames;
- they do not produce uncontrolled side effects during evaluation;
- their results and error behavior match the deterministic reference runtime.

The current reference implementation runs serially and deterministically. This provides a reliable reference for later optimizations.

## Host functions and purity

Host functions in signal expressions can undermine determinism if they use the clock, randomness, mutable globals, or I/O.

Implemented policy:

- signal expressions initially allow only built-in pure operations and explicitly registered pure host functions;
- external values are supplied as tracked inputs associated with specific ticks;
- actions run separately from computation and cannot mutate the state currently being computed.

Host-provided functions are passed explicitly to the runtime; the caller is responsible for ensuring registered functions used in state rules are pure and deterministic.

## Side effects and atomic commit

Actions such as `!(print(...))` are not implemented. A future action model should:

1. collect actions as events during tick evaluation;
2. evaluate all state rules and check for conflicts;
3. commit the frame;
4. execute actions afterward in a defined order.

A failure before commit must not publish a partial frame. An action failure after commit must be reported as an action failure and must not imply that the entire tick was never committed.

## Determinism

A run is reproducible when the language version, runtime version, program, initial state, tick inputs, and random seeds are identical, and all allowed host functions are deterministic.

Declared `Bool`, `Int32`, `Int64`, `Float32`, and `Float64` values are validated
at storage boundaries. Integer ranges are checked without wrapping, Float32
values round to binary32 on storage, and non-finite declared floats are
rejected. See the [Stage 1 contract](./stage1-contract.md) for exact behavior,
runtime budgets, and replay-manifest rules. Model-level action ordering and
failure behavior remain unspecified because actions are not implemented.

## Syntax and frontend note

The earlier concept draft is inconsistent about syntax: examples such as `:fib := ...` coexist with a grammar using the markers `:[` and `]:`. The current implementation uses a custom statement grammar in `.bc` files and a restricted Python-like expression subset. A BrainCode parser lowers the source to backend-independent `.bcc` IR. Python is the initial host and reference backend; it is not the BrainCode source grammar. Details are in [Language and Compilation Model](./06-language-and-compilation.md).

The implemented temporal reference syntax is `:signal~N`, with positive integer delays. The currently supported grammar is documented in [Language and Compilation Model](./06-language-and-compilation.md).
