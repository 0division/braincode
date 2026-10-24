# BrainCode run: counter.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "counter": 0
  },
  "inputs": [],
  "parameters": {},
  "ticks": 5
}
```

## BrainCode source

```braincode
# Scalar BrainCode draft.
# Initial state supplied by the host: :counter = 0 at T=0.
# Each assignment computes the next frame from committed history.

:counter = :counter~1 + 1
```

## Output

```json
[
  {
    "counter": 0
  },
  {
    "counter": 1
  },
  {
    "counter": 2
  },
  {
    "counter": 3
  },
  {
    "counter": 4
  },
  {
    "counter": 5
  }
]
```
