# Cross-cutting suggestion: paired Python reference implementations

Add selected Python implementations alongside BrainCode examples to make the
same model's expression and execution structure easier to compare. This is an
educational and conceptual tool, not a performance claim or a replacement for
the BrainCode examples.

## Why

BrainCode and Python encourage different ways of describing computation.
BrainCode makes state, tick boundaries, historical reads, and independent
updates explicit. A Python implementation makes its host-language control
flow and data handling visible. Comparing equivalent models can help users
understand both the BrainCode execution contract and the kinds of solutions
each way of expressing a problem makes natural.

## Suggested scope

- Start with one small, representative model, such as a cellular automaton or
  a discrete network update, and provide a plain standard-library Python
  counterpart.
- Keep the BrainCode and Python versions next to one another and document the
  correspondence between state, inputs, tick updates, and output.
- Use the same small input fixtures and compare outputs in correctness tests
  where a faithful correspondence is practical.
- Explain meaningful semantic differences, including synchronous updates,
  committed-history reads, initialization, and boundary handling.
- Add further paired examples only when they illuminate a distinct modeling
  pattern; do not mechanically translate the entire example gallery.

## Boundaries

- Label Python files as reference implementations, not BrainCode runtime code.
- Prefer clear, idiomatic Python over micro-optimized code. Do not present the
  pair as a speed comparison.
- Keep NumPy variants separate and optional when they are useful to illustrate
  array-oriented expression. Different libraries or optimization levels
  would otherwise obscure the language comparison.
- Treat any claim that one expression style helps users discover better
  solutions as a question to explore, not a guaranteed outcome.

The first deliverable can be a single paired example and a short explanation.
It needs no compiler or runtime changes.
