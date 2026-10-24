# BrainCode Long-Term Product Roadmap

This roadmap describes a path from the current v0.2 compiler and serial
reference runtime to a usable BrainCode product. The long-term goal is not just
a more complete language: it is an integrated environment where people can
build, run, inspect, debug, visualize, and share large stateful models, with
GPU execution for workloads that benefit from it.

The serial Python runtime remains the correctness reference. Product features
and accelerated backends must preserve BrainCode's documented synchronous
execution semantics, or clearly show where and why results can differ.

## Product vision

A BrainCode user should be able to:

- create and edit a model in an integrated IDE, initially through a VS Code
  extension;
- understand its state, history, parallel domains, and data flow visually;
- run it locally or through a hosted API on a supported CPU or GPU backend and
  see progress and resource use;
- pause, inspect, step through, and debug individual ticks and state values;
- explore time-series and spatial results without writing a separate viewer;
- save, replay, compare, and share a complete model run.

## Product pillars

### 1. GPU and scalable execution

- Define a backend interface that lets the compiler target the serial
  reference runtime, optimized CPU execution, and GPU devices.
- Implement a first GPU backend for a deliberately bounded, high-value subset
  of BrainCode, such as regular population updates and stencil computations.
- Add device discovery, memory estimates, capability reporting, and explicit
  CPU fallback when a program cannot run on the selected GPU.
- Keep data resident on the device across ticks where possible; report transfer
  and compilation costs separately from kernel execution time.
- Support deterministic execution modes where practical and document numeric
  precision and reduction differences when GPU execution changes operation
  ordering.
- Expand supported features based on real examples and measured speedups, not
  on backend feature counts alone.

**Product outcome:** users can run representative large cellular automata,
stencils, and other supported data-parallel models on a GPU and compare their
results and performance with the serial reference.

### 2. IDE authoring environment

- Start with a VS Code extension that uses a workspace for model files,
  examples, input configurations, run settings, and generated artifacts.
- Keep the compiler and runtime independent of VS Code so other clients,
  including a future standalone GUI, can reuse them.
- Provide BrainCode syntax highlighting, completion, formatting, diagnostics,
  navigation, and documentation hints.
- Show model structure visually: state variables, temporal dependencies,
  population dimensions, update rules, and host inputs.
- Allow users to configure and launch runs without composing command-line
  arguments by hand.
- Keep the textual `.bc` language first-class: graphical views should explain
  and assist with source, not silently replace or obscure it.

**Product outcome:** a new user can open an example in VS Code, understand its
model and inputs, edit it, and run it. Reassess a standalone GUI only if user
needs outgrow the extension workflow.

### 3. Interactive debugger and time inspector

- Add breakpoints on rules, ticks, and conditional branches.
- Support run, pause, resume, single-step, and step-back through retained
  history or checkpoints.
- Inspect a signal or population element at a selected tick, including the
  values read by a rule and the value it proposes to write.
- Explain a result by showing the rule, historical inputs, boundary behavior,
  and evaluation outcome that produced it.
- Compare two ticks or runs and highlight changed state, parameters, and
  inputs.
- Present explicit limits when a backend cannot pause at a fine-grained
  execution point; GPU debugging must not imply observability it cannot provide.

**Product outcome:** users can diagnose an unexpected state transition without
manually instrumenting the runtime or printing entire frames.

### 4. Visualization and model exploration

- Provide time-series plots for scalar signals and selected population
  elements.
- Add grid and tensor viewers for 1D, 2D, and 3D data, with playback across
  ticks and controls for scale, slice, and color mapping.
- Visualize neighborhoods, boundaries, reductions, and selected data-flow
  relationships where these views help explain a model.
- Let users filter, sample, and aggregate large results instead of loading
  every value into a GUI.
- Make visualization definitions saveable as part of a project or run.

**Product outcome:** spatial and temporal behavior is explorable interactively,
including for runs too large to inspect as raw JSON.

### 5. Reproducible projects and run management

- Define a project format that groups `.bc` sources, `.bc.in.json` inputs,
  dependencies, and visualization/debug settings.
- Save run manifests with source and input versions, compiler and backend
  versions, device details, parameters, and relevant execution settings.
- Support deterministic replay when the selected program and backend permit it.
- Provide run history, comparisons, checkpoint/resume, export, and sharing.
- Make large-run storage configurable, with retention and resource controls.

**Product outcome:** a project can be reopened and a past result can be
understood, compared, or reproduced without relying on undocumented machine
state.

### 6. Distribution and extensibility

- Package the compiler, runtimes, and VS Code extension for supported
  platforms; package a standalone GUI only if later user needs justify it.
- Refine the existing Python embedding API and consider optional NumPy
  interoperation without making NumPy a required dependency.
- Provide a documented extension interface for approved host functions,
  visualization components, and future execution backends.
- Include an example gallery and templates organized by model type and
  execution requirements.
- Add automated compatibility checks for project, IR, and checkpoint format
  versions.
- Establish stable release channels and migration guidance before promising
  long-term project-file compatibility.

**Product outcome:** BrainCode can be installed, extended, upgraded, and used
outside the source checkout by people who are not developing the compiler.

### 7. Hosted API service

- Offer versioned compile/validation and run APIs that reuse the existing
  compiler, run contract, and execution-backend interface.
- Provide asynchronous run submission, status, cancellation, structured
  diagnostics, and bounded result retrieval.
- Begin with a capped CPU-backed preview; schedule GPU runs only for programs
  supported by a validated and benchmarked GPU backend.
- Isolate submitted models in workers with strict CPU, memory, duration,
  input/output, and concurrency limits.
- Define authentication, tenant isolation, retention/deletion, privacy,
  observability, availability, and cost controls before opening the service
  beyond a controlled preview.
- Do not accept arbitrary Python host functions in the hosted service unless a
  separately reviewed and constrained extension mechanism is designed.

**Product outcome:** clients can submit a BrainCode model and inputs to a
documented cloud API, follow a run, and retrieve versioned results and replay
metadata with clear resource and backend guarantees.

## Suggested delivery sequence

1. **Technical foundation:** stabilize the language contract, diagnostics, IR
   versioning, run manifests, and backend interface.
2. **First acceleration:** deliver a measured CPU or GPU prototype for a small,
   useful language subset; retain the serial runtime as the conformance oracle.
3. **First interactive workflow:** build a VS Code editor/run experience for
   the serial backend. Prototype source-linked tick and state inspection using
   runtime capabilities; do not imply pause/step debugging until implemented.
4. **Visual exploration:** add time-series and tensor/grid viewers driven by
   saved run data and streaming interfaces.
5. **GPU productization:** expand GPU coverage, improve memory management,
   integrate progress and profiling, and support graceful fallback.
6. **Release-ready application:** complete project management, replay,
   checkpointing, packaging, documentation, and compatibility policies for
   the VS Code extension or a standalone application if justified.
7. **Ecosystem growth:** add extensions, richer visual analyses, collaboration,
   and additional backends based on user needs.
8. **Hosted execution:** deploy a limited API service only after the run
   contract, backend capabilities, worker isolation, and resource policies are
   validated. A CPU-backed preview does not need to wait for broad GPU
   coverage; GPU selection must remain capability-gated.

These stages are directional rather than calendar commitments. A stage should
advance only when the previous capabilities work end to end for representative
models and are validated with real users.

Paired Python reference examples and Python/NumPy interoperability are
cross-cutting proposals, not new numbered stages. Array interoperability must
not be confused with an accelerated NumPy backend or a performance claim. See
the [cross-cutting suggestions](./suggestions/README.md).

## Foundational work that enables the product

The following engineering work is necessary, but it is not the long-term
product vision by itself:

- finish the language and numeric semantics and maintain a conformance suite;
- validate declared inputs, shapes, history, and resource limits;
- establish performance and memory baselines for representative workloads;
- make execution errors and backend capabilities visible and actionable;
- preserve reproducibility through run manifests, versioned artifacts, and
  replay tests.

## Measures of product readiness

- A first-time user can open, edit, run, and visualize an example without
  leaving the application.
- A user can trace an unexpected value back to its rule and historical inputs.
- At least one representative data-parallel workload has a measured GPU
  benefit at a documented problem size, including transfer and setup costs.
- Unsupported GPU features fail clearly or fall back as documented.
- Saved projects and runs reopen with enough provenance to explain their
  results.
- Performance, memory use, and known limitations are published for each
  supported backend and release.
