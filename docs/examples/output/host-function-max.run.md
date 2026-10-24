# BrainCode run: host-function-max.bc

## Input data

```json
{
  "initial_history": [
    {
      "t": 4
    }
  ],
  "initial_state": {
    "t": 7
  },
  "inputs": [],
  "parameters": {},
  "ticks": 1
}
```

## BrainCode source

```braincode
# Scalar BrainCode draft demonstrating a Python host function in an expression.
# `max` must be available through the runtime's approved pure-function registry.
# At T+1, :t~1 is the committed value at T and :t~2 is the value at T-1.

:t = max(:t~1, :t~2)
```

## Output

```json
[
  {
    "t": 4
  },
  {
    "t": 7
  },
  {
    "t": 7
  }
]
```
