# BrainCode run: fibonacci.bc

## Input data

```json
{
  "initial_history": [
    {
      "fib": 0
    }
  ],
  "initial_state": {
    "fib": 1
  },
  "inputs": [],
  "parameters": {},
  "ticks": 5
}
```

## BrainCode source

```braincode
# Scalar BrainCode draft.
# Initial history supplied by the host:
#   :fib at T=0 = 0
#   :fib at T=1 = 1
# The recurrence begins when both delayed values exist.

:fib = :fib~1 + :fib~2
```

## Output

```json
[
  {
    "fib": 0
  },
  {
    "fib": 1
  },
  {
    "fib": 1
  },
  {
    "fib": 2
  },
  {
    "fib": 3
  },
  {
    "fib": 5
  },
  {
    "fib": 8
  }
]
```
