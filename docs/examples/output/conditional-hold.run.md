# BrainCode run: conditional-hold.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "alarm": true,
    "trigger": false
  },
  "inputs": [],
  "parameters": {},
  "ticks": 1
}
```

## BrainCode source

```braincode
# Draft conditional-update example.
# Initial frame supplied by the host:
#   :alarm = False at T=0
#
# If the prior tick's trigger is true, set :alarm in T+1.
# If this conditional update does not run, the prior :alarm value is held.

?(:trigger~1):
    :alarm = True
```

## Output

```json
[
  {
    "alarm": true,
    "trigger": false
  },
  {
    "alarm": true,
    "trigger": false
  }
]
```
