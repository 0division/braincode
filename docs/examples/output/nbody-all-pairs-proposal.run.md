# BrainCode run: nbody-all-pairs-proposal.bc

## Input data

```json
{
  "initial_history": [],
  "initial_state": {
    "bodies": [
      0,
      0
    ],
    "mass": [
      1.0,
      1.0
    ],
    "position": [
      [
        0.0,
        0.0
      ],
      [
        1.0,
        0.0
      ]
    ],
    "velocity": [
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
  "inputs": [],
  "parameters": {
    "BODY_COUNT": 2,
    "G": 1.0,
    "VECTOR_DIM": 2,
    "softening": 0.01,
    "time_step": 0.01
  },
  "ticks": 1
}
```

## BrainCode source

```braincode
# The syntax is supported by the reference compiler. Use small body counts
# on the serial Python backend; this is not a performance implementation.
#
# Workload: gravitational N-body simulation with all-pairs interactions.
# Approximate work: O(body_count^2) pair interactions per tick.
# At 100,000 bodies, this is about 10 billion interactions per tick.
#
# The host supplies initial positions and velocities at T=0, plus masses and
# physical constants. Both rules compute T+1 from the committed T frame.

population :bodies[BODY_COUNT]
population :mass[BODY_COUNT] of Float64
population :position[BODY_COUNT, VECTOR_DIM] of Float64
population :velocity[BODY_COUNT, VECTOR_DIM] of Float64

each :i in :bodies parallel:
    let acceleration = sum(
        :G * :mass[:j]
        * (:position[:j]~1 - :position[:i]~1)
        / (
            length(:position[:j]~1 - :position[:i]~1) ** 2
            + :softening ** 2
        ) ** 1.5
        for :j in range(:BODY_COUNT)
        if :j != :i
    )
    :velocity[:i] = :velocity[:i]~1 + :time_step * acceleration
    :position[:i] = :position[:i]~1 + :time_step * :velocity[:i]~1

# This is a simplified explicit-Euler-style sketch, not a validated integrator.
# Force law, units, integration accuracy, collision handling, and reduction
# reproducibility all need precise definitions.
# :G, :mass, :softening, :time_step, and :BODY_COUNT are immutable model
# parameters; positions and velocities are dynamic state read from T.
```

## Output

```json
[
  {
    "bodies": [
      0,
      0
    ],
    "mass": [
      1.0,
      1.0
    ],
    "position": [
      [
        0.0,
        0.0
      ],
      [
        1.0,
        0.0
      ]
    ],
    "velocity": [
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
    "bodies": [
      0,
      0
    ],
    "mass": [
      1.0,
      1.0
    ],
    "position": [
      [
        0.0,
        0.0
      ],
      [
        1.0,
        0.0
      ]
    ],
    "velocity": [
      [
        0.009998500187478127,
        0.0
      ],
      [
        -0.009998500187478127,
        0.0
      ]
    ]
  }
]
```
