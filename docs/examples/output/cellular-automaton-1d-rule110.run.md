# BrainCode run: cellular-automaton-1d-rule110.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "cells": [
      false,
      false,
      false,
      true,
      false,
      false,
      false
    ]
  },
  "inputs": [],
  "parameters": {},
  "ticks": 1
}
```

## BrainCode source

```braincode
# Optional tiny example: Rule 110, a one-dimensional cellular automaton.
# It is useful as a minimal test of local-neighbor updates, not as a required
# BrainCode feature or the main massive-parallelism example.
# The current reference compiler supports the population/indexing syntax.
#
# Initial frame supplied by the host at T=0:
#   :cells = [False, False, False, True, False, False, False]
#
# Every next cell reads only the previous frame.

population :cells[7] of Bool
boundary :cells = False

each :i in :cells parallel:
    let left = :cells[:i - 1]~1
    let center = :cells[:i]~1
    let right = :cells[:i + 1]~1
    :cells[:i] = (
        (left and center and not right)
        or (left and not center and right)
        or (not left and center and right)
        or (not left and center and not right)
        or (not left and not center and right)
    )

# Rule 110 is implemented directly as its truth table: the next cell is alive
# for neighborhoods 110, 101, 011, 010, and 001; otherwise it is dead.
# The chosen dead-cell boundary policy supplies False for out-of-range neighbors.
```

## Output

```json
[
  {
    "cells": [
      false,
      false,
      false,
      true,
      false,
      false,
      false
    ]
  },
  {
    "cells": [
      false,
      false,
      true,
      true,
      false,
      false,
      false
    ]
  }
]
```
