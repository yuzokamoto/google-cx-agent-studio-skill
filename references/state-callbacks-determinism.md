# State, Variables, Callbacks, and Deterministic Control

Use this reference when deciding how state is represented, how variables are updated, where validation belongs, or how callbacks should enforce behavior.

## Conversation state is not authoritative business state

CX Agent Studio variables are useful for conversational orchestration. They should not automatically become the system of record for durable business processes.

Keep authoritative state in a trusted backend when you need:

- consistency across sessions/channels;
- idempotency;
- durable recovery;
- authorization/audit guarantees;
- irreversible transaction control;
- compliance-grade workflow history.

Use CX variables as a projection/cache/orchestration aid when appropriate.

## Static variables

Current CX Agent Studio supports **static variables**.

Properties:

- referenced in instructions as `{{variable_name}}`;
- compiled directly into the prompt as text substitution;
- intended for values that change infrequently;
- useful for configuration, stable business rules, or large context that is constant within a conversation;
- changing their value invalidates prompt caching and can affect latency.

Do not put secrets into prompts merely because static variables exist.

## Dynamic variables

Dynamic variables:

- referenced as `{variable_name}`;
- can change during a conversation;
- can be updated by tools, callbacks, or API requests;
- are represented to the model through state-update events rather than simple prompt text substitution.

Use them for:

- validated user/session attributes;
- tool results needed by later turns;
- routing/handoff prerequisites;
- lightweight conversational progress.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/variable

## Built-in session context

OpenAPI and MCP integrations can use built-in context values such as project/app/session identifiers and declared variables. These built-in values are not ordinary custom instruction variables and cannot be manually overwritten.

Prefer built-in context injection for technical metadata instead of asking the model to populate it.

## Callback lifecycle

CX Agent Studio currently documents six callback types:

1. `before_agent_callback`
2. `after_agent_callback`
3. `before_model_callback`
4. `after_model_callback`
5. `before_tool_callback`
6. `after_tool_callback`

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/callback

Conceptual flow:

```text
agent invocation
  -> before_agent_callback
  -> before_model_callback
  -> model
  -> after_model_callback
  -> before_tool_callback (when a tool is called)
  -> tool
  -> after_tool_callback
  -> ...
  -> after_agent_callback
```

Actual turns can contain multiple model/tool cycles. Do not treat this diagram as proof of a single fixed call sequence for every conversation.

## Callback selection

### `before_agent_callback`

Use for deterministic checks/setup before an agent is invoked, or to bypass the agent with a deterministic response.

Examples:

- required session state check;
- initialization;
- blocking entry into an agent when prerequisites are missing.

### `after_agent_callback`

Use for cleanup/final-state checks or replacing the agent's final output when the documented return behavior fits the requirement.

### `before_model_callback`

Use to inspect/modify model input or return a deterministic model response without making a model call.

Examples:

- deterministic session-start greeting;
- context injection;
- pre-model validation;
- deterministic handling of a known event.

### `after_model_callback`

Use to inspect/replace model output.

Examples:

- enforce output postconditions;
- redact/transform generated text when a guardrail rule is not sufficient;
- attach supported response parts/payloads.

### `before_tool_callback`

Use for deterministic validation and interception immediately before tool execution.

Examples:

- normalize an argument;
- validate format/checksum;
- enforce a session prerequisite;
- return a mocked/cached response and skip external execution.

### `after_tool_callback`

Use to minimize/transform the response given back to the model and to persist selected values into dynamic variables.

Examples:

- strip irrelevant upstream fields;
- map backend statuses to stable agent-facing enums;
- store an opaque journey/correlation identifier;
- normalize tool failures.

## Determinism hierarchy

For requirements that must not depend on model judgment, prefer:

```text
Authoritative backend
    > tool implementation
    > callback
    > Handoff Rule
    > instruction
    > free model inference
```

This is an engineering preference, not a claim that every higher layer can replace every lower layer. Choose the layer that actually owns the responsibility.

## Validation pattern

For user input that affects a backend request:

1. normalize/validate early for UX;
2. block obviously invalid tool calls deterministically if appropriate;
3. **validate again in the backend**;
4. never treat client/model/callback validation as authorization.

A callback improves experience; the backend remains the trust boundary.

## Response minimization pattern

If an upstream service returns a large payload:

```text
upstream response
  -> after_tool_callback or Python wrapper
  -> minimal stable agent-facing response
  -> model
```

Keep only fields the model needs to explain the outcome or decide the next conversational action.

## Do not guess callback payload shapes

The documented callback signatures are useful, but application-specific tool wrappers and response contents can still surprise you.

Before production code depends on paths such as:

```python
input["requestBody"]
tool_response["body"]
tool.name == "some_runtime_name"
```

verify those paths in the current Simulator trace/tool execution. Treat placeholder callback examples as scaffolding until runtime evidence confirms the shape.

## Error handling

Prefer explicit, stable error classes from tools/backends such as:

```text
INVALID_INPUT
UNAUTHORIZED
NOT_FOUND
RATE_LIMITED
TEMPORARILY_UNAVAILABLE
INTERNAL_ERROR
```

Only expose customer-safe distinctions. Internal root causes, stack traces, risk scores, and sensitive decision criteria should remain outside model context unless necessary and approved.

## Idempotency

Do not use a dynamic variable like `already_called=true` as the sole protection against duplicate financial/order/state-changing operations.

Use backend idempotency keys or durable journey state for operations where duplicates matter. CX state can reduce accidental repeated calls, but it is not the authoritative safety mechanism.

## Evaluation checklist

For callback/state logic, test:

- variable default and update behavior;
- invalid input blocked before external execution;
- valid input reaches backend once;
- callback failure path;
- response filtering;
- handoff condition after state update;
- repeated user input;
- async pending state interaction;
- new session does not incorrectly inherit state;
- backend still rejects invalid/unauthorized operations independently.
