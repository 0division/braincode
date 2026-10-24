# TODO — Stage 4: hosted BrainCode API

Make BrainCode models runnable through a hosted API. A client should be able
to submit BrainCode source and a run configuration, start a run, check its
status, and retrieve results and a replay manifest without installing the
runtime locally.

This stage productizes the compiler and execution backends; it does not make
the language faster by itself. The first service may use the Python serial
backend with conservative limits. GPU execution is an optional backend only
after its supported subset, correctness, and measured performance are
established in Stage 3.

## Goals

- Provide a versioned, documented HTTP API for validating/compiling models,
  submitting runs, checking run status, and retrieving results.
- Keep the service thin: reuse the BrainCode compiler, versioned run
  manifests, and `ExecutionBackend` boundary rather than implementing another
  parser or runtime.
- Support asynchronous jobs so clients can submit a run and poll for
  completion without holding a request open for an unbounded computation.
- Return structured diagnostics, run metadata, and explicit backend and
  resource-limit information.
- Preserve the language's synchronous tick semantics and identify the exact
  compiler, runtime, and backend versions used for each run.

## Initial API shape

Define and version the precise schema before implementation. A first
resource-oriented API could provide:

- `POST /v1/compile` to validate source and return diagnostics and supported
  capabilities without executing it.
- `POST /v1/runs` to submit source, parameters, initial state/history,
  tick-indexed inputs, tick count, and requested backend; return a run ID.
- `GET /v1/runs/{id}` to retrieve state (`queued`, `running`, `succeeded`,
  `failed`, or `cancelled`), timestamps, and structured errors.
- `GET /v1/runs/{id}/results` and `GET /v1/runs/{id}/manifest` to retrieve
  completed output and replay metadata.
- `DELETE /v1/runs/{id}` to cancel an eligible run or request deletion of its
  stored data, with behavior defined explicitly.

Keep result pagination or downloadable artifacts in scope for large outputs;
do not require every full frame to fit in one API response. Define request,
response, and manifest schema versions, and make incompatible API changes
explicit.

## Trust, isolation, and operations

- Treat submitted source and inputs as untrusted. Run model execution in
  isolated workers with no ambient filesystem, network, or cloud credentials.
- Do not accept arbitrary Python code or uploaded host functions in the
  hosted MVP. The current local API allows registered host functions, which
  should remain a trusted, local capability unless a separately reviewed
  sandboxed extension model is designed.
- Authenticate clients and authorize access to each run. Apply per-user and
  per-run limits for source size, input/output size, ticks, population
  elements, memory, CPU/GPU time, queue depth, and concurrency.
- Enforce hard worker-level time and memory limits; runtime-level limits alone
  are not a process or container security boundary.
- Define result retention, deletion, encryption in transit and at rest,
  logging, incident response, and data-location policies before accepting
  sensitive models or inputs.
- Report queue time, execution time, selected backend, and resource usage
  separately. Make failures and partial availability explicit.

## Suggested delivery sequence

1. Specify the API schemas, compatibility policy, threat model, data-retention
   policy, and target users before selecting a cloud provider.
2. Prototype a local service against the CLI/runtime and conformance suite;
   verify that API results match direct serial runs and manifests replay.
3. Add authentication, isolated workers, quotas, bounded result storage,
   cancellation semantics, monitoring, and deployment automation.
4. Launch a limited CPU-backed preview with strict caps. Add GPU scheduling
   only for workloads supported and measured by Stage 3.
5. Test client integrations and real usage; set service-level objectives and
   pricing only after observing workload and cost data.

The cloud API is an access and operations layer, not evidence of acceleration.
Publish performance claims only for named workloads and hardware, measured
against relevant alternatives with compilation, queueing, and data-transfer
costs reported separately.
