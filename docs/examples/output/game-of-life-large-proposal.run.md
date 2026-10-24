# BrainCode run: game-of-life-large-proposal.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "cells": [
      [
        false,
        true,
        false
      ],
      [
        false,
        false,
        true
      ],
      [
        true,
        true,
        true
      ]
    ]
  },
  "inputs": [],
  "parameters": {
    "HEIGHT": 3,
    "WIDTH": 3
  },
  "ticks": 1
}
```

## BrainCode source

```braincode
# The syntax is supported by the reference compiler. `parallel` currently
# defines the data-parallel iteration domain; the Python backend is serial.
#
# Workload: a large two-dimensional Game of Life grid.
# Approximate work: O(width * height) cell updates per generation.
# A 16,384 x 16,384 grid contains over 268 million cells.
#
# The host supplies the initial population state at T=0.
# `each` expresses data parallelism across cells. Every neighborhood read
# uses the same previously committed frame.

population :cells[WIDTH, HEIGHT] of Bool
boundary :cells = wrap

each (:x, :y) in :cells parallel:
    :cells[:x, :y] = life_rule(
        neighbor_count(:cells~1, :x, :y, radius=1, include_center=False),
        :cells[:x, :y]~1
    )

# Design questions:
# - Are neighbor_count and life_rule built-ins or host-registered pure functions?
# - Are boundaries periodic, fixed, reflective, or explicitly supplied?
# - How are Boolean neighbor counts represented?
# - How does the runtime store or compress hundreds of millions of cells?
# - Can it avoid materializing every intermediate frame?
```

## Output

```json
[
  {
    "cells": [
      [
        false,
        true,
        false
      ],
      [
        false,
        false,
        true
      ],
      [
        true,
        true,
        true
      ]
    ]
  },
  {
    "cells": [
      [
        false,
        false,
        false
      ],
      [
        true,
        false,
        true
      ],
      [
        false,
        true,
        true
      ]
    ]
  }
]
```
