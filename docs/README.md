# BrainCode Documentation

These documents develop the v0.1 concept and describe the evolving v0.2 implementation. They separate the vision, implemented semantics, history model, and research questions so open design work is not mistaken for a guarantee of a finished language.

## Documents

1. [Project handoff](./PROJECT-HANDOFF.md)
2. [Vision and scope](./01-vision.md)
3. [Execution model](./02-execution-model.md)
4. [Time, history, and replay](./03-time-history-replay.md)
5. [AI-assisted programming and discrete models](./04-ai-and-discrete-models.md)
6. [Stage-based concept suggestions](./05-concept-improvements.md)
7. [Language and compilation model](./06-language-and-compilation.md)
8. [Example configuration](./braincode.yaml.example)
9. [Implementation plan](./implementation-plan.md)
10. [BrainCode examples](./examples/README.md)
11. [Long-term product roadmap](./long-term-improvement-plan.md)

## Status

The compiler and serial Python reference runtime implement the subset used by the current examples. See the [Stage 1 contract](./stage1-contract.md) for declared-value checks, host adapters, run manifests, history/resource limits, and backend boundaries. Full static type inference, model-level actions, and accelerated backends remain future work. The v0.1 file remains as historical context.
