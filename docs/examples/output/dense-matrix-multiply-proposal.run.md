# BrainCode run: dense-matrix-multiply-proposal.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "A": [
      [
        1,
        2
      ],
      [
        3,
        4
      ]
    ],
    "B": [
      [
        5,
        6
      ],
      [
        7,
        8
      ]
    ]
  },
  "inputs": [],
  "parameters": {
    "N": 2
  },
  "ticks": 1
}
```

## BrainCode source

```braincode
# The syntax is supported by the reference compiler. Use small matrices on
# the serial Python backend; this is not a performance implementation.
#
# Workload: dense matrix multiplication.
# Approximate work: O(N^3) multiply-add terms for N x N matrices.
# Two 16,384 x 16,384 Float32 input matrices are about 2 GiB each; the output
# is another 1 GiB. Classical multiplication requires about 4.4 trillion
# multiply-add terms at this size.
#
# A and B are host-provided input signals recorded in each frame. The rule
# computes C at T+1 exclusively from A and B in the committed frame at T.
# Each output is reduced independently; no newly computed value is read.

tensor :A[N, N] of Float32
tensor :B[N, N] of Float32
tensor :C[N, N] of Float32

each (:i, :j) in :C parallel:
    :C[:i, :j] = sum(
        :A[:i, :k]~1 * :B[:k, :j]~1
        for :k in range(:N)
    )

# This is a temporal update whose expression performs a reduction over the
# previous frame. The reference runtime evaluates each reduction in order.
```

## Output

```json
[
  {
    "A": [
      [
        1.0,
        2.0
      ],
      [
        3.0,
        4.0
      ]
    ],
    "B": [
      [
        5.0,
        6.0
      ],
      [
        7.0,
        8.0
      ]
    ],
    "C": [
      [
        0.0,
        0.0
      ],
      [
        0.0,
        0.0
      ]
    ]
  },
  {
    "A": [
      [
        1.0,
        2.0
      ],
      [
        3.0,
        4.0
      ]
    ],
    "B": [
      [
        5.0,
        6.0
      ],
      [
        7.0,
        8.0
      ]
    ],
    "C": [
      [
        19.0,
        22.0
      ],
      [
        43.0,
        50.0
      ]
    ]
  }
]
```
