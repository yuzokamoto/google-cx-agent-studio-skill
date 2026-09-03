# API and Automation

Use this reference for REST/RPC automation, CI/CD integration, the official CX Agent Studio MCP server, direct mutation, and export/edit/import workflows.

## Prefer documented interfaces

For automation, use the current CX Agent Studio REST/RPC APIs or the official CX Agent Studio MCP server rather than scraping the console.

Base service/API versions and resource availability evolve. Check current `v1` and `v1beta` references before implementing a client.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rpc/google.cloud.ces.v1

## Authentication

Use Google Cloud Application Default Credentials/service identities/OAuth as documented for the operation and environment. Apply least privilege and do not embed credentials into exported application files or agent instructions.

Before automating writes, verify:

- project/location/app identifiers;
- caller identity;
- IAM permission for the exact method;
- target API version;
- current ETag/concurrency semantics where exposed.

## Mutation authorization policy

CX Agent Studio's APIs and official MCP server can change application resources. Access to a write-capable interface is not, by itself, intent to modify resources.

Use the following skill-level safety boundary:

### Read-only intents

Treat these tasks as read-only unless the user explicitly asks for a change:

- review or audit;
- architecture analysis;
- troubleshooting or diagnosis;
- comparison;
- explanation/documentation lookup;
- inspection of an exported app, trace, evaluation, or current configuration.

Do not "fix while reviewing" merely because a correction appears obvious.

### Write intents

A write is appropriate when the user explicitly asks to create, update, delete, import, restore, configure, or otherwise implement a change.

For authorized writes:

1. read the current target first;
2. identify the smallest intended diff;
3. preserve unrelated fields/resources;
4. verify environment and target identifiers;
5. use supported concurrency controls when available;
6. validate the resulting behavior;
7. report what changed.

Do not add extra confirmation when the write intent and non-production target are already explicit and unambiguous.

### Production and deployment boundary

Treat configuration mutation and deployment as separate permissions in the user's request.

- Editing an application does not imply permission to deploy it.
- Creating a version does not imply permission to change production traffic.
- A request to deploy to production should be explicit or otherwise unambiguously part of the requested operation.
- Before a production mutation/deployment, identify the affected version/state and a recovery/rollback boundary when the platform workflow supports one.
- Do not silently promote a draft or newly changed resource because tests pass.

This policy is an engineering safeguard for agents using the APIs/MCP server; it is not a claim that CX Agent Studio itself imposes these intent checks.

## Direct mutation versus export/edit/import

Current Google guidance for the official MCP server distinguishes two useful patterns.

### Direct mutation

Best for small, targeted changes:

- update one instruction;
- create/update one tool;
- run an evaluation;
- inspect/list resources.

Advantages:

- faster feedback;
- fewer files touched;
- suitable for interactive agent-assisted development.

Risks:

- multiple related mutations can leave an intermediate inconsistent state;
- review is harder if changes are not also captured in source control.

### Export → edit → import

Best for broad architectural refactors:

- renaming/restructuring many agents;
- changing references across many files;
- environment migration;
- large tool/variable changes;
- pull-request review of the whole change set.

Advantages:

- coherent diff;
- easier bulk validation;
- better source-control review.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/mcp-server

## Official CX Agent Studio MCP server

The product provides an MCP server that exposes administration capabilities over the same platform API used to manage CX Agent Studio resources.

Use it when an AI coding environment should make controlled CX Agent Studio changes programmatically.

Typical capability categories documented include actions analogous to:

- listing/managing agents;
- creating/updating tools;
- updating instructions;
- running evaluations;
- exporting/importing applications.

Do not hard-code a tool list from this skill. Discover the current MCP server capabilities because they can evolve.

## Automation safety

For any authorized write automation:

1. read the current resource first;
2. understand the intended minimal diff;
3. preserve unrelated configuration;
4. use ETags/concurrency control when supported;
5. prefer a non-production environment first for broad or risky changes unless the user explicitly targets production;
6. run relevant evaluations;
7. create a version or recovery boundary when appropriate;
8. deploy only when deployment is part of the authorized task and the reviewed version is identified.

Never mass-update generated configuration from guessed object names.

## Export format automation

Current export archives use display names to reference other application objects. The current documented format includes `app.yaml`, agent directories, instruction files, tool/toolset definitions, callbacks, and `environment.json`.

When writing scripts:

- parse YAML/JSON structurally instead of regex-replacing configuration;
- preserve unknown fields unless the API/import format rejects them;
- validate cross-references after renames;
- keep environment dependencies externalized;
- do not commit secrets;
- check reserved tool names in the current export-format documentation.

Reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/export

## CI/CD pattern

A practical pipeline can be:

```text
Pull request
  -> validate export structure
  -> check naming/references
  -> static policy checks
  -> import into isolated test app/environment
  -> run Golden/Scenario evaluations
  -> integration smoke tests
  -> approval
  -> create immutable version
  -> deploy / canary traffic split
```

Do not claim CX Agent Studio itself provides every CI orchestration step. GitHub Actions/Cloud Build/other CI systems can call the platform APIs as appropriate.

## API-contract review

When generating code for the REST API:

- fetch the exact current method schema;
- use the documented resource name format;
- honor long-running operations where returned;
- do not mix `v1` and `v1beta` request shapes;
- do not infer a field from similarly named ADK/Dialogflow resources;
- check IAM permissions documented on the method page.

## Tool execution API

The API supports programmatic tool execution. Current schemas distinguish persisted tools from tools inside toolsets. Use the exact current `ToolCall`/`ToolResponse`/`executeTool` schema rather than assuming a single identifier shape.

References:
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest/v1/projects.locations.apps/executeTool
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest/v1/ToolCall
- https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/rest/v1/ToolResponse

## Review output for automated changes

When an automation or coding agent changes CX Agent Studio configuration, report:

```text
Scope changed:
Files/resources changed:
Behavioral reason:
Environment dependencies changed:
Evaluations run:
Integration checks:
Version created:
Deployment impact:
Rollback target:
```

This keeps platform mutation auditable and avoids treating an AI-generated change as self-validating.
