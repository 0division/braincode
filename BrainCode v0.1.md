# BrainCode v0.1

> A Hybrid Neuro-Temporal Language

## Abstract

BrainCode is an embedded domain-specific language (DSL) designed to run concurrently within a standard sequential language such as Python. It defines a graph of simultaneous assignments that execute synchronously at every time step.

The host language handles initialization, setup, and external I/O. BrainCode assignments are defined in the host environment but executed in parallel during the runtime loop.

---

## I. Syntax and Core Components

### 1. Variables and Functions (Host Language)

Standard host language syntax is used for initialization. Variables and functions defined here are static constants or sequential setup logic that feeds the BrainCode graph.

```python
# Standard Python code for initialization
WEIGHT_A = 0.5
TIME_LIMIT = 50

def complex_filter(data_in):
    # Standard sequential function
    return data_in * 2
```

### 2. Time Access

The system provides a built-in, read-only variable for the current time step.

| Syntax | Meaning |
| --- | --- |
| `~T` | The current global time step counter (tick) |
| `var~N` | The value of `var` from `N` time steps in the past |

---

## II. BrainCode Parallel Syntax

The following elements define the concurrent temporal computation graph.

### 1. Simultaneous Assignment

Assignments define a variable's evolution rule for the next time step. The variable name is enclosed in brackets.

```python
# The new position is defined by the old position (pos~1)
# plus the old velocity (vel~1).
:pos := pos~1 + vel~1
```

### 2. Conditional Assignment Block

This structure allows a block of parallel actions to execute only when a temporal condition is met.

```python
# This block executes in parallel only when the counter reaches 100
?(counter~1 == 100):
    :flag_done := True
    !(print("Limit Reached!"))
```

A conditional block executes when the expression evaluates to true, similar to an `if` statement but for parallel assignments and side-effect calls.

### 3. Action Calls (Side Effects)

Actions produce side effects such as printing or file I/O. They are always preceded by `!` and must be contained within a conditional assignment block.

```python
!(call_name(arguments))
```

---

## III. Programming Examples

### 1. Hybrid Counter with Event Logging

This example shows a counter defined in BrainCode and a side effect triggered by the tick count.

```python
# Initial Setup (Host Environment)
# (Assume 'start_value' is defined here)

# BrainCode Graph Definition (executed at every tick)
:counter := counter~1 + 1

?(~T % 5 == 0):
    !(print(f"[~T] Counter value: {counter~1}"))
    :log_flag := True

?(counter~1 > 1000):
    :counter := 0
    !(print("Counter reset triggered."))
```

### 2. Fibonacci Sequence with Initialization

This demonstrates how to handle initial conditions with the time operator.

```python
# 1. Fibonacci sequence assignment
# Uses ~T value to set initial conditions (T=0 and T=1)
:fib := 0 if ~T == 0 \
    else 1 if ~T == 1 \
    else fib~1 + fib~2

# 2. Conditional block: stop and print final result after 10 ticks
?(~T == 10):
    !(print(f"Fibonacci at T=10 is: {fib~1}"))
    !(stop_simulation())
```

---

## Time-Value Boards: Capturing the Temporal State

The Time-Value Board (TVB) is a critical conceptual and implementation component of BrainCode. Since BrainCode defines a graph of simultaneous assignments that execute synchronously at every tick, the TVB acts as the memory ledger that records the value of every parallel variable for every time step.

It converts a dynamic concurrent execution into a static, queryable dataset that is useful for debugging, logging, and post-hoc analysis.

### The Structure of a Time-Value Board

Conceptually, the TVB is a two-dimensional matrix or database table:

- Rows represent time steps
- Columns represent parallel variables

### Example: variable/time matrix

| Variable / Time | T=0 | T=1 | T=2 | ... | T=N |
| --- | --- | --- | --- | --- | --- |
| counter | 0 | 1 | 2 | ... | N |
| pos | 10.0 | 10.5 | 11.5 | ... | V_N |
| fib | 0 | 1 | 1 | ... | F_N |
| log_flag | False | False | True | ... | False |

### Operational Role in BrainCode

The TVB makes the temporal syntax of BrainCode possible through past access, such as `var~N`.

#### 1. Enabling Past Access

When a BrainCode expression uses past access, such as `fib~2`, the runtime does not recompute the value; it simply performs a lookup in the TVB.

#### 2. Flow of Computation

1. Read phase: at the start of a time step, the system reads required past values from prior TVB rows.
2. Execution phase: the parallel computation graph evaluates all simultaneous assignments for the current tick.
3. Write phase: the new values are written synchronously to the row for the current time step and become available as past values for the next step.

---

## Applications and Benefits

### 1. Advanced Debugging and Verification

Because every intermediate value is stored, developers can step backward in time to inspect the exact state of a computation.

- Traceability: follow the dependency chain of a variable across multiple time steps.
- Replay: reconstruct the entire simulation by reading the board state.

### 2. Post-Hoc Analysis

The TVB becomes the definitive data source for analyzing simulation behavior.

- Visualization: plot variable evolution over time.
- Statistical analysis: compute aggregate metrics after the run completes.

---

## Time-Value Board for the Fibonacci Sequence

The TVB stores the value of `:fib` for each time step.

| Time step | fib at T-2 | fib at T-1 | Calculation for fib at T | New value |
| --- | --- | --- | --- | --- |
| 0 | N/A | N/A | 0 (initialization: `~T == 0`) | 0 |
| 1 | N/A | 0 | 1 (initialization: `~T == 1`) | 1 |
| 2 | 0 | 1 | `fib~1 + fib~2` => 1 + 0 | 1 |
| 3 | 1 | 1 | `fib~1 + fib~2` => 1 + 1 | 2 |
| 4 | 1 | 2 | `fib~1 + fib~2` => 2 + 1 | 3 |
| 5 | 2 | 3 | `fib~1 + fib~2` => 3 + 2 | 5 |
| 6 | 3 | 5 | `fib~1 + fib~2` => 5 + 3 | 8 |
| 7 | 5 | 8 | `fib~1 + fib~2` => 8 + 5 | 13 |
| 8 | 8 | 13 | `fib~1 + fib~2` => 13 + 8 | 21 |
| 9 | 13 | 21 | `fib~1 + fib~2` => 21 + 13 | 34 |
| 10 | 21 | 34 | `fib~1 + fib~2` => 34 + 21 | 55 |

### Explanation of the Process

1. Time `~T = 0` and `~T = 1` (initialization)
   - The conditions assign the starting values 0 and 1.
   - No historical access is required.
2. Time `~T = 2` (first historical access)
   - The calculation requires `fib~1` and `fib~2`.
   - The system reads from the TVB: `fib~1 = 1`, `fib~2 = 0`.
   - Result: `1 + 0 = 1`.
3. Time `~T = 3`
   - The system reads: `fib~1 = 1`, `fib~2 = 1`.
   - Result: `1 + 1 = 2`.

This example shows how the TVB provides the historical values needed for the current calculation.

---

## PLY Definition

This definition assumes BrainCode syntax is embedded within Python. The parser handles the specific parallel structures of BrainCode.

### 1. Lexical Analysis (Tokens)

| Token name | Regex | Description |
| --- | --- | --- |
| `TIME_ACCESS` | `~T` | Current global time step |
| `PAST_OPERATOR` | `~` | Past variable access operator |
| `SIM_ASSIGN_START` | `:[` | Start of a simultaneous assignment |
| `SIM_ASSIGN_END` | `]:` | End of a simultaneous assignment |
| `ASSIGN` | `:=` | Simultaneous assignment operator |
| `COND_START` | `?(` | Start of a conditional block |
| `COND_END` | `)` | End of a conditional block |
| `ACTION_CALL` | `!` | Side-effect operator |
| `ID` | `[a-zA-Z_][a-zA-Z_0-9]*` | Variable names |
| `NUMBER` | `\d+` | Integer values |
| `LPAREN` | `(` | Left parenthesis |
| `RPAREN` | `)` | Right parenthesis |
| `PLUS` | `+` | Addition |
| `MINUS` | `-` | Subtraction |
| `TIMES` | `*` | Multiplication |
| `DIVIDE` | `/` | Division |
| `EQ` | `==` | Equality |
| `NEQ` | `!=` | Inequality |
| `LT` | `<` | Less than |
| `GT` | `>` | Greater than |
| `LE` | `<=` | Less than or equal |
| `GE` | `>=` | Greater than or equal |
| `MOD` | `%` | Modulo |
| `AND` | `and` | Logical and |
| `OR` | `or` | Logical or |
| `NEWLINE` | `\n+` | Line separator |

### 2. Grammar (Parsing Rules)

```text
# Overall BrainCode program embedded in a Python host
sim_program : sim_statement
            | sim_program sim_statement

# Simultaneous statement
sim_statement : simultaneous_assignment
              | conditional_block
              | NEWLINE

# Simultaneous assignment
simultaneous_assignment : SIM_ASSIGN_START ID SIM_ASSIGN_END ASSIGN expression NEWLINE

# Conditional assignment block
conditional_block : COND_START expression COND_END NEWLINE INDENT sim_block DEDENT

# Block structure
sim_block : sim_block sim_action
          | sim_action

sim_action : simultaneous_assignment
           | action_call

# Side effect call
action_call : ACTION_CALL function_call NEWLINE

# Time access in expressions
time_variable : ID PAST_OPERATOR NUMBER
              | TIME_ACCESS

# Expression grammar
expression : term
           | expression PLUS term
           | expression MINUS term
           | expression EQ term
           | expression GT term
           | expression LT term

term : factor
     | term TIMES factor
     | term DIVIDE factor
     | term MOD factor

factor : NUMBER
       | ID
       | time_variable
       | function_call
       | LPAREN expression RPAREN

function_call : ID LPAREN argument_list RPAREN
argument_list : expression
              | argument_list ',' expression
              | empty
```

### Key BrainCode Structures in the Grammar

- Temporal logic: `TIME_ACCESS` (`~T`) and `PAST_OPERATOR` (`var~N`) are part of the core syntax.
- Parallelism: simultaneous assignments are clearly delimited by `:[` and `]:`.
- Control flow: conditional blocks use `?(...)` and indentation similar to Python.
- Side effects: calls using `!` are allowed only as actions within conditional blocks.

---

## Summary

BrainCode provides a hybrid model where a host language such as Python handles ordinary sequential work, while BrainCode executes time-aware parallel rules synchronously across the full simulation loop. The design is especially useful for temporal systems, historical state access, replayable debugging, and concurrent computations that require a persistent time-indexed memory model.