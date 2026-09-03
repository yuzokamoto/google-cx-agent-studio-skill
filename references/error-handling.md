# Fallback and Error Handling

Use this reference when a CX Agent Studio application cannot generate a response, a tool fails, a business operation returns a negative result, retries are needed, or a session may need to end/escalate.

## Start by classifying the failure

Do not treat every non-happy-path outcome as the same kind of error.

| Failure class | Examples | Primary owner / control surface |
|---|---|---|
| **System/model failure** | AI cannot generate a response, LLM/system error | Agent application fallback/error-handling settings |
| **Tool/integration failure** | timeout, 5xx, auth/IAM failure, network error, malformed upstream response | Tool/backend contract plus callback/agent handling where needed |
| **Expected business-negative result** | no product available, order not found, request rejected by an authoritative rule | Stable backend/tool result contract plus customer-facing agent behavior |
| **Invalid/missing prerequisite** | malformed input, unauthenticated state, missing validated variable | Backend validation and appropriate callback/Handoff Rule/tool precondition |
| **User-requested escalation/end** | user asks for human, user is done | Explicit supported escalation/end-session path |
| **Critical journey failure** | required operation cannot safely continue | Deterministic failure handling, possibly handoff or end-session according to policy |

Identify the failure class before changing prompts. A prompt edit cannot repair IAM, networking, or an authoritative business decision.

## Application fallback behavior

CX Agent Studio currently exposes application-level fallback behavior for cases where the AI/system cannot continue generating responses.

Current settings documentation describes:

- **Retries** — how many times the agent should retry when AI cannot generate a response;
- **Agent response** — the response used when asking the end-user for permission before retrying;
- **Fallback** — what happens after the final retry attempt fails.

The current API/RPC model exposes `ErrorHandlingSettings` with:

- `error_handling_strategy`;
- `fallback_response_config`;
- `end_session_config`.

Current strategies include:

- `NONE`;
- `FALLBACK_RESPONSE` — return a fallback message for system errors such as LLM errors;
- `END_SESSION` — emit an `EndSession` signal for system errors such as LLM errors.

`FallbackResponseConfig` currently supports language-keyed custom fallback messages and `max_fallback_attempts`. `EndSessionConfig` currently supports marking the ended session as escalated.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/settings
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rpc/google.cloud.ces.v1

### Scope boundary

Application fallback settings are **not** a universal catch-all for every failure.

Do not assume they handle:

- an HTTP 503 returned by a business tool in the desired customer-specific way;
- a normal `NOT_FOUND`/`NO_RESULT` business outcome;
- invalid tool arguments;
- authorization rejection by the backend;
- a failed private-network connection;
- a user explicitly requesting a human representative.

Those cases need handling at the layer that owns them.

## Tool and integration failures

For a tool failure, first preserve the technical distinction needed for engineering while exposing only customer-safe information to the model/user.

A useful tool/backend contract may distinguish categories such as:

```text
INVALID_INPUT
UNAUTHORIZED
NOT_FOUND
RATE_LIMITED
UPSTREAM_TIMEOUT
TEMPORARILY_UNAVAILABLE
INTERNAL_ERROR
```

The exact taxonomy is application-specific. Keep it small and stable.

Possible deterministic handling layers include:

- backend HTTP/status contract;
- `before_tool_callback` for local prerequisites/validation;
- `after_tool_callback` for response/error normalization;
- `before_model_callback` when current documented function-response evidence supports deterministic transfer/end behavior;
- Handoff Rules when transfer depends on an explicit variable/prerequisite.

Google's current best-practices documentation includes patterns for deterministically transferring or ending a session after a specific tool failure. Treat those as patterns, not a requirement that every tool failure should terminate or transfer.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/best-practices

## Expected business-negative outcomes are not technical failures

A valid business response such as:

```json
{
  "status": "NO_PRODUCTS_AVAILABLE"
}
```

or:

```json
{
  "status": "ORDER_NOT_FOUND"
}
```

may be a normal successful API execution even though the user's desired result was not achieved.

Model these explicitly instead of mapping every negative result to `INTERNAL_ERROR` or application fallback.

Benefits:

- the agent can provide the correct neutral/customer-safe response;
- retry policy stays meaningful;
- telemetry can distinguish business outcomes from incidents;
- evaluations can assert the intended path;
- the model does not need to infer whether an empty/ambiguous response means failure.

Do not expose sensitive reasons merely because the backend has them. Return the minimum safe distinction the conversation needs.

## Retry ownership

Different retries solve different problems.

### AI/system fallback retry

Use the application fallback retry configuration for the documented AI/system generation failure case.

### Tool/network retry

Retry transient external operations only when the integration contract permits it. Consider:

- idempotency;
- mutation side effects;
- rate limits;
- upstream retry guidance;
- total latency/tool timeout;
- whether the backend/orchestrator is the better retry owner.

Do not implement blind model-driven repeated tool calls as a retry mechanism for state-changing operations.

### User correction retry

Invalid user input often requires a conversational correction rather than an infrastructure retry. Validate deterministically where appropriate, explain the accepted format, and ask again without calling the backend repeatedly when the request is known-invalid.

## Escalation and session termination

Do not conflate these cases:

- system fallback configured to end/escalate after the agent cannot continue;
- deterministic handling of a critical tool failure;
- user explicitly asks for a human;
- normal successful end of conversation.

The current `end_session` system tool supports a reason, `session_escalated`, and metadata params. Use the currently documented channel/platform handoff mechanism for actual human-routing behavior; an `EndSession` escalation signal alone does not define every external contact-center routing implementation.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/system

## Failure-handling design checklist

For every important journey, define:

1. What counts as a normal business-negative result?
2. What errors are retryable?
3. Which layer owns each retry?
4. Does the operation require idempotency?
5. What customer-safe message corresponds to each failure class?
6. When should the conversation remain active?
7. When should control transfer to another agent?
8. When should the session end or escalate?
9. What technical correlation/audit data stays outside customer-facing model context?
10. How will each path be evaluated and integration-tested?

## Debugging order

When a failure occurs:

1. classify it as system/model, tool/integration, business-negative, prerequisite, or channel/escalation;
2. inspect Simulator/trace and tool response evidence;
3. inspect networking/authentication/backend logs for integration failures;
4. inspect variables/callbacks/handoff rules for deterministic prerequisite failures;
5. inspect application fallback settings only for the system/model failure class they are intended to handle;
6. add a regression evaluation for agent-visible behavior;
7. add/retain a real integration test if networking/auth/backend behavior is involved.

## Evaluation coverage

At minimum, distinguish tests for:

- system/model fallback path;
- fallback retry exhaustion;
- technical tool failure;
- retryable versus non-retryable tool failure;
- expected business-negative result;
- invalid prerequisite/input;
- user-requested human escalation;
- critical failure end-session path;
- no duplicate state-changing call during recovery;
- customer-facing response does not leak internal error details.

See `evaluations-debugging.md` for replay modes, metric limitations, and release-gate composition.
