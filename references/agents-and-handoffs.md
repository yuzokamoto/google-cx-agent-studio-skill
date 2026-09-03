# Agents, Routing, Handoffs, and Agent-as-a-Tool

Use this reference when deciding agent boundaries, root/sub-agent responsibilities, routing, deterministic transfers, or capability reuse.

## Agent application model

A CX Agent Studio application contains a root agent and can contain child/sub-agents. Each agent has its own instructions, model settings, description, tools/toolsets, and callbacks. The root agent is the initial conversational owner.

Agent descriptions matter because other agents can use them when deciding whether to transfer control. Write descriptions as routing contracts, not labels.

Good description:

```text
Handles order-status and shipment-tracking requests after an order identifier is available.
```

Weak description:

```text
Order agent.
```

## When to create a sub-agent

Create a sub-agent when at least one of these is true:

- the responsibility is a distinct business/domain capability;
- the agent needs a distinct tool surface or security boundary;
- the instructions are becoming large because unrelated behaviors are mixed;
- ownership of the conversation should clearly move to another specialist;
- the capability deserves independent evaluation and lifecycle management.

Do **not** create a sub-agent merely because:

- there is another API call;
- a form has another group of fields;
- the codebase has another backend service;
- you want a one-to-one mapping between flowchart boxes and agents.

Excessive decomposition increases routing ambiguity, context transfer risk, evaluation surface, and maintenance cost.

## Root-agent default

The root agent should generally:

- establish the application's broad purpose;
- understand high-level user intent;
- route/delegate to specialized capabilities;
- handle genuinely shared or unsupported requests;
- avoid accumulating every transactional tool in the application.

Do not force all business logic into the root agent simply to avoid handoffs.

## Instruction-based delegation versus Handoff Rules

### Instruction-based delegation

Use `{@AGENT: Agent Name}` in instructions when semantic interpretation is acceptable. This is model-mediated routing and is therefore probabilistic.

Appropriate examples:

- deciding whether a user is asking about returns or product recommendations;
- routing broad natural-language intents;
- selecting a specialist when small ambiguity is tolerable.

### Handoff Rules

Handoff Rules deterministically control transfers between parent and child agents. They can force transfer when a condition is satisfied or block transfer until a condition is satisfied.

Use them when transfer itself is a policy boundary, for example:

- only enter an account-management agent after authentication state is true;
- keep a sensitive-data agent inaccessible until prerequisites are satisfied;
- route users differently based on an explicit validated variable;
- guarantee a backward/forward transfer condition.

Do not create a Handoff Rule around an unreliable or never-populated variable. First establish how that variable is set and evaluate it.

Official reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/handoff

## Agent-as-a-Tool versus handoff

Agent-as-a-tool lets one agent reuse another agent's capability without transferring conversational ownership. It can execute synchronously or asynchronously. As of the 2026-09-03 audit, this feature is documented as Preview.

Choose based on ownership:

| Need | Prefer |
|---|---|
| Specialist should take over the conversation | Sub-agent handoff |
| Current agent should stay in control and consume specialist output | Agent-as-a-tool |
| Deterministic transfer condition | Handoff Rule |
| Background specialist work with the active agent continuing the conversation | Async agent-as-a-tool |

Do not use agent-as-a-tool just to hide poor tool design. If the reused capability is deterministic API logic, a regular tool may be simpler and cheaper.

Official reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/tool/agent-as-tool

## Routing checklist

Before adding an agent, answer:

1. What responsibility does this agent own?
2. What triggers entry?
3. Does entry need to be deterministic?
4. What tools does it uniquely need?
5. What state must already exist?
6. What state can it change?
7. When does it return control?
8. What happens on failure or unsupported requests?
9. How will this routing be evaluated?

If these cannot be answered, the agent boundary may be premature.

## Tool ownership

Expose only relevant tools to each agent. More tools increase model choice complexity and context size.

Prefer:

```text
root_agent
├── order_agent → order tools
├── returns_agent → return tools
└── product_agent → catalog/knowledge tools
```

over:

```text
root_agent → every tool
all sub-agents → every tool
```

## Shared utility agents

A shared escalation or satisfaction capability may be valid, but avoid creating circular or confusing transitions. When editing exported configuration, preserve the documented parent/child constraints in the export format and inspect the resulting hierarchy after import.

Export reference:
https://docs.cloud.google.com/gemini-enterprise-cx/cx-agent-studio/reference/export

## Flow-based agents

Existing Dialogflow CX flows can be imported as flow-based agents. Treat this as a migration/integration boundary rather than a normal generative sub-agent design. See `flows-and-migration.md`.

## Evaluation expectations

Every routing boundary should have tests for:

- expected transfer;
- forbidden transfer;
- ambiguous user phrasing;
- missing prerequisite state;
- return/backward handoff where applicable;
- prompt injection attempting to bypass routing prerequisites.
