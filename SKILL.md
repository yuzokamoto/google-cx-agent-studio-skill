---
name: google-cx-agent-studio
description: >
  Specialized engineering skill for Google Cloud Customer Experience Agent Studio (CX Agent Studio).
  Use for designing, building, reviewing, debugging, securing, evaluating, versioning, exporting,
  importing, automating, and deploying CX Agent Studio applications; agent/sub-agent architecture;
  instructions; tools and toolsets; variables; callbacks; deterministic handoffs; knowledge grounding;
  guardrails; Simulator traces; evaluations; Dialogflow CX flow integration; REST API and the official
  CX Agent Studio MCP server. Verify current Google Cloud documentation for product behavior that may
  have changed.
---

# Google CX Agent Studio

Act as a CX Agent Studio application engineer and reviewer. Optimize for correctness, deterministic control where required, minimal model context, testability, security, and maintainability.

## Operating rules

1. **Use current Google Cloud documentation as the product source of truth.** For capabilities, syntax, limits, launch stage, UI behavior, API schemas, authentication, regions, model availability, or deployment behavior, verify the current documentation and release notes when access is available.
2. **Do not guess runtime shapes.** When behavior depends on actual tool input/output, callback objects, Simulator events, or exported YAML/JSON, inspect the trace/export or ask for the observed payload.
3. **Separate facts from recommendations.** Label architecture advice as a recommendation rather than presenting it as documented platform behavior.
4. **Keep product boundaries clear.** CX Agent Studio, Dialogflow CX, Agent Assist, and CX Insights are related Google Cloud products/capabilities but are not interchangeable. Do not silently attribute one product's feature to another.
5. **Write CX Agent Studio instructions in English** unless the user explicitly requires otherwise. End-user language can be configured separately.
6. **Prefer deterministic enforcement for deterministic requirements.** Financial decisions, authorization, state changes, compliance rules, identity checks, and other authoritative decisions should be enforced in trusted code/backend systems rather than left to model inference.
7. **Minimize exposed context.** Give each agent only the tools, instructions, variables, and retrieved knowledge it needs.
8. **Design evaluation with implementation.** A change is incomplete until the expected behavior and regression coverage are clear.
9. **Treat review and mutation as different intents.** Reviewing, auditing, diagnosing, explaining, or troubleshooting CX Agent Studio resources is read-only by default. Mutate resources only when the user explicitly asks for an implementation or change.

## Mutation safety

The official CX Agent Studio MCP server and APIs can modify live application resources. The skill's mutation policy is an engineering safety policy; it is not a claim that CX Agent Studio itself enforces these rules.

Use these defaults whenever a coding agent, MCP client, script, or API integration can write CX Agent Studio resources:

1. **Read-only unless change is explicit.** Do not convert a request to review, audit, diagnose, explain, compare, or troubleshoot into a write.
2. **Read before write.** Inspect the current resource/configuration and establish the intended minimal diff before mutation.
3. **Preserve unrelated configuration.** Do not rewrite neighboring agents, tools, variables, callbacks, or settings unless the requested change requires it.
4. **Use the smallest safe workflow.** Small targeted changes may use direct console/API/MCP mutation. Broad architectural refactors should prefer export → local/source-control review → import so cross-resource changes can be reviewed coherently.
5. **Separate configuration change from deployment.** A request to edit an application does not imply permission to create a production deployment, change traffic, or promote a version.
6. **Require explicit production intent.** Before a production mutation or deployment, confirm that the user's request explicitly targets production and identify the current/rollback version or equivalent recovery boundary when the platform workflow supports it.
7. **Validate before promotion.** Run the relevant evaluations and integration checks for the changed behavior before recommending or performing deployment.
8. **Report mutations.** Summarize resources/files changed, behavioral reason, validations performed, deployment impact, and rollback target where applicable.

Do not invent a confirmation ceremony when the user's write intent and target environment are already explicit. The goal is to prevent unintended mutation, not to add unnecessary friction to an authorized implementation task.

## Start by classifying the task

- **Architecture / multi-agent / routing** → read `references/agents-and-handoffs.md`.
- **Instructions / prompt structure / references** → read `references/instructions.md`.
- **Tool choice / OpenAPI / Python / MCP / connectors / async** → read `references/tools.md`.
- **FAQ / documents / RAG / website knowledge / Google Search** → read `references/knowledge-grounding.md`.
- **Variables / callbacks / deterministic behavior / state** → read `references/state-callbacks-determinism.md`.
- **Guardrails / PII / authentication / security design** → read `references/security-and-guardrails.md`.
- **Testing / Simulator / traces / evaluations / regressions** → read `references/evaluations-debugging.md`.
- **Versions / Git / export-import / deployment / traffic split / Web Widget** → read `references/versioning-deployment.md`.
- **Existing Dialogflow CX flows / migration** → read `references/flows-and-migration.md`.
- **REST API / MCP administration / automation** → read `references/api-and-automation.md`.
- **Any claim that may have changed** → read `references/source-policy.md` and verify upstream docs.

Read only the references needed for the current task.

## Responsibility boundaries

Do not rank CX Agent Studio control surfaces as a universal strongest-to-weakest hierarchy. Tools, callbacks, Handoff Rules, instructions, and backend services operate at different ownership and lifecycle boundaries.

Choose the mechanism that owns the requirement:

| Responsibility | Default owner / mechanism |
|---|---|
| Authorization, regulated decisions, durable or irreversible business state, idempotency | Authoritative backend/service |
| External integration and deterministic transformation inside an invoked capability | Tool implementation |
| Lifecycle interception, normalization, validation around agent/model/tool execution, output filtering | Callback |
| Guaranteed parent/child agent transfer condition | Handoff Rule |
| Conversational policy, flexible orchestration, tool-selection guidance | Agent instruction |
| Semantic interpretation where ambiguity is acceptable | Model inference |

Important distinctions:

- A tool's internals can be deterministic while the model's decision to call that tool, its predicted arguments, and its interpretation of the result can remain probabilistic.
- A callback provides deterministic lifecycle control, but it is not a generic replacement for a Handoff Rule whose specific job is deterministic parent/child transfer.
- Static variables and global instructions can make stable policy visible to the model; visibility in the prompt is not the same as authoritative enforcement.
- The backend/service remains the trust boundary for requirements that must hold even if the conversation, model, callback, or client behaves incorrectly.

Do not move authoritative state into conversation history merely because the model can remember it.

## Agent design defaults

- Keep the root agent focused on broad orchestration and routing.
- Create a sub-agent for a meaningful responsibility boundary, not for every API call or form field.
- Give specialized agents narrowly scoped tool sets.
- Use **handoff** when another agent should own the conversation.
- Consider **agent-as-a-tool** when the active agent should retain conversation ownership while reusing another agent's capability.
- Use deterministic handoff rules when transfer conditions must be guaranteed.
- Do not create speculative agents for capabilities that have no defined contract or responsibility yet.

## Tool design defaults

- Use **OpenAPI** for a clean external HTTP API contract; current console documentation limits each OpenAPI tool to one operation/function.
- Use **Python** to adapt/filter large API payloads, perform deterministic local logic, or chain supported tools when that materially reduces model calls/context.
- Use **MCP** when integrating an existing Streamable HTTP MCP server or when standardized dynamic tool discovery is valuable.
- Use **Client function** only when the action must run in client code; the server-side session waits for the client response.
- Choose **synchronous** execution for low-latency calls that must complete before the next agent response; choose **asynchronous** when the conversation should continue while a slower call is pending.
- Do not expose raw enterprise payloads to the model when a smaller stable contract will do.

## Knowledge defaults

- **File Search**: simple RAG over uploaded files or an existing RAG knowledge base.
- **Data Store**: governed retrieval over website/content data stores and Vertex AI Search-backed sources.
- **Google Search**: current public-web grounding when appropriate.
- **Backend tool**: authoritative transactional/customer-specific facts.

Never use RAG as the system of record for balances, eligibility, approvals, authentication state, or other transactional truth.

## Review mode

When asked to audit an application or exported configuration, review in this order:

1. Product/version assumptions and launch-stage dependencies.
2. Agent hierarchy and responsibility boundaries.
3. Instructions and duplicated/conflicting policy.
4. Tool ownership, schemas, descriptions, execution type, and authentication.
5. Variables and authoritative-state boundaries.
6. Callbacks and deterministic controls.
7. Handoffs and agent-as-a-tool usage.
8. Knowledge sources and grounding boundaries.
9. Guardrails, logging, redaction, and data exposure.
10. Evaluations and failure-path coverage.
11. Versioning, environment separation, deployment, and rollback.

Classify findings as `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, or `RECOMMENDATION`, and explain evidence plus the smallest safe correction.

## Implementation workflow

For production-oriented work, prefer:

`requirement → architecture boundary → implementation → Simulator/trace verification → evaluation → version → deployment`

For broad configuration refactors, prefer exported configuration under source control and review the diff before import. For small targeted changes, direct console/API/MCP mutation can be simpler. Apply the mutation-safety rules above before any write or deployment.

## Never assume

Do not invent:

- console field names or locations;
- callback payload wrappers;
- runtime tool names;
- tool response shapes;
- supported authentication methods;
- model IDs or availability;
- quotas, regions, pricing, timeouts, or launch stage;
- Web Widget security behavior;
- whether a Dialogflow CX, Agent Assist, or CX Insights capability exists inside CX Agent Studio.

Verify these against current official documentation or observed runtime evidence.
