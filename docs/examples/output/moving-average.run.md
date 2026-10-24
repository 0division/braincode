# BrainCode run: moving-average.bc

## Input data

```json
{
  "initial_history": [
    {
      "temperature": 1
    },
    {
      "temperature": 2
    }
  ],
  "initial_state": {
    "temperature": 3
  },
  "inputs": [],
  "parameters": {},
  "ticks": 1
}
```

## BrainCode source

```braincode
# Scalar BrainCode draft.
# :temperature is a host-provided input recorded in the TVB each tick.
# While computing T+1, delays 1, 2, and 3 read input values at T, T-1,
# and T-2. The host must provide enough initial input history.

:average = (:temperature~1 + :temperature~2 + :temperature~3) / 3
```

## Output

```json
[
  {
    "temperature": 1
  },
  {
    "temperature": 2
  },
  {
    "temperature": 3
  },
  {
    "average": 2.0,
    "temperature": 3
  }
]
```
