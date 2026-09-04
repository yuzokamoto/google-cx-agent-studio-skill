# Durable Asynchronous Jobs and External Callbacks

Use this reference when a CX Agent Studio interaction starts work that completes later through a queue, webhook, callback, batch process, or other durable backend job.

This pattern is different from CX Agent Studio's native asynchronous tool execution.

## Platform facts

Current CX Agent Studio documentation distinguishes synchronous and asynchronous tool execution:

- synchronous tools block agent response generation and are intended for low-latency calls;
- asynchronous tools let the agent continue while the tool call is pending;
- Google's current guidance describes asynchronous tools as a good fit for roughly 5-60 second tool latencies;
- when the asynchronous tool result becomes available, it is added to context for a later agent response.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool

For work that can take minutes, hours, or longer, prefer a durable backend job rather than holding a CX tool request open indefinitely.

CX Agent Studio callbacks are Python lifecycle hooks that execute at defined points in an agent turn. They are not documented as externally callable webhook endpoints for arbitrary downstream systems.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/callback

The Session API documents `runSession` as initiating a single-turn interaction with the CES agent within a session. The service is `ces.googleapis.com`; the v1 REST path is:

`POST /v1/{config.session=projects/*/locations/*/apps/*/sessions/*}:runSession`

A `SessionInput` can carry an `event` or `variables` input. The `input_type` field is a union, so represent an event and variables as separate `SessionInput` entries when both are needed in the same `runSession` call.

For CX Agent Studio, variables used by the agent should be declared in the application. The current `SessionInput` reference states that only declared variables are used by the CES agent.

The caller of `runSession` must also satisfy the current API authentication/IAM requirements. The current v1 method reference documents the `ces.sessions.runSession` IAM permission on the session resource. Use a least-privilege service identity for automated resumptions.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest/v1/projects.locations.apps.sessions/runSession
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest/v1/SessionInput

## Recommended architecture

Use this pattern when an external system completes the work later:

```text
user/channel
  -> CX Agent Studio
  -> start_job tool
  -> authoritative backend
  -> durable queue/job processor
  -> external completion callback
  -> authoritative backend updates job state
  -> correlate operation_id to CX session
  -> runSession(existing session) with event/context
  -> agent calls get_job_result tool
  -> channel delivery layer presents the resulting agent response
```

The backend job is the source of truth. CX Agent Studio owns conversational orchestration, not durable job state.

## Start-job contract

The initiating tool should return a small stable contract, for example:

```json
{
  "operation_id": "job_opaque_id",
  "status": "PENDING"
}
```

`operation_id` is an application-level design recommendation, not a required CX Agent Studio field.

Store durable correlation outside model memory. Typical backend state may include:

```text
operation_id
session_id
status
created_at
expires_at
result_reference
idempotency_key
```

Use built-in session context injection where supported to supply the CX session identifier deterministically instead of asking the model to invent or recall it.

## External callback boundary

The external completion callback should terminate at a trusted application/backend boundary, not at an LLM prompt or a Python CX callback.

The backend should:

1. authenticate or validate the callback according to the integration contract;
2. enforce idempotency and reject duplicate or stale completions where required;
3. normalize external statuses into a fixed application-owned enum;
4. update the authoritative job state;
5. resolve the corresponding CX session and operation;
6. decide whether the result should still be surfaced;
7. resume the CX conversation only after the state transition is accepted.

Do not derive CX event names, tool names, or instructions directly from arbitrary callback text. Map accepted backend states to an allowlisted set of application-owned events.

Prefer passing an opaque operation identifier or minimal event metadata back into CX Agent Studio. For sensitive or authoritative data, have the agent retrieve the final result from a trusted read tool instead of injecting the entire callback payload into model context.

## Resume an existing session

`runSession` can start a new turn in an existing session. A recommended pattern is to send declared variables and a named event as separate `SessionInput` entries.

Illustrative request fragment:

```json
{
  "inputs": [
    {
      "variables": {
        "async_operation_id": "job_opaque_id"
      }
    },
    {
      "event": {
        "event": "async_job_completed"
      }
    }
  ]
}
```

This fragment intentionally omits other `RunSessionRequest` configuration fields. Fetch the current API schema before implementing production code.

Declare `async_operation_id` (or the application-specific equivalent) in the CX Agent Studio application if the CES agent must consume it.

Use application-specific event names. Do not claim that `async_job_completed` or `async_operation_id` are built-in CX Agent Studio identifiers.

## Agent behavior after the event

Keep the event handling deterministic where practical. A common design is:

1. receive the completion event;
2. read the opaque operation identifier;
3. call a read-only result tool such as `get_job_result`;
4. treat the backend response as authoritative;
5. generate or return a customer-safe response;
6. avoid restarting the original job unless an explicit retry contract allows it.

For highly regulated or sensitive outcomes, a callback can intercept the event and produce a deterministic response when model reasoning is unnecessary, but verify the exact callback/runtime shape in Simulator before relying on it.

## Channel delivery is a separate responsibility

Calling `runSession` produces a session response for the caller of the API. Do not assume that this alone pushes a message into every existing client/channel UI.

Treat proactive delivery as a channel integration responsibility:

```text
external callback
  -> backend
  -> runSession
  -> agent response returned to backend/channel adapter
  -> WebSocket / SSE / channel-specific push
  -> active client
```

For the Web Widget, current documentation exposes JavaScript rendering functions such as `renderCustomText`. Treat those functions as presentation mechanisms; do not assume a manually rendered message automatically becomes authoritative CX conversation state unless current documentation or observed behavior proves it.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/deploy/web-widget

If the target channel has its own proactive-messaging API, verify that channel's authentication, session, consent, expiration, and policy requirements separately.

## Concurrency and ordering

External events can race with active user turns. Do not assume two concurrent `runSession` operations on the same logical conversation will produce the desired ordering.

Recommended controls:

- serialize resumptions per session when ordering matters;
- deduplicate callbacks by operation/idempotency key;
- record the accepted completion sequence in the backend;
- define behavior when the user sends a message while completion is being processed;
- define whether an event should be suppressed after cancellation, timeout, handoff, or session expiration;
- never use a CX dynamic variable as the sole duplicate-prevention mechanism for a durable operation.

## Offline and expired-session behavior

Design the backend job independently from the lifetime of the interactive client.

If the user is offline or the original conversation can no longer be resumed:

- keep the authoritative result in the backend according to retention policy;
- avoid losing or re-running the job merely because the chat disconnected;
- decide whether the user should receive a channel-specific notification;
- otherwise surface the completed result when a later authenticated interaction retrieves the job state;
- do not create a fresh session and attach sensitive prior-job context solely from an old `session_id` without re-establishing the required user/session authorization boundary.

Do not promise that CX Agent Studio itself persists or proactively delivers a late result across arbitrary channel/session boundaries without current documented evidence.

## Security rules

- A session identifier is correlation metadata, not proof of end-user identity or authorization.
- Never trust callback payload data solely because it contains a known `operation_id` or `session_id`.
- Treat free-text callback fields and external payload content as untrusted data; do not let them select events, tools, prompts, or instructions without deterministic validation/mapping.
- Keep secrets and callback credentials out of agent instructions and model-visible variables.
- Use least-privilege credentials for the service that invokes `runSession`.
- Re-authorize access when the result tool returns customer-specific or sensitive data.
- Minimize model exposure: an opaque completion event plus a trusted result lookup is safer than copying a full webhook payload into the prompt.
- Apply backend authorization, idempotency, audit, retention, and replay protection independently from the model.

## Decision guide

Use native CX asynchronous tool execution when:

- the operation normally completes within the documented async latency envelope;
- keeping one CX tool call open is acceptable;
- the result should simply become available to the agent later in the same conversational flow.

Use a durable backend job plus external callback when:

- completion time can exceed the tool execution window;
- the work is queue-based, batch-based, externally approved, or webhook-driven;
- the operation must survive disconnects/restarts;
- durable retries, audit, idempotency, cancellation, or recovery are required;
- the completion should trigger a later conversational turn.

## Evaluation and integration tests

Test at least:

- start-job success and failure;
- duplicate start request;
- duplicate callback;
- callback authentication failure;
- callback containing unexpected/free-text status or event-like content;
- callback after cancellation;
- completion while the user is actively sending a message;
- completion after the user changes topic;
- late completion after client disconnect;
- result lookup authorization failure;
- result lookup temporary failure/retry;
- event delivered once and only once where required;
- correct behavior when the original session cannot be resumed;
- `runSession` caller lacks permission or uses the wrong target session;
- sensitive result is not copied into logs/model context unnecessarily;
- channel adapter delivers the CX-generated response to the intended user/session.

## Evidence labels for this pattern

**Documented:** native tool execution modes, callback lifecycle role, `runSession`, the current `ces.sessions.runSession` IAM permission, `SessionInput.event`, `SessionInput.variables`, declared-variable behavior, and Web Widget rendering APIs.

**Recommended:** durable `operation_id` correlation, queue/job store ownership, callback-to-backend bridge, allowlisted event mapping, result-by-tool retrieval, per-session serialization, and channel push architecture.

Do not present the recommended architecture as a built-in end-to-end CX Agent Studio callback feature.
