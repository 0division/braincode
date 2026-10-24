# BrainCode run: three-dimensional-heat-diffusion-proposal.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "temperature": [
      [
        [
          0.0,
          0.0
        ],
        [
          0.0,
          0.0
        ]
      ],
      [
        [
          0.0,
          0.0
        ],
        [
          0.0,
          1.0
        ]
      ]
    ]
  },
  "inputs": [],
  "parameters": {
    "DEPTH": 2,
    "HEIGHT": 2,
    "WIDTH": 2,
    "alpha": 0.1,
    "dt": 0.01,
    "dx": 1.0,
    "dy": 1.0,
    "dz": 1.0
  },
  "ticks": 1
}
```

## BrainCode source

```braincode
# The syntax is supported by the reference compiler. The workload should
# use small dimensions on the serial Python backend.
#
# Workload: explicit finite-difference heat diffusion on a 3D grid.
# Approximate work: O(width * height * depth) updates per step.
# A 1,024^3 Float32 grid needs about 4 GiB for one frame.
#
# The host supplies the initial :temperature population at T=0.
# All six stencil reads use the same committed prior frame.

population :temperature[WIDTH, HEIGHT, DEPTH] of Float32
boundary :temperature = insulated

each (:x, :y, :z) in :temperature parallel:
    :temperature[:x, :y, :z] =
        :temperature[:x, :y, :z]~1
        + :alpha * :dt * (
            (:temperature[:x - 1, :y, :z]~1
             - 2 * :temperature[:x, :y, :z]~1
             + :temperature[:x + 1, :y, :z]~1) / :dx ** 2
          + (:temperature[:x, :y - 1, :z]~1
             - 2 * :temperature[:x, :y, :z]~1
             + :temperature[:x, :y + 1, :z]~1) / :dy ** 2
          + (:temperature[:x, :y, :z - 1]~1
             - 2 * :temperature[:x, :y, :z]~1
             + :temperature[:x, :y, :z + 1]~1) / :dz ** 2
        )

# The runtime should validate numerical stability constraints and retain only
# the history required by the maximum delay when full tracing is disabled.
```

## Output

```json
[
  {
    "temperature": [
      [
        [
          0.0,
          0.0
        ],
        [
          0.0,
          0.0
        ]
      ],
      [
        [
          0.0,
          0.0
        ],
        [
          0.0,
          1.0
        ]
      ]
    ]
  },
  {
    "temperature": [
      [
        [
          0.0,
          0.0
        ],
        [
          0.0,
          0.001
        ]
      ],
      [
        [
          0.0,
          0.001
        ],
        [
          0.001,
          0.997
        ]
      ]
    ]
  }
]
```
