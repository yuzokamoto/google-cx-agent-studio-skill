# Python Runtime for Tools and Callbacks

Use this reference whenever writing or debugging executable Python for a CX Agent Studio Python tool or callback.

This file describes the **CX Agent Studio Python runtime**. Do not assume that a generic Google ADK example, normal CPython environment, or third-party `requests` example is valid in this sandbox without checking the current CX Agent Studio runtime documentation.

## Source of truth

Before generating production-ready Python, verify the current versions of these pages:

- Python runtime reference: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/python
- Python code tools: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/python
- Callbacks: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/callback
- Outbound networking: https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/network/outbound

Runtime APIs, available packages, helper behavior, and networking support are time-sensitive.

## Current runtime environment

**Documented at the 2026-09-03 audit:** Python tools and callbacks run in a secure **Python 3.12** sandbox.

The current runtime reference limits imports to:

- Python 3.12 standard-library modules;
- Pydantic 2.11.6;
- NumPy 2.3.1;
- protobuf 5.29.1.

Treat package versions as a snapshot, not a permanent compatibility guarantee. Do not generate code that depends on arbitrary `pip` packages unless current CX Agent Studio documentation explicitly supports them.

## CX Agent Studio globals and helpers

The runtime exposes platform-specific globals. Prefer these documented interfaces instead of assuming a conventional application runtime.

### `context`

`context` is globally available. Do not add it as a tool function argument and do not import it from generic ADK packages.

For Python tools, it is a `ToolContext`. `ToolContext` derives from `CallbackContext` and adds the current `function_call_id`.

Useful current context data includes:

- `user_content` — most recent user content;
- `invocation_id` — current invocation/turn identifier;
- `agent_name` — current agent display name;
- `session_id` — current session identifier;
- `variables` — current session variables;
- `state` — alias of `variables` for ADK compatibility;
- `events` — session events;
- `function_call_id` — current tool-call identifier on `ToolContext`.

Current documentation states that `context.state` and `context.variables` are interchangeable, but **new code should prefer `context.variables`**. `state` exists for ADK compatibility.

### Variable helpers

The runtime also currently exposes:

```python
get_variable(key)
set_variable(key, value)
remove_variable(key)
```

These are shortcuts around the same session-variable state.

For code that needs explicit defaults, direct dictionary access is often clearer:

```python
customer_id = context.variables.get("customer_id")
```

Do not treat session variables as authoritative durable business state. See `state-callbacks-determinism.md`.

### `ces_requests`

`ces_requests` is a globally available `Requests` instance with a requests-like API. Current documented methods include:

```text
get
post
put
delete
patch
head
options
```

Example pattern:

```python
def get_status(item_id: str) -> dict:
    """Gets the current public-service status for an item."""
    response = ces_requests.get(
        url=f"https://api.example.com/items/{item_id}"
    )
    response.raise_for_status()
    return response.json()
```

Do not `pip install requests` or assume the full third-party `requests` API. Use only behavior documented for `ces_requests`/`Requests`.

### `tools`

`tools` is the globally available synchronous tool-call helper.

Current runtime pattern:

```python
response = tools.<TOOL_DISPLAY_NAME>({"argument": "value"})
response.raise_for_status()
data = response.json()
```

The Python-tool documentation currently shows an OpenAPI example whose callable name is derived from the OpenAPI tool/endpoint name. Do not guess that generated callable name. Inspect the actual application/tool definition or runtime evidence when it matters.

Use a Python tool to chain other tools only when the deterministic sequence belongs inside that capability and doing so improves reliability/context efficiency. Tool chaining does not move authorization or durable state ownership out of the authoritative backend.

### `async_tools`

`async_tools` is the globally available asynchronous tool-call helper.

Current runtime pattern:

```python
response_future = async_tools.<TOOL_DISPLAY_NAME>({"argument": "value"})

# Do other local work if useful.
response = response_future()
response.raise_for_status()
data = response.json()
```

Do not confuse `async_tools` inside Python with an agent-level asynchronous tool execution policy. They are related to asynchronous execution but operate at different orchestration layers.

## Response and status handling

The runtime currently exposes `StatusError` for errors carrying an HTTP-style status code/reason, and tool/HTTP responses support patterns such as:

```python
try:
    response.raise_for_status()
except StatusError as exc:
    return {
        "status": "UPSTREAM_ERROR",
        "status_code": exc.status_code,
    }
```

Do **not** infer retryability solely from an HTTP status code in generic skill-generated code. Whether a failure is retryable depends on the upstream contract, operation idempotency, rate-limit semantics, and the owning system's retry policy. Map only the error distinctions the capability is authorized to own, and avoid exposing internal diagnostics to the model/user unnecessarily.

Avoid broad `except:` blocks in production examples unless the goal is deliberately to collapse every runtime exception to one safe outcome. Preserve distinctions needed for observability while returning only customer/model-safe data.

See `error-handling.md` for system fallback versus tool/integration/business-negative outcomes.

## Python tool contract

For a Python code tool, current documentation requires:

- the CX Agent Studio tool name and main Python function name to match exactly in `snake_case`;
- the function docstring to act as the tool description presented to the model.

Therefore the docstring is part of the orchestration contract, not just developer documentation.

Good minimal shape:

```python
def normalize_reference(reference: str) -> dict:
    """
    Normalizes a customer-provided public reference identifier.
    Use only before a lookup that requires the normalized identifier.
    This function does not authenticate the user or perform the lookup.
    """
    normalized = reference.strip().upper()
    return {"normalized_reference": normalized}
```

Keep tool parameters and returned data small, explicit, and model-relevant.

## Networking boundary

This is a hard architecture constraint.

**Current documented behavior:**

- Python code tools can access public-internet endpoints;
- Python callbacks can access public-internet endpoints;
- Python code tools **do not support CX Agent Studio Private network access**;
- Python callbacks **do not support CX Agent Studio Private network access**;
- they cannot directly use the Service Directory private path to access private IP/private DNS targets.

If the dependency is private-only, do not solve the problem by adding more Python. Use a currently supported private-network-capable tool type such as OpenAPI or MCP, or move the transformation behind a reachable service boundary.

See `tools.md` and `security-and-guardrails.md` for the current networking matrix and VPC/Service Directory constraints.

## Callback signatures

Callback function names and signatures are runtime contracts. Use the current CX Agent Studio callback documentation rather than a remembered ADK signature.

### `before_agent_callback`

```python
def before_agent_callback(
    callback_context: CallbackContext,
) -> Optional[Content]:
    ...
```

If a `Content` value is returned, the agent invocation is skipped and that content is used.

### `after_agent_callback`

```python
def after_agent_callback(
    callback_context: CallbackContext,
) -> Optional[Content]:
    ...
```

If a `Content` value is returned, it replaces the agent output.

### `before_model_callback`

```python
def before_model_callback(
    callback_context: CallbackContext,
    llm_request: LlmRequest,
) -> Optional[LlmResponse]:
    ...
```

If an `LlmResponse` is returned, the model call is skipped and the returned response is used.

### `after_model_callback`

```python
def after_model_callback(
    callback_context: CallbackContext,
    llm_response: LlmResponse,
) -> Optional[LlmResponse]:
    ...
```

If an `LlmResponse` is returned, it replaces the model response.

### `before_tool_callback`

```python
def before_tool_callback(
    tool: Tool,
    input: dict[str, Any],
    callback_context: CallbackContext,
) -> Optional[dict[str, Any]]:
    ...
```

If a dictionary is returned, the actual tool execution is skipped and that dictionary is supplied as the tool result.

### `after_tool_callback`

```python
def after_tool_callback(
    tool: Tool,
    input: dict[str, Any],
    callback_context: CallbackContext,
    tool_response: dict,
) -> Optional[dict]:
    ...
```

If a dictionary is returned, it replaces the tool response supplied back to the model.

Multiple callbacks of the same type can exist. Current platform resource documentation states they execute sequentially in configured order and later callbacks can be skipped when an earlier callback produces an overriding response. Verify the exact current behavior before depending on callback ordering for a critical invariant.

## `CallbackContext`

Current runtime documentation exposes these useful attributes:

```text
user_content
invocation_id
agent_name
session_id
variables
state
events
```

and methods such as:

```text
get_variable(key, default)
set_variable(key, value)
remove_variable(key)
get_last_user_input()
get_last_agent_output()
```

Prefer `callback_context.variables` for new CX Agent Studio callback code. Do not assume every ADK context method exists in CX Agent Studio unless it is present in the current runtime reference.

## CX Agent Studio runtime versus ADK

CX Agent Studio is built with concepts related to ADK, and its documentation links to corresponding ADK callbacks/context concepts. That does **not** make the environments interchangeable.

When writing executable CX Agent Studio code:

1. use the CX Agent Studio Python runtime reference first;
2. use ADK documentation only as supplemental conceptual/background material;
3. do not import ADK runtime objects merely because an ADK example does so;
4. do not assume an ADK package/version/helper is available inside the CX sandbox;
5. prefer CX-provided globals/classes and current callback signatures.

## Do not guess runtime wrapper shapes

The callback signature can be documented while the application-specific content of a tool input/response still varies by tool type and execution path.

Do **not** write production logic that assumes paths such as:

```python
input["requestBody"]
tool_response["body"]
tool.name == "invented_runtime_name"
```

unless those paths/names are established by the current schema or observed runtime evidence.

For runtime-shape-dependent logic:

1. test the tool directly;
2. reproduce the call through Preview/Simulator;
3. inspect Steps/trace;
4. capture the exact tool name, input shape, response shape, and variable updates;
5. implement the smallest callback/tool logic against that evidence;
6. add an evaluation that protects the observed contract.

## Implementation checklist

Before returning executable Python for CX Agent Studio, verify:

- [ ] Current CX Python runtime docs were consulted for time-sensitive API/package behavior.
- [ ] Tool/function names match exactly where required.
- [ ] Docstring describes tool semantics and boundaries clearly.
- [ ] Only currently supported imports/packages are used.
- [ ] `context.variables` is preferred for new state access.
- [ ] Session variables are not used as authoritative durable state.
- [ ] `ces_requests`, `tools`, and `async_tools` syntax matches current runtime documentation.
- [ ] Private-network dependencies are not accessed from Python tool/callback runtime.
- [ ] Callback function name/signature/return semantics match the current callback docs.
- [ ] No application-specific tool wrapper shape is guessed.
- [ ] Errors are normalized without hiding observability needed by the owning system.
- [ ] Relevant Simulator/trace verification and evaluations are defined.
