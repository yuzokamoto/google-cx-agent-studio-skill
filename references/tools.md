# Tools and Tool Selection

Use this reference when selecting, designing, integrating, or debugging CX Agent Studio tools.

## Current tool families

As of the 2026-09-03 audit, the current Google documentation lists these tool families:

- Agent as a tool
- Client function tools
- Confluence tools
- Data store tools
- File search tools
- Google Maps tools (Preview at audit time)
- Google Search tools
- Integration Connector tools
- Jira tools
- MCP tools
- OpenAPI tools
- Python code tools
- Salesforce tools
- Service Now tools
- SharePoint tools
- System tools
- Widget tools

Always re-check the current Tools page before treating this list or a launch stage as permanent:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool

## Selection guide

| Need | Default choice |
|---|---|
| Call a clean external HTTP API with an explicit contract | OpenAPI |
| Reduce/transform a large API response or implement deterministic local glue | Python |
| Use an existing standardized MCP server | MCP |
| Run functionality in the end-user/client application | Client function |
| Search governed enterprise/web/document data stores | Data Store |
| Simple RAG over uploaded files / existing RAG knowledge base | File Search |
| Ground with current public Google Search results | Google Search |
| Use a supported enterprise SaaS integration | Native connector/tool |
| Reuse another agent's reasoning/capability without handing off | Agent-as-a-tool |
| End session or invoke built-in session behavior | System tool |
| Produce supported rich interaction behavior | Widget tool |

Do not choose a tool type solely because it is newer. Prefer the smallest interface that matches the ownership and security boundary.

## Synchronous versus asynchronous execution

Current CX Agent Studio tools support two execution types:

### Synchronous

The session waits for the tool response before the agent continues. Google's guidance is to use this for low-latency calls, ideally below about 5 seconds.

### Asynchronous

The agent can continue while the tool is executing. The tool initially produces a pending state; its completed response is added to context later. Google's guidance is to use this for roughly 5-60 second latency cases.

The REST/RPC schema currently documents default timeouts of 30 seconds for synchronous and 60 seconds for asynchronous tools/toolsets when not explicitly set. Verify this before relying on it.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest/v1/projects.locations.apps.tools

### Async design rules

When using an asynchronous tool:

- define what the agent says while work is pending;
- explicitly prevent duplicate calls while the same work is pending when duplication matters;
- do not invent a custom `PENDING` backend response merely to simulate platform pending behavior unless the backend protocol independently requires it;
- define what happens if the user changes topic while the result is pending;
- decide whether late results should still be surfaced;
- evaluate pending, success, no-result, timeout/failure, and duplicate-request cases.

For jobs that truly take minutes/hours/days, model them as durable backend jobs with an explicit status/retrieval contract rather than holding one CX tool request open indefinitely.

## OpenAPI tools

Use OpenAPI for a stable external HTTP contract.

Current console documentation states that **each OpenAPI tool can contain only one operation/function**. Do not silently assume a multi-operation specification will behave as a single console tool.

The API also exposes **OpenAPI toolsets**, which represent groups of tools defined from an OpenAPI schema. Treat `OpenApiTool` and `OpenApiToolset` as distinct resource concepts and check the current API documentation for the workflow you are using.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/open-api

### OpenAPI design rules

- Keep request/response schemas small and explicit.
- Prefer flat parameters where practical; deep nested structures are harder for models to predict reliably.
- Give operations clear `operationId`, descriptions, enums, and required fields.
- Return only fields needed by the agent.
- Use backend HTTP status codes consistently.
- Do not return internal scores, debug fields, or sensitive metadata unless the agent genuinely needs them.
- Revalidate security/business inputs in the backend even if a callback validates them first.

### Session context injection

Built-in session context can be injected without asking the model to predict it. Current documentation exposes values such as:

```text
$context.project_id
$context.project_number
$context.location
$context.app_id
$context.session_id
$context.turn_index
$context.variables
$context.variables.<name>
```

For OpenAPI parameters, use `x-ces-session-context` where supported.

Example:

```yaml
parameters:
  - name: X-Session-Id
    in: header
    required: true
    schema:
      type: string
    x-ces-session-context: $context.session_id
```

Do not expose values to model prediction when the platform can inject them deterministically.

## Python tools

Python tools are useful for deterministic logic and context engineering.

Good uses:

- normalize or validate inputs before an external operation;
- call supported external services using the platform runtime;
- wrap a noisy OpenAPI/backend response and return a minimal structure;
- chain a deterministic sequence of tool calls when doing so reduces model round-trips;
- update dynamic session variables where appropriate.

Do not move durable business state or authorization logic into a Python tool merely because it is convenient. The Python runtime is an execution helper, not a substitute for an authoritative backend.

### Context engineering

Google's best-practices documentation recommends wrapping APIs when raw schemas/results contain large amounts of irrelevant information. Extra fields consume tokens, increase reasoning time, and can confuse tool-result interpretation.

Prefer:

```json
{
  "status": "CONFIRMED",
  "appointment_time": "...",
  "confirmation_id": "..."
}
```

over dumping the full upstream response.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/best-practices

## MCP tools

CX Agent Studio MCP tools connect to existing MCP servers.

Current documented constraints and behavior include:

- Streamable HTTP transport is supported; SSE transport is not supported;
- MCP tools use the same authentication options as OpenAPI tools;
- custom HTTP headers can be supplied from session variables;
- test the MCP server independently before adding it to an agent;
- for Cloud Run-hosted MCP servers, Google recommends Service Agent ID Token and the appropriate Cloud Run invoker permission for the CX Agent Studio service agent.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/mcp

### MCP decision rule

Use MCP because it is the right integration contract, not merely because it is flexible. A narrowly scoped OpenAPI tool can be easier to govern than exposing a large dynamic MCP tool catalog.

## Client function tools

Client function tools execute in client code. The server-side conversation waits until the client sends the matching response.

Use when the capability is inherently client-side, such as:

- interacting with the page/application UI;
- reading client-local information that should not be hosted in an agent-side tool;
- invoking an existing local client capability.

Do not use client functions as a shortcut around backend security boundaries.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/function

## Agent-as-a-tool

Use when an active agent should retain control of the conversation while consuming another agent's capability. This is different from a sub-agent handoff.

As of this audit, agent-as-a-tool is Preview. Re-check launch status before production commitments.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/agent-as-tool

## Tool descriptions

Tool descriptions influence model selection. They should state:

- the task the tool performs;
- when to use it;
- meaningful prerequisites;
- what the result represents;
- what it does **not** do when confusion is likely.

Avoid overlapping descriptions such as `search_customer`, `find_customer`, and `lookup_customer` unless they have materially distinct semantics.

## Tool ownership

Remove unused tools from agents. Do not expose every application tool to every agent.

Review:

- Is this tool attached to the correct agent?
- Is its description distinct from neighboring tools?
- Can the model predict all arguments reliably?
- Can context injection supply any arguments deterministically?
- Is the output minimal?
- Should execution be sync or async?
- Are retries/idempotency handled by the authoritative system?
- Is authentication least-privilege?
- Are tool failures covered by evaluations?

## Testing workflow

1. Test the external API/server independently.
2. Test the tool directly with **Test Tool**.
3. Test through **Preview agent**.
4. Inspect Steps/trace for the exact model call, arguments, result, and callbacks.
5. Only then write runtime-shape-dependent callback logic.
6. Add Golden/Scenario evaluation coverage.
