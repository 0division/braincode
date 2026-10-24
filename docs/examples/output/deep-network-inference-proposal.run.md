# BrainCode run: deep-network-inference-proposal.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "input": [
      [
        1.0,
        2.0
      ]
    ],
    "weights_1": [
      [
        1.0,
        0.0
      ],
      [
        0.0,
        1.0
      ]
    ],
    "weights_2": [
      [
        3.0
      ],
      [
        4.0
      ]
    ]
  },
  "inputs": [],
  "parameters": {
    "BATCH": 1,
    "HIDDEN_WIDTH": 2,
    "INPUT_WIDTH": 2,
    "OUTPUT_WIDTH": 1
  },
  "ticks": 1
}
```

## BrainCode source

```braincode
# PROPOSAL — tensors, batches, reductions, and explicit kernel stages are not
# yet part of the defined BrainCode grammar.
#
# Workload: batched dense neural-network inference.
# Approximate work: O(batch * sum(layer_width[i] * layer_width[i+1])).
# Matrix operations and independent samples expose substantial parallel work.
#
# Inputs and weights are signals recorded in each frame. Each rule computes
# its state for T+1 using only the committed frame at T. Consequently, this
# models one layer of temporal propagation per tick; it does not compute a
# conventional whole-network inference pass in a single tick.

tensor :input[BATCH, INPUT_WIDTH] of Float32
tensor :weights_1[INPUT_WIDTH, HIDDEN_WIDTH] of Float32
tensor :weights_2[HIDDEN_WIDTH, OUTPUT_WIDTH] of Float32
tensor :hidden[BATCH, HIDDEN_WIDTH] of Float32
tensor :output[BATCH, OUTPUT_WIDTH] of Float32

each (:sample, :h) in :hidden parallel:
    :hidden[:sample, :h] = relu(sum(
        :input[:sample, :i]~1 * :weights_1[:i, :h]~1
        for :i in range(:INPUT_WIDTH)
    ))

each (:sample, :o) in :output parallel:
    :output[:sample, :o] = sum(
        :hidden[:sample, :h]~1 * :weights_2[:h, :o]~1
        for :h in range(:HIDDEN_WIDTH)
    )

# The output therefore reflects the preceding tick's hidden state. This
# deliberate tick latency follows the no-same-tick-dependency rule.
```

## Output

```json
[
  {
    "hidden": [
      [
        0.0,
        0.0
      ]
    ],
    "input": [
      [
        1.0,
        2.0
      ]
    ],
    "output": [
      [
        0.0
      ]
    ],
    "weights_1": [
      [
        1.0,
        0.0
      ],
      [
        0.0,
        1.0
      ]
    ],
    "weights_2": [
      [
        3.0
      ],
      [
        4.0
      ]
    ]
  },
  {
    "hidden": [
      [
        1.0,
        2.0
      ]
    ],
    "input": [
      [
        1.0,
        2.0
      ]
    ],
    "output": [
      [
        0.0
      ]
    ],
    "weights_1": [
      [
        1.0,
        0.0
      ],
      [
        0.0,
        1.0
      ]
    ],
    "weights_2": [
      [
        3.0
      ],
      [
        4.0
      ]
    ]
  }
]
```
