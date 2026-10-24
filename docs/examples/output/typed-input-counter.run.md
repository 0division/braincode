# BrainCode run: typed-input-counter.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "counter": 0
  },
  "inputs": [
    {
      "increment": 1
    },
    {
      "increment": 2
    },
    {
      "increment": 3
    },
    {
      "increment": 4
    }
  ],
  "parameters": {},
  "ticks": 3
}
```

## BrainCode source

```braincode
input :increment of Int32
state :counter of Int32

:counter = :counter~1 + :increment~1
```

## Output

```json
[
  {
    "counter": 0,
    "increment": 1
  },
  {
    "counter": 1,
    "increment": 2
  },
  {
    "counter": 3,
    "increment": 3
  },
  {
    "counter": 6,
    "increment": 4
  }
]
```
