# BrainCode run: coupled-signals.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "left": 1,
    "right": 10
  },
  "inputs": [],
  "parameters": {},
  "ticks": 1
}
```

## BrainCode source

```braincode
# Scalar BrainCode draft.
# Initial frame supplied by the host at T=0:
#   :left = 1
#   :right = 10
#
# Both rules read the same committed frame. Neither observes the other
# rule's uncommitted result.

:left = :right~1 + 1
:right = :left~1 + 1
```

## Output

```json
[
  {
    "left": 1,
    "right": 10
  },
  {
    "left": 11,
    "right": 2
  }
]
```
