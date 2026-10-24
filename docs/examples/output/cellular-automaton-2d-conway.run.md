# BrainCode run: cellular-automaton-2d-conway.bc

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
# Proposed 2D cellular-automaton syntax: Conway's Game of Life (B3/S23).
# Population/indexing and neighbor_count are implemented by the v0.2
# reference compiler; parallel execution is currently serial.
#
# Initial frame is supplied by the host. Each cell in T+1 is computed only
# from the committed grid at T. `neighbor_count` is a data-parallel stencil
# primitive; it should be lowered by the backend, not called as a Python
# function once per cell.

population :cells[WIDTH, HEIGHT] of Bool
boundary :cells = dead

each (:x, :y) in :cells parallel:
    let neighbors = neighbor_count(
        :cells~1, :x, :y, neighborhood=moore_2d, boundary=dead
    )
    let was_alive = :cells[:x, :y]~1
    :cells[:x, :y] =
        True if neighbors == 3
        else True if (was_alive and neighbors == 2)
        else False

# B3/S23: a dead cell is born with exactly three live neighbors; a live cell
# survives with two or three. All other cells are dead in the next frame.
#
# `let` names are local to this cell's rule evaluation, not temporal signals.
# Work per generation is O(WIDTH * HEIGHT), with eight neighbor reads per cell.
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
