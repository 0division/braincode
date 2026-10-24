# BrainCode Documentation

These documents develop the v0.1 concept and describe the evolving v0.2 implementation. They separate the vision, implemented semantics, history model, and research questions so open design work is not mistaken for a guarantee of a finished language.

## Documents

1. [Vision and scope](./01-vision.md)
2. [Execution model](./02-execution-model.md)
3. [Time, history, and replay](./03-time-history-replay.md)
4. [AI-assisted programming and discrete models](./04-ai-and-discrete-models.md)
5. [Further concept improvements](./05-concept-improvements.md)
6. [Language and compilation model](./06-language-and-compilation.md)
7. [Example configuration](./braincode.yaml.example)
8. [Implementation plan](./implementation-plan.md)
9. [BrainCode examples](./examples/README.md)

## Status

The compiler and serial Python reference runtime implement the subset used by the current examples. Type-system details, explicit `.bc` input declarations, actions, resource limits, replay packaging, and accelerated backends remain open implementation work. The v0.1 file remains as historical context.
